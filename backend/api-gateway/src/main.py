import os
import sys
import time
from datetime import datetime

import requests
from flask import Flask, g, jsonify, request
from flask_cors import CORS

# Add shared modules to path
sys.path.append("/home/ubuntu/nexafi_backend_refactored/shared")

from logging.logger import get_logger, log_security_event, setup_request_logging

from audit.audit_logger import audit_logger
from middleware.auth import init_auth_manager, optional_auth
from middleware.rate_limiter import add_rate_limit_headers, rate_limit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "nexafi-api-gateway-secret-key-2024"
)

# Initialize authentication
init_auth_manager(app.config["SECRET_KEY"])

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization", "X-User-ID"])

# Setup request logging
setup_request_logging(app)

# Get logger
logger = get_logger("api_gateway")

# Service registry with health check and circuit breaker support
SERVICES = {
    "user-service": {
        "url": "http://localhost:5001",
        "health_endpoint": "/api/v1/health",
        "routes": ["/api/v1/auth", "/api/v1/users"],
        "timeout": 30,
        "retry_count": 3,
        "circuit_breaker": {"failure_threshold": 5, "recovery_timeout": 60},
    },
    "ledger-service": {
        "url": "http://localhost:5002",
        "health_endpoint": "/api/v1/health",
        "routes": ["/api/v1/accounts", "/api/v1/journal-entries", "/api/v1/reports"],
        "timeout": 30,
        "retry_count": 3,
        "circuit_breaker": {"failure_threshold": 5, "recovery_timeout": 60},
    },
    "payment-service": {
        "url": "http://localhost:5003",
        "health_endpoint": "/api/v1/health",
        "routes": [
            "/api/v1/payment-methods",
            "/api/v1/transactions",
            "/api/v1/wallets",
            "/api/v1/recurring-payments",
            "/api/v1/exchange-rates",
            "/api/v1/analytics",
        ],
        "timeout": 30,
        "retry_count": 3,
        "circuit_breaker": {"failure_threshold": 5, "recovery_timeout": 60},
    },
    "ai-service": {
        "url": "http://localhost:5004",
        "health_endpoint": "/api/v1/health",
        "routes": [
            "/api/v1/predictions",
            "/api/v1/insights",
            "/api/v1/chat",
            "/api/v1/models",
        ],
        "timeout": 60,  # AI operations may take longer
        "retry_count": 2,
        "circuit_breaker": {"failure_threshold": 3, "recovery_timeout": 120},
    },
}

# Circuit breaker state tracking
circuit_breaker_state = {}


def get_service_for_route(path):
    """Determine which service should handle the request"""
    for service_name, config in SERVICES.items():
        for route_prefix in config["routes"]:
            if path.startswith(route_prefix):
                return service_name, config
    return None, None


def is_circuit_breaker_open(service_name):
    """Check if circuit breaker is open for service"""
    if service_name not in circuit_breaker_state:
        circuit_breaker_state[service_name] = {
            "failure_count": 0,
            "last_failure_time": None,
            "state": "closed",  # closed, open, half-open
        }

    state = circuit_breaker_state[service_name]
    config = SERVICES[service_name]["circuit_breaker"]

    if state["state"] == "open":
        # Check if recovery timeout has passed
        if (time.time() - state["last_failure_time"]) > config["recovery_timeout"]:
            state["state"] = "half-open"
            logger.info(f"Circuit breaker for {service_name} moved to half-open state")
            return False
        return True

    return False


def record_service_failure(service_name):
    """Record service failure for circuit breaker"""
    if service_name not in circuit_breaker_state:
        circuit_breaker_state[service_name] = {
            "failure_count": 0,
            "last_failure_time": None,
            "state": "closed",
        }

    state = circuit_breaker_state[service_name]
    config = SERVICES[service_name]["circuit_breaker"]

    state["failure_count"] += 1
    state["last_failure_time"] = time.time()

    if state["failure_count"] >= config["failure_threshold"]:
        state["state"] = "open"
        logger.warning(f"Circuit breaker opened for {service_name}")

        # Log security event for service failures
        log_security_event(
            "service_failure",
            f"Circuit breaker opened for {service_name} due to repeated failures",
            {"service": service_name, "failure_count": state["failure_count"]},
        )


def record_service_success(service_name):
    """Record service success for circuit breaker"""
    if service_name in circuit_breaker_state:
        state = circuit_breaker_state[service_name]
        if state["state"] == "half-open":
            # Reset circuit breaker
            state["failure_count"] = 0
            state["state"] = "closed"
            logger.info(f"Circuit breaker closed for {service_name}")


