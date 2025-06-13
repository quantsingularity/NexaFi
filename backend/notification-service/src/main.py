"""
Notification Service for NexaFi
Handles email, SMS, and in-app notifications with compliance requirements
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import queue
import time

# Add shared modules to path
sys.path.append('/home/ubuntu/nexafi_backend_refactored/shared')

from middleware.auth import require_auth, require_permission
from validators.schemas import validate_json_request, SanitizationMixin, Schema, fields, validate
from logging.logger import setup_request_logging, get_logger
from audit.audit_logger import audit_logger, AuditEventType, AuditSeverity, audit_action
from database.manager import initialize_database, BaseModel

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexafi-notification-service-secret-key-2024')

# Enable CORS
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization", "X-User-ID"])

# Setup logging
setup_request_logging(app)
logger = get_logger('notification_service')

# Initialize database
db_path = '/home/ubuntu/nexafi_backend_refactored/notification-service/data/notifications.db'
db_manager, migration_manager = initialize_database(db_path)

# Apply notification-specific migrations
NOTIFICATION_MIGRATIONS = {
    "008_create_notifications_table": {
        "description": "Create notifications table",
        "sql": """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            channel TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'normal',
            subject TEXT,
            message TEXT NOT NULL,
            template_name TEXT,
            template_data TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            scheduled_at TIMESTAMP,
            sent_at TIMESTAMP,
            delivery_attempts INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
        CREATE INDEX IF NOT EXISTS idx_notifications_scheduled_at ON notifications(scheduled_at);
        """
    },
    
    "009_create_notification_preferences_table": {
        "description": "Create notification preferences table",
        "sql": """
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            email_enabled BOOLEAN DEFAULT 1,
            sms_enabled BOOLEAN DEFAULT 1,
            push_enabled BOOLEAN DEFAULT 1,
            marketing_enabled BOOLEAN DEFAULT 0,
            security_alerts BOOLEAN DEFAULT 1,
            transaction_alerts BOOLEAN DEFAULT 1,
            compliance_alerts BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences(user_id);
        """
    },
    
    "010_create_notification_templates_table": {
        "description": "Create notification templates table",
        "sql": """
        CREATE TABLE IF NOT EXISTS notification_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT NOT NULL UNIQUE,
            template_type TEXT NOT NULL,
            channel TEXT NOT NULL,
            subject_template TEXT,
            body_template TEXT NOT NULL,
            variables TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_notification_templates_name ON notification_templates(template_name);
        CREATE INDEX IF NOT EXISTS idx_notification_templates_type ON notification_templates(template_type);
        """
    }
}

# Apply migrations
for version, migration in NOTIFICATION_MIGRATIONS.items():
    migration_manager.apply_migration(version, migration["description"], migration["sql"])

# Set database manager for models
BaseModel.set_db_manager(db_manager)

class Notification(BaseModel):
    table_name = 'notifications'

class NotificationPreferences(BaseModel):
    table_name = 'notification_preferences'

class NotificationTemplate(BaseModel):
    table_name = 'notification_templates'

# Validation schemas
class NotificationSchema(SanitizationMixin, Schema):
    user_id = fields.Str(required=True)
    notification_type = fields.Str(required=True, validate=validate.OneOf([
        'security_alert', 'transaction_alert', 'compliance_alert', 'marketing',
        'system_maintenance', 'account_update', 'kyc_update', 'payment_confirmation'
    ]))
    channel = fields.Str(required=True, validate=validate.OneOf(['email', 'sms', 'push', 'in_app']))
    priority = fields.Str(required=False, validate=validate.OneOf(['low', 'normal', 'high', 'urgent']))
    subject = fields.Str(required=False, validate=validate.Length(max=200))
    message = fields.Str(required=True, validate=validate.Length(min=1, max=5000))
    template_name = fields.Str(required=False)
    template_data = fields.Dict(required=False)
    scheduled_at = fields.DateTime(required=False)

class NotificationPreferencesSchema(SanitizationMixin, Schema):
    email_enabled = fields.Bool(required=False)
    sms_enabled = fields.Bool(required=False)
    push_enabled = fields.Bool(required=False)
    marketing_enabled = fields.Bool(required=False)
    security_alerts = fields.Bool(required=False)
    transaction_alerts = fields.Bool(required=False)
    compliance_alerts = fields.Bool(required=False)

# Notification templates
DEFAULT_TEMPLATES = {
    'security_alert_email': {
        'template_type': 'security_alert',
        'channel': 'email',
        'subject_template': 'Security Alert - {alert_type}',
        'body_template': '''
        Dear {user_name},
        
        We detected a security event on your account:
        
        Alert Type: {alert_type}
        Time: {timestamp}
        IP Address: {ip_address}
        Details: {details}
        
        If this was not you, please contact our security team immediately.
        
        Best regards,
        NexaFi Security Team
        ''',
        'variables': ['user_name', 'alert_type', 'timestamp', 'ip_address', 'details']
    },
    
    'transaction_confirmation_email': {
        'template_type': 'transaction_alert',
        'channel': 'email',
        'subject_template': 'Transaction Confirmation - {amount} {currency}',
        'body_template': '''
        Dear {user_name},
        
        Your transaction has been processed successfully:
        
        Amount: {amount} {currency}
        Transaction ID: {transaction_id}
        Date: {timestamp}
        Description: {description}
        
        Thank you for using NexaFi.
        
        Best regards,
        NexaFi Team
        ''',
        'variables': ['user_name', 'amount', 'currency', 'transaction_id', 'timestamp', 'description']
    },
    
    'kyc_status_update_email': {
        'template_type': 'compliance_alert',
        'channel': 'email',
        'subject_template': 'KYC Verification Update - {status}',
        'body_template': '''
        Dear {user_name},
        
        Your KYC verification status has been updated:
        
        Status: {status}
        Verification Type: {verification_type}
        Updated: {timestamp}
        
        {additional_message}
        
        Best regards,
        NexaFi Compliance Team
        ''',
        'variables': ['user_name', 'status', 'verification_type', 'timestamp', 'additional_message']
    }
}

class NotificationQueue:
    """Notification queue processor"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        
        # Email configuration (in production, use proper SMTP settings)
        self.smtp_config = {
            'host': os.environ.get('SMTP_HOST', 'localhost'),
            'port': int(os.environ.get('SMTP_PORT', 587)),
            'username': os.environ.get('SMTP_USERNAME', ''),
            'password': os.environ.get('SMTP_PASSWORD', ''),
            'use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
        }
        
        self.start_worker()
    
    def start_worker(self):
        """Start background worker thread"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_notifications, daemon=True)
        self.worker_thread.start()
    
    def stop_worker(self):
        """Stop background worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
    
    def _process_notifications(self):
        """Background worker to process notifications"""
        while self.running:
            try:
                notification_id = self.queue.get(timeout=1)
                self._send_notification(notification_id)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
    
    def _send_notification(self, notification_id: int):
        """Send a notification"""
        notification = Notification.find_by_id(notification_id)
        if not notification:
            return
        
        try:
            if notification.channel == 'email':
                self._send_email(notification)
            elif notification.channel == 'sms':
                self._send_sms(notification)
            elif notification.channel == 'push':
                self._send_push(notification)
            elif notification.channel == 'in_app':
                self._send_in_app(notification)
            
            # Update notification status
            notification.status = 'sent'
            notification.sent_at = datetime.utcnow()
            notification.save()
            
            logger.info(f"Notification {notification_id} sent successfully via {notification.channel}")
            
        except Exception as e:
            # Update notification with error
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.delivery_attempts += 1
            notification.save()
            
            logger.error(f"Failed to send notification {notification_id}: {e}")
            
            # Retry logic for failed notifications
            if notification.delivery_attempts < 3 and notification.priority in ['high', 'urgent']:
                # Re-queue for retry after delay
                threading.Timer(300, lambda: self.queue.put(notification_id)).start()  # 5 minute delay
    
    def _send_email(self, notification: Notification):
        """Send email notification"""
        if not self.smtp_config['host'] or self.smtp_config['host'] == 'localhost':
            # Simulate email sending in development
            logger.info(f"Simulated email sent to user {notification.user_id}: {notification.subject}")
            return
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = self.smtp_config['username']
        msg['To'] = f"user{notification.user_id}@example.com"  # In production, get actual email
        msg['Subject'] = notification.subject or 'NexaFi Notification'
        
        msg.attach(MIMEText(notification.message, 'plain'))
        
        # Send email
        with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
            if self.smtp_config['use_tls']:
                server.starttls()
            if self.smtp_config['username'] and self.smtp_config['password']:
                server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
    
    def _send_sms(self, notification: Notification):
        """Send SMS notification"""
        # Simulate SMS sending (in production, integrate with SMS provider)
        logger.info(f"Simulated SMS sent to user {notification.user_id}: {notification.message[:50]}...")
    
    def _send_push(self, notification: Notification):
        """Send push notification"""
        # Simulate push notification (in production, integrate with push service)
        logger.info(f"Simulated push notification sent to user {notification.user_id}: {notification.subject}")
    
    def _send_in_app(self, notification: Notification):
        """Send in-app notification"""
        # In-app notifications are just stored in database for retrieval
        logger.info(f"In-app notification created for user {notification.user_id}")
    
    def enqueue_notification(self, notification_id: int):
        """Add notification to queue"""
        self.queue.put(notification_id)

