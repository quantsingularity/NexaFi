from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import requests
import json
import time
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexafi-api-gateway-secret-key-2024'

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization", "X-User-ID"])

# Service registry
SERVICES = {
    'user-service': {
        'url': 'http://localhost:5001',
        'health_endpoint': '/api/v1/health',
        'routes': ['/api/v1/auth', '/api/v1/users']
    },
    'ledger-service': {
        'url': 'http://localhost:5002',
        'health_endpoint': '/api/v1/health',
        'routes': ['/api/v1/accounts', '/api/v1/journal-entries', '/api/v1/reports']
    },
    'payment-service': {
        'url': 'http://localhost:5003',
        'health_endpoint': '/api/v1/health',
        'routes': ['/api/v1/payment-methods', '/api/v1/transactions', '/api/v1/wallets', '/api/v1/recurring-payments', '/api/v1/exchange-rates', '/api/v1/analytics']
    },
    'ai-service': {
        'url': 'http://localhost:5004',
        'health_endpoint': '/api/v1/health',
        'routes': ['/api/v1/predictions', '/api/v1/insights', '/api/v1/chat', '/api/v1/models']
    }
}

def get_service_for_route(path):
    """Determine which service should handle the request"""
    for service_name, config in SERVICES.items():
        for route_prefix in config['routes']:
            if path.startswith(route_prefix):
                return service_name, config['url']
    return None, None

def forward_request(service_url, path, method, headers=None, data=None, params=None):
    """Forward request to appropriate service"""
    try:
        url = f"{service_url}{path}"
        
        # Prepare headers
        forward_headers = {}
        if headers:
            # Forward important headers
            for header_name in ['Authorization', 'Content-Type', 'X-User-ID']:
                if header_name in headers:
                    forward_headers[header_name] = headers[header_name]
        
        # Make request to service
        if method == 'GET':
            response = requests.get(url, headers=forward_headers, params=params, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=forward_headers, json=data, params=params, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=forward_headers, json=data, params=params, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=forward_headers, params=params, timeout=30)
        else:
            return {'error': 'Method not supported'}, 405
        
        return response.json() if response.content else {}, response.status_code
        
    except requests.exceptions.Timeout:
        return {'error': 'Service timeout'}, 504
    except requests.exceptions.ConnectionError:
        return {'error': 'Service unavailable'}, 503
    except Exception as e:
        return {'error': f'Gateway error: {str(e)}'}, 500

@app.route('/api/v1/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_request(path):
    """Proxy requests to appropriate microservice"""
    full_path = f"/api/v1/{path}"
    
    # Determine target service
    service_name, service_url = get_service_for_route(full_path)
    
    if not service_name:
        return jsonify({'error': 'Service not found for this endpoint'}), 404
    
    # Get request data
    data = None
    if request.is_json:
        data = request.get_json()
    
    # Forward request
    result, status_code = forward_request(
        service_url,
        full_path,
        request.method,
        headers=dict(request.headers),
        data=data,
        params=dict(request.args)
    )
    
    return jsonify(result), status_code

@app.route('/health', methods=['GET'])
def gateway_health():
    """Gateway health check"""
    service_status = {}
    overall_healthy = True
    
    for service_name, config in SERVICES.items():
        try:
            response = requests.get(f"{config['url']}{config['health_endpoint']}", timeout=5)
            service_status[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time_ms': int(response.elapsed.total_seconds() * 1000)
            }
            if response.status_code != 200:
                overall_healthy = False
        except Exception as e:
            service_status[service_name] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
    
    return jsonify({
        'status': 'healthy' if overall_healthy else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'services': service_status,
        'gateway_version': '1.0.0'
    }), 200 if overall_healthy else 503

@app.route('/api/v1/services', methods=['GET'])
def list_services():
    """List available services and their endpoints"""
    service_info = {}
    
    for service_name, config in SERVICES.items():
        service_info[service_name] = {
            'url': config['url'],
            'routes': config['routes'],
            'health_endpoint': config['health_endpoint']
        }
    
    return jsonify({
        'services': service_info,
        'total_services': len(SERVICES)
    }), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'NexaFi API Gateway',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'available_endpoints': {
            'health': '/health',
            'services': '/api/v1/services',
            'user_service': '/api/v1/auth, /api/v1/users',
            'ledger_service': '/api/v1/accounts, /api/v1/journal-entries, /api/v1/reports',
            'payment_service': '/api/v1/payment-methods, /api/v1/transactions, /api/v1/wallets',
            'ai_service': '/api/v1/predictions, /api/v1/insights, /api/v1/chat'
        }
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal gateway error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

