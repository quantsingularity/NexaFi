"""
Rate limiting middleware for NexaFi API Gateway
Implements industry-standard rate limiting for financial services
"""

from flask import request, jsonify, g
from functools import wraps
import time
import redis
import json
from typing import Dict, Optional
import hashlib

class RateLimiter:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(
            host='localhost', 
            port=6379, 
            db=0, 
            decode_responses=True
        )
    
    def get_client_id(self) -> str:
        """Get unique client identifier"""
        # Try to get user ID from headers first
        user_id = request.headers.get('X-User-ID')
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        return f"ip:{client_ip}"
    
    def get_rate_limit_key(self, client_id: str, endpoint: str, window: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"rate_limit:{client_id}:{endpoint}:{window}"
    
    def is_rate_limited(self, client_id: str, endpoint: str, limit: int, window: int) -> tuple[bool, Dict]:
        """Check if client is rate limited"""
        current_time = int(time.time())
        window_start = current_time - (current_time % window)
        
        key = self.get_rate_limit_key(client_id, endpoint, str(window_start))
        
        try:
            # Get current count
            current_count = self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            # Check if limit exceeded
            if current_count >= limit:
                return True, {
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': window_start + window,
                    'retry_after': window_start + window - current_time
                }
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            pipe.execute()
            
            return False, {
                'limit': limit,
                'remaining': limit - current_count - 1,
                'reset_time': window_start + window,
                'retry_after': 0
            }
            
        except redis.RedisError:
            # If Redis is down, allow the request (fail open)
            return False, {
                'limit': limit,
                'remaining': limit - 1,
                'reset_time': current_time + window,
                'retry_after': 0
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limit configurations for different endpoints
RATE_LIMITS = {
    # Authentication endpoints - stricter limits
    '/api/v1/auth/login': {'limit': 5, 'window': 300},  # 5 attempts per 5 minutes
    '/api/v1/auth/register': {'limit': 3, 'window': 3600},  # 3 attempts per hour
    '/api/v1/auth/reset-password': {'limit': 3, 'window': 3600},
    
    # Financial transaction endpoints - moderate limits
    '/api/v1/transactions': {'limit': 100, 'window': 60},  # 100 per minute
    '/api/v1/payment-methods': {'limit': 50, 'window': 60},
    '/api/v1/journal-entries': {'limit': 200, 'window': 60},
    
    # Read-only endpoints - higher limits
    '/api/v1/accounts': {'limit': 500, 'window': 60},
    '/api/v1/reports': {'limit': 100, 'window': 60},
    '/api/v1/insights': {'limit': 200, 'window': 60},
    
    # AI/ML endpoints - moderate limits due to computational cost
    '/api/v1/predictions': {'limit': 20, 'window': 60},
    '/api/v1/chat': {'limit': 50, 'window': 60},
    
    # Default rate limit for unspecified endpoints
    'default': {'limit': 1000, 'window': 60}  # 1000 per minute
}

def get_endpoint_rate_limit(path: str) -> Dict:
    """Get rate limit configuration for endpoint"""
    # Check for exact match first
    if path in RATE_LIMITS:
        return RATE_LIMITS[path]
    
    # Check for prefix matches
    for endpoint_pattern, config in RATE_LIMITS.items():
        if endpoint_pattern != 'default' and path.startswith(endpoint_pattern):
            return config
    
    # Return default
    return RATE_LIMITS['default']

def rate_limit(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get client identifier
        client_id = rate_limiter.get_client_id()
        
        # Get endpoint path
        endpoint_path = request.path
        
        # Get rate limit configuration
        config = get_endpoint_rate_limit(endpoint_path)
        
        # Check rate limit
        is_limited, info = rate_limiter.is_rate_limited(
            client_id, 
            endpoint_path, 
            config['limit'], 
            config['window']
        )
        
        # Add rate limit headers to response
        g.rate_limit_info = info
        
        if is_limited:
            response = jsonify({
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Limit: {info["limit"]} per {config["window"]} seconds',
                'retry_after': info['retry_after']
            })
            response.status_code = 429
            response.headers['X-RateLimit-Limit'] = str(info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
            response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
            response.headers['Retry-After'] = str(info['retry_after'])
            return response
        
        return f(*args, **kwargs)
    
    return decorated_function

def add_rate_limit_headers(response):
    """Add rate limit headers to response"""
    if hasattr(g, 'rate_limit_info'):
        info = g.rate_limit_info
        response.headers['X-RateLimit-Limit'] = str(info.get('limit', 0))
        response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
        response.headers['X-RateLimit-Reset'] = str(info.get('reset_time', 0))
    return response