# Global notification queue
notification_queue = NotificationQueue()

class TemplateEngine:
    """Simple template engine for notifications"""
    
    @staticmethod
    def render_template(template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        rendered = template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered
    
    @classmethod
    def get_template(cls, template_name: str) -> Optional[NotificationTemplate]:
        """Get template by name"""
        return NotificationTemplate.find_one("template_name = ? AND is_active = 1", (template_name,))

def initialize_templates():
    """Initialize default notification templates"""
    for template_name, template_data in DEFAULT_TEMPLATES.items():
        existing = NotificationTemplate.find_one("template_name = ?", (template_name,))
        if not existing:
            template = NotificationTemplate(
                template_name=template_name,
                template_type=template_data['template_type'],
                channel=template_data['channel'],
                subject_template=template_data['subject_template'],
                body_template=template_data['body_template'],
                variables=json.dumps(template_data['variables'])
            )
            template.save()

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'notification-service',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'queue_size': notification_queue.queue.qsize()
    })

@app.route('/api/v1/notifications/send', methods=['POST'])
@require_auth
@require_permission('notification:write')
@validate_json_request(NotificationSchema)
@audit_action(AuditEventType.SYSTEM_CONFIG_CHANGE, "notification_sent", severity=AuditSeverity.LOW)
def send_notification():
    """Send a notification"""
    data = request.validated_data
    
    # Check user preferences
    preferences = NotificationPreferences.find_one("user_id = ?", (data['user_id'],))
    if preferences:
        # Check if user has enabled this type of notification
        channel = data['channel']
        notification_type = data['notification_type']
        
        if channel == 'email' and not preferences.email_enabled:
            return jsonify({'error': 'User has disabled email notifications'}), 400
        elif channel == 'sms' and not preferences.sms_enabled:
            return jsonify({'error': 'User has disabled SMS notifications'}), 400
        elif channel == 'push' and not preferences.push_enabled:
            return jsonify({'error': 'User has disabled push notifications'}), 400
        
        # Check specific notification type preferences
        if notification_type == 'marketing' and not preferences.marketing_enabled:
            return jsonify({'error': 'User has disabled marketing notifications'}), 400
        elif notification_type == 'security_alert' and not preferences.security_alerts:
            return jsonify({'error': 'User has disabled security alerts'}), 400
        elif notification_type == 'transaction_alert' and not preferences.transaction_alerts:
            return jsonify({'error': 'User has disabled transaction alerts'}), 400
        elif notification_type == 'compliance_alert' and not preferences.compliance_alerts:
            return jsonify({'error': 'User has disabled compliance alerts'}), 400
    
    # Process template if specified
    message = data['message']
    subject = data.get('subject')
    
    if data.get('template_name'):
        template = TemplateEngine.get_template(data['template_name'])
        if template:
            template_data = data.get('template_data', {})
            message = TemplateEngine.render_template(template.body_template, template_data)
            if template.subject_template:
                subject = TemplateEngine.render_template(template.subject_template, template_data)
    
    # Create notification record
    notification = Notification(
        user_id=data['user_id'],
        notification_type=data['notification_type'],
        channel=data['channel'],
        priority=data.get('priority', 'normal'),
        subject=subject,
        message=message,
        template_name=data.get('template_name'),
        template_data=json.dumps(data.get('template_data', {})),
        scheduled_at=data.get('scheduled_at', datetime.utcnow())
    )
    notification.save()
    
    # Queue for immediate sending or schedule for later
    if data.get('scheduled_at') and data['scheduled_at'] > datetime.utcnow():
        notification.status = 'scheduled'
        notification.save()
        # In production, use a proper scheduler like Celery
        logger.info(f"Notification {notification.id} scheduled for {data['scheduled_at']}")
    else:
        notification_queue.enqueue_notification(notification.id)
    
    # Log notification
    audit_logger.log_event(
        AuditEventType.SYSTEM_CONFIG_CHANGE,
        "notification_created",
        user_id=g.current_user['user_id'],
        resource_type='notification',
        resource_id=str(notification.id),
        details={
            'recipient_user_id': data['user_id'],
            'notification_type': data['notification_type'],
            'channel': data['channel'],
            'priority': data.get('priority', 'normal')
        }
    )
    
    return jsonify({
        'notification_id': notification.id,
        'status': notification.status,
        'message': 'Notification queued for delivery'
    }), 201

