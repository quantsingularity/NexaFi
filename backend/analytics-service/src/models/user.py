from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import json

db = SQLAlchemy()

class Dashboard(db.Model):
    __tablename__ = 'dashboards'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Dashboard configuration
    layout = db.Column(db.Text)  # JSON layout configuration
    widgets = db.Column(db.Text)  # JSON widget configuration
    filters = db.Column(db.Text)  # JSON default filters
    refresh_interval = db.Column(db.Integer, default=300)  # seconds
    
    # Access control
    is_public = db.Column(db.Boolean, default=False)
    shared_with = db.Column(db.Text)  # JSON array of user IDs
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    is_template = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))  # financial, operational, executive
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('Report', backref='dashboard', cascade='all, delete-orphan')
    
    def get_layout(self):
        return json.loads(self.layout) if self.layout else {}
    
    def set_layout(self, layout_data):
        self.layout = json.dumps(layout_data)
    
    def get_widgets(self):
        return json.loads(self.widgets) if self.widgets else []
    
    def set_widgets(self, widgets_data):
        self.widgets = json.dumps(widgets_data)
    
    def get_filters(self):
        return json.loads(self.filters) if self.filters else {}
    
    def set_filters(self, filters_data):
        self.filters = json.dumps(filters_data)
    
    def get_shared_with(self):
        return json.loads(self.shared_with) if self.shared_with else []
    
    def set_shared_with(self, user_ids):
        self.shared_with = json.dumps(user_ids)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'layout': self.get_layout(),
            'widgets': self.get_widgets(),
            'filters': self.get_filters(),
            'refresh_interval': self.refresh_interval,
            'is_public': self.is_public,
            'shared_with': self.get_shared_with(),
            'is_active': self.is_active,
            'is_template': self.is_template,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Widget(db.Model):
    __tablename__ = 'widgets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dashboard_id = db.Column(db.String(36), nullable=False, index=True)
    
    # Widget configuration
    name = db.Column(db.String(200), nullable=False)
    widget_type = db.Column(db.String(50), nullable=False)  # chart, table, metric, gauge
    data_source = db.Column(db.String(100), nullable=False)  # API endpoint or query
    
    # Layout and styling
    position_x = db.Column(db.Integer, default=0)
    position_y = db.Column(db.Integer, default=0)
    width = db.Column(db.Integer, default=4)
    height = db.Column(db.Integer, default=3)
    
    # Configuration
    config = db.Column(db.Text)  # JSON widget-specific configuration
    filters = db.Column(db.Text)  # JSON widget filters
    
    # Caching
    cache_duration = db.Column(db.Integer, default=300)  # seconds
    last_cached = db.Column(db.DateTime)
    cached_data = db.Column(db.Text)  # JSON cached data
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_config(self):
        return json.loads(self.config) if self.config else {}
    
    def set_config(self, config_data):
        self.config = json.dumps(config_data)
    
    def get_filters(self):
        return json.loads(self.filters) if self.filters else {}
    
    def set_filters(self, filters_data):
        self.filters = json.dumps(filters_data)
    
    def get_cached_data(self):
        return json.loads(self.cached_data) if self.cached_data else None
    
    def set_cached_data(self, data):
        self.cached_data = json.dumps(data)
        self.last_cached = datetime.utcnow()
    
    def is_cache_valid(self):
        if not self.last_cached or not self.cached_data:
            return False
        return (datetime.utcnow() - self.last_cached).total_seconds() < self.cache_duration
    
    def to_dict(self):
        return {
            'id': self.id,
            'dashboard_id': self.dashboard_id,
            'name': self.name,
            'widget_type': self.widget_type,
            'data_source': self.data_source,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'width': self.width,
            'height': self.height,
            'config': self.get_config(),
            'filters': self.get_filters(),
            'cache_duration': self.cache_duration,
            'last_cached': self.last_cached.isoformat() if self.last_cached else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dashboard_id = db.Column(db.String(36), db.ForeignKey('dashboards.id'))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    
    # Report details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    report_type = db.Column(db.String(50), nullable=False)  # financial, operational, custom
    
    # Query and data
    query = db.Column(db.Text)  # SQL query or data source configuration
    parameters = db.Column(db.Text)  # JSON parameters
    
    # Scheduling
    schedule_type = db.Column(db.String(20))  # manual, daily, weekly, monthly
    schedule_config = db.Column(db.Text)  # JSON schedule configuration
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    
    # Output configuration
    output_format = db.Column(db.String(20), default='json')  # json, csv, pdf, excel
    email_recipients = db.Column(db.Text)  # JSON array of email addresses
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, paused, error
    last_error = db.Column(db.Text)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = db.relationship('ReportExecution', backref='report', cascade='all, delete-orphan')
    
    def get_parameters(self):
        return json.loads(self.parameters) if self.parameters else {}
    
    def set_parameters(self, params):
        self.parameters = json.dumps(params)
    
    def get_schedule_config(self):
        return json.loads(self.schedule_config) if self.schedule_config else {}
    
    def set_schedule_config(self, config):
        self.schedule_config = json.dumps(config)
    
    def get_email_recipients(self):
        return json.loads(self.email_recipients) if self.email_recipients else []
    
    def set_email_recipients(self, emails):
        self.email_recipients = json.dumps(emails)
    
    def calculate_next_run(self):
        """Calculate next run time based on schedule"""
        if self.schedule_type == 'daily':
            return datetime.utcnow() + timedelta(days=1)
        elif self.schedule_type == 'weekly':
            return datetime.utcnow() + timedelta(weeks=1)
        elif self.schedule_type == 'monthly':
            return datetime.utcnow() + timedelta(days=30)
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'dashboard_id': self.dashboard_id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'report_type': self.report_type,
            'query': self.query,
            'parameters': self.get_parameters(),
            'schedule_type': self.schedule_type,
            'schedule_config': self.get_schedule_config(),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'output_format': self.output_format,
            'email_recipients': self.get_email_recipients(),
            'status': self.status,
            'last_error': self.last_error,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ReportExecution(db.Model):
    __tablename__ = 'report_executions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('reports.id'), nullable=False)
    
    # Execution details
    status = db.Column(db.String(20), default='running')  # running, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Results
    result_data = db.Column(db.Text)  # JSON result data
    result_file_path = db.Column(db.String(500))  # Path to generated file
    row_count = db.Column(db.Integer)
    
    # Error handling
    error_message = db.Column(db.Text)
    execution_time = db.Column(db.Float)  # seconds
    
    # Metadata
    triggered_by = db.Column(db.String(20), default='manual')  # manual, scheduled, api
    parameters_used = db.Column(db.Text)  # JSON parameters used
    
    def get_result_data(self):
        return json.loads(self.result_data) if self.result_data else None
    
    def set_result_data(self, data):
        self.result_data = json.dumps(data)
    
    def get_parameters_used(self):
        return json.loads(self.parameters_used) if self.parameters_used else {}
    
    def set_parameters_used(self, params):
        self.parameters_used = json.dumps(params)
    
    def mark_completed(self, result_data=None, row_count=None):
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if result_data:
            self.set_result_data(result_data)
        if row_count is not None:
            self.row_count = row_count
        if self.started_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()
    
    def mark_failed(self, error_message):
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        if self.started_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result_file_path': self.result_file_path,
            'row_count': self.row_count,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'triggered_by': self.triggered_by,
            'parameters_used': self.get_parameters_used(),
            'created_at': self.started_at.isoformat()
        }