def forward_request(
    service_name, service_config, path, method, headers=None, data=None, params=None
):
    """Forward request to appropriate service with retry and circuit breaker"""

    # Check circuit breaker
    if is_circuit_breaker_open(service_name):
        return {"error": "Service temporarily unavailable"}, 503

    url = f"{service_config['url']}{path}"
    timeout = service_config.get("timeout", 30)
    retry_count = service_config.get("retry_count", 3)

    # Prepare headers
    forward_headers = {}
    if headers:
        # Forward important headers
        for header_name in ["Authorization", "Content-Type", "X-User-ID"]:
            if header_name in headers:
                forward_headers[header_name] = headers[header_name]

    # Add correlation ID
    if hasattr(g, "correlation_id"):
        forward_headers["X-Correlation-ID"] = g.correlation_id

    last_exception = None

    for attempt in range(retry_count):
        try:
            start_time = time.time()

            # Make request to service
            if method == "GET":
                response = requests.get(
                    url, headers=forward_headers, params=params, timeout=timeout
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=forward_headers,
                    json=data,
                    params=params,
                    timeout=timeout,
                )
            elif method == "PUT":
                response = requests.put(
                    url,
                    headers=forward_headers,
                    json=data,
                    params=params,
                    timeout=timeout,
                )
            elif method == "DELETE":
                response = requests.delete(
                    url, headers=forward_headers, params=params, timeout=timeout
                )
            else:
                return {"error": "Method not supported"}, 405

            response_time = time.time() - start_time

            # Log API call
            logger.info(
                f"Service call: {method} {service_name}{path}",
                extra={
                    "service": service_name,
                    "endpoint": path,
                    "method": method,
                    "status_code": response.status_code,
                    "response_time_ms": response_time * 1000,
                    "attempt": attempt + 1,
                },
            )

            # Record success for circuit breaker
            if response.status_code < 500:
                record_service_success(service_name)

            return response.json() if response.content else {}, response.status_code

        except requests.exceptions.Timeout:
            last_exception = "Service timeout"
            logger.warning(f"Timeout calling {service_name}, attempt {attempt + 1}")

        except requests.exceptions.ConnectionError:
            last_exception = "Service unavailable"
            logger.warning(
                f"Connection error calling {service_name}, attempt {attempt + 1}"
            )

        except Exception as e:
            last_exception = f"Gateway error: {str(e)}"
            logger.error(f"Error calling {service_name}: {str(e)}")

        # Wait before retry (exponential backoff)
        if attempt < retry_count - 1:
            wait_time = (2**attempt) * 0.1  # 0.1, 0.2, 0.4 seconds
            time.sleep(wait_time)

    # All retries failed
    record_service_failure(service_name)

    if "timeout" in last_exception.lower():
        return {"error": last_exception}, 504
    elif "unavailable" in last_exception.lower():
        return {"error": last_exception}, 503
    else:
        return {"error": last_exception}, 500


@app.before_request
def before_request():
    """Pre-request processing"""
    # Security headers check
    if request.method == "POST" and not request.is_json:
        if "multipart/form-data" not in request.content_type:
            log_security_event(
                "invalid_content_type",
                f"Invalid content type: {request.content_type}",
                {"endpoint": request.path, "method": request.method},
            )


@app.after_request
def after_request(response):
    """Post-request processing"""
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    # Add rate limit headers
    response = add_rate_limit_headers(response)

    return response


@app.route("/health", methods=["GET"])
def health_check():
    """Gateway health check"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "services": list(SERVICES.keys()),
        }
    )


@app.route("/api/v1/services", methods=["GET"])
@optional_auth
def list_services():
    """List available services and their status"""
    service_status = {}

    for service_name, config in SERVICES.items():
        try:
            health_url = f"{config['url']}{config['health_endpoint']}"
            response = requests.get(health_url, timeout=5)
            service_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": config["url"],
                "routes": config["routes"],
                "circuit_breaker_state": circuit_breaker_state.get(
                    service_name, {}
                ).get("state", "closed"),
            }
        except Exception:
            service_status[service_name] = {
                "status": "unavailable",
                "url": config["url"],
                "routes": config["routes"],
                "circuit_breaker_state": circuit_breaker_state.get(
                    service_name, {}
                ).get("state", "closed"),
            }

    return jsonify(
        {"services": service_status, "timestamp": datetime.utcnow().isoformat()}
    )


@app.route("/api/v1/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@rate_limit
@optional_auth
def proxy_request(path):
    """Proxy requests to appropriate microservice"""
    full_path = f"/api/v1/{path}"

    # Determine target service
    service_name, service_config = get_service_for_route(full_path)

    if not service_name:
        log_security_event(
            "unknown_endpoint",
            f"Request to unknown endpoint: {full_path}",
            {"method": request.method, "path": full_path},
        )
        return jsonify({"error": "Service not found for this endpoint"}), 404

    # Get request data
    data = None
    if request.is_json:
        data = request.get_json()

    # Log the proxied request
    user_id = getattr(g, "current_user", {}).get("user_id")
    audit_logger.log_api_access(
        user_id=user_id,
        endpoint=full_path,
        method=request.method,
        status_code=200,  # Will be updated based on response
        ip_address=request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr),
        user_agent=request.headers.get("User-Agent", ""),
    )

    # Forward request
    result, status_code = forward_request(
        service_name,
        service_config,
        full_path,
        request.method,
        headers=dict(request.headers),
        data=data,
        params=dict(request.args),
    )

    return jsonify(result), status_code


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    log_security_event(
        "not_found",
        f"404 error for path: {request.path}",
        {"method": request.method, "path": request.path},
    )
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=5000, debug=False)