@app.route('/api/v1/notifications/preferences/<user_id>', methods=['GET'])
@require_auth
def get_notification_preferences(user_id):
    """Get user notification preferences"""
    # Users can only access their own preferences unless they have admin permission
    if g.current_user['user_id'] != user_id and not any(role in ['admin', 'business_owner'] for role in g.current_user.get('roles', [])):
        return jsonify({'error': 'Access denied'}), 403
    
    preferences = NotificationPreferences.find_one("user_id = ?", (user_id,))
    if not preferences:
        # Create default preferences
        preferences = NotificationPreferences(user_id=user_id)
        preferences.save()
    
    return jsonify({'preferences': preferences.to_dict()})

@app.route('/api/v1/notifications/preferences/<user_id>', methods=['PUT'])
@require_auth
@validate_json_request(NotificationPreferencesSchema)
@audit_action(AuditEventType.USER_UPDATE, "notification_preferences_updated")
def update_notification_preferences(user_id):
    """Update user notification preferences"""
    # Users can only update their own preferences unless they have admin permission
    if g.current_user['user_id'] != user_id and not any(role in ['admin', 'business_owner'] for role in g.current_user.get('roles', [])):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.validated_data
    
    preferences = NotificationPreferences.find_one("user_id = ?", (user_id,))
    if not preferences:
        preferences = NotificationPreferences(user_id=user_id)
    
    # Update preferences
    for field in ['email_enabled', 'sms_enabled', 'push_enabled', 'marketing_enabled', 
                  'security_alerts', 'transaction_alerts', 'compliance_alerts']:
        if field in data:
            setattr(preferences, field, data[field])
    
    preferences.updated_at = datetime.utcnow()
    preferences.save()
    
    # Log preference update
    audit_logger.log_user_action(
        AuditEventType.USER_UPDATE,
        user_id,
        "notification_preferences_updated",
        details=data
    )
    
    return jsonify({
        'message': 'Notification preferences updated',
        'preferences': preferences.to_dict()
    })