class DataSource(db.Model):
    __tablename__ = 'data_sources'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    
    # Data source details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    source_type = db.Column(db.String(50), nullable=False)  # api, database, file, service
    
    # Connection configuration
    connection_config = db.Column(db.Text)  # JSON connection details
    authentication = db.Column(db.Text)  # JSON auth details (encrypted)
    
    # Data schema
    schema_config = db.Column(db.Text)  # JSON schema definition
    sample_data = db.Column(db.Text)  # JSON sample data
    
    # Status and health
    status = db.Column(db.String(20), default='active')  # active, inactive, error
    last_tested = db.Column(db.DateTime)
    last_error = db.Column(db.Text)
    
    # Caching
    cache_enabled = db.Column(db.Boolean, default=True)
    cache_duration = db.Column(db.Integer, default=3600)  # seconds
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_connection_config(self):
        return json.loads(self.connection_config) if self.connection_config else {}
    
    def set_connection_config(self, config):
        self.connection_config = json.dumps(config)
    
    def get_authentication(self):
        return json.loads(self.authentication) if self.authentication else {}
    
    def set_authentication(self, auth):
        self.authentication = json.dumps(auth)
    
    def get_schema_config(self):
        return json.loads(self.schema_config) if self.schema_config else {}
    
    def set_schema_config(self, schema):
        self.schema_config = json.dumps(schema)
    
    def get_sample_data(self):
        return json.loads(self.sample_data) if self.sample_data else None
    
    def set_sample_data(self, data):
        self.sample_data = json.dumps(data)
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'source_type': self.source_type,
            'schema_config': self.get_schema_config(),
            'sample_data': self.get_sample_data(),
            'status': self.status,
            'last_tested': self.last_tested.isoformat() if self.last_tested else None,
            'last_error': self.last_error,
            'cache_enabled': self.cache_enabled,
            'cache_duration': self.cache_duration,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'connection_config': self.get_connection_config(),
                'authentication': self.get_authentication()
            })
        
        return data

