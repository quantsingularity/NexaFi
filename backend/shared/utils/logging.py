"""
Shared logging utilities for NexaFi services
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from ..config.infrastructure import InfrastructureConfig

class StructuredLogger:
    """Structured logging for better log analysis"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, InfrastructureConfig.LOG_LEVEL))
        
        # Create formatter
        formatter = logging.Formatter(InfrastructureConfig.LOG_FORMAT)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler
        file_handler = logging.FileHandler(f'logs/{service_name}.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _create_log_entry(self, level: str, message: str, 
                         extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create structured log entry"""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'level': level,
            'message': message
        }
        
        if extra_data:
            entry.update(extra_data)
        
        return entry
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        entry = self._create_log_entry('INFO', message, kwargs)
        self.logger.info(json.dumps(entry))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        entry = self._create_log_entry('WARNING', message, kwargs)
        self.logger.warning(json.dumps(entry))
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        entry = self._create_log_entry('ERROR', message, kwargs)
        self.logger.error(json.dumps(entry))
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        entry = self._create_log_entry('DEBUG', message, kwargs)
        self.logger.debug(json.dumps(entry))
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        entry = self._create_log_entry('CRITICAL', message, kwargs)
        self.logger.critical(json.dumps(entry))

def get_logger(service_name: str) -> StructuredLogger:
    """Get structured logger for service"""
    return StructuredLogger(service_name)