@app.route('/api/v1/notifications/user/<user_id>', methods=['GET'])
@require_auth
def get_user_notifications(user_id):
    """Get notifications for a user"""
    # Users can only access their own notifications unless they have admin permission
    if g.current_user['user_id'] != user_id and not any(role in ['admin', 'business_owner'] for role in g.current_user.get('roles', [])):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get query parameters
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    status = request.args.get('status')
    notification_type = request.args.get('type')
    
    # Build query
    where_clause = "user_id = ?"
    params = [user_id]
    
    if status:
        where_clause += " AND status = ?"
        params.append(status)
    
    if notification_type:
        where_clause += " AND notification_type = ?"
        params.append(notification_type)
    
    where_clause += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
    
    notifications = Notification.find_all(where_clause, tuple(params))
    
    return jsonify({
        'notifications': [notification.to_dict() for notification in notifications],
        'total': len(notifications),
        'limit': limit,
        'offset': offset
    })

@app.route('/api/v1/notifications/<int:notification_id>/status', methods=['PUT'])
@require_auth
@require_permission('notification:write')
def update_notification_status(notification_id):
    """Update notification status (for admin use)"""
    data = request.get_json() or {}
    new_status = data.get('status')
    
    if new_status not in ['pending', 'sent', 'failed', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    notification = Notification.find_by_id(notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.status = new_status
    if new_status == 'cancelled':
        notification.error_message = 'Cancelled by admin'
    
    notification.save()
    
    return jsonify({
        'message': 'Notification status updated',
        'notification_id': notification_id,
        'status': new_status
    })

@app.route('/api/v1/notifications/stats', methods=['GET'])
@require_auth
@require_permission('notification:read')
def notification_stats():
    """Get notification statistics"""
    # Get statistics for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    total_sent = len(Notification.find_all("status = 'sent' AND created_at >= ?", (thirty_days_ago.isoformat(),)))
    total_failed = len(Notification.find_all("status = 'failed' AND created_at >= ?", (thirty_days_ago.isoformat(),)))
    total_pending = len(Notification.find_all("status = 'pending'"))
    
    # Get stats by channel
    email_sent = len(Notification.find_all("channel = 'email' AND status = 'sent' AND created_at >= ?", (thirty_days_ago.isoformat(),)))
    sms_sent = len(Notification.find_all("channel = 'sms' AND status = 'sent' AND created_at >= ?", (thirty_days_ago.isoformat(),)))
    push_sent = len(Notification.find_all("channel = 'push' AND status = 'sent' AND created_at >= ?", (thirty_days_ago.isoformat(),)))
    
    return jsonify({
        'period': '30_days',
        'total_sent': total_sent,
        'total_failed': total_failed,
        'total_pending': total_pending,
        'success_rate': (total_sent / (total_sent + total_failed)) * 100 if (total_sent + total_failed) > 0 else 0,
        'by_channel': {
            'email': email_sent,
            'sms': sms_sent,
            'push': push_sent
        },
        'queue_size': notification_queue.queue.qsize()
    })

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('/home/ubuntu/nexafi_backend_refactored/notification-service/data', exist_ok=True)
    
    # Initialize default templates
    initialize_templates()
    
    # Development server
    app.run(host='0.0.0.0', port=5006, debug=False)