class Metric(db.Model):
    __tablename__ = 'metrics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    
    # Metric definition
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    metric_type = db.Column(db.String(50), nullable=False)  # kpi, gauge, counter, ratio
    
    # Calculation
    calculation_method = db.Column(db.String(50), nullable=False)  # sum, avg, count, custom
    formula = db.Column(db.Text)  # Custom formula or SQL
    data_source_id = db.Column(db.String(36))
    
    # Display configuration
    unit = db.Column(db.String(20))  # $, %, count, etc.
    format_config = db.Column(db.Text)  # JSON formatting options
    
    # Thresholds and alerts
    target_value = db.Column(db.Float)
    warning_threshold = db.Column(db.Float)
    critical_threshold = db.Column(db.Float)
    
    # Current value and history
    current_value = db.Column(db.Float)
    previous_value = db.Column(db.Float)
    last_calculated = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(20), default='normal')  # normal, warning, critical
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    history = db.relationship('MetricHistory', backref='metric', cascade='all, delete-orphan')
    
    def get_format_config(self):
        return json.loads(self.format_config) if self.format_config else {}
    
    def set_format_config(self, config):
        self.format_config = json.dumps(config)
    
    def calculate_change(self):
        """Calculate percentage change from previous value"""
        if self.previous_value and self.previous_value != 0:
            return ((self.current_value - self.previous_value) / self.previous_value) * 100
        return 0
    
    def update_status(self):
        """Update status based on thresholds"""
        if self.current_value is None:
            self.status = 'unknown'
        elif self.critical_threshold and self.current_value <= self.critical_threshold:
            self.status = 'critical'
        elif self.warning_threshold and self.current_value <= self.warning_threshold:
            self.status = 'warning'
        else:
            self.status = 'normal'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'metric_type': self.metric_type,
            'calculation_method': self.calculation_method,
            'formula': self.formula,
            'data_source_id': self.data_source_id,
            'unit': self.unit,
            'format_config': self.get_format_config(),
            'target_value': self.target_value,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'current_value': self.current_value,
            'previous_value': self.previous_value,
            'change_percentage': self.calculate_change(),
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MetricHistory(db.Model):
    __tablename__ = 'metric_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_id = db.Column(db.String(36), db.ForeignKey('metrics.id'), nullable=False)
    
    # Historical data
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Context
    calculation_details = db.Column(db.Text)  # JSON calculation details
    data_points = db.Column(db.Integer)  # Number of data points used
    
    def get_calculation_details(self):
        return json.loads(self.calculation_details) if self.calculation_details else {}
    
    def set_calculation_details(self, details):
        self.calculation_details = json.dumps(details)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_id': self.metric_id,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'calculation_details': self.get_calculation_details(),
            'data_points': self.data_points
        }

