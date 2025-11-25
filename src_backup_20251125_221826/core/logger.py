"""
Logging configuration following best practices.
Provides structured logging with proper formatting and levels.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from .config import get_config


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging.
    
    Outputs logs in JSON format for better parsing and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, default=str)


class ContextualLogger:
    """
    Contextual logger wrapper that adds common fields to all log entries.
    
    Follows the Decorator pattern to enhance logging functionality.
    """
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any] = None):
        self._logger = logger
        self._context = context or {}
    
    def _log_with_context(self, level: int, message: str, *args, **kwargs):
        """Log message with context."""
        extra_fields = {**self._context}
        
        # Add any extra fields from kwargs
        if 'extra_fields' in kwargs:
            extra_fields.update(kwargs.pop('extra_fields'))
        
        # Create log record with extra fields
        self._logger.log(level, message, *args, extra={'extra_fields': extra_fields}, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        kwargs['exc_info'] = True
        self._log_with_context(logging.ERROR, message, *args, **kwargs)


def setup_logger(name: str, context: Dict[str, Any] = None) -> ContextualLogger:
    """
    Setup logger with proper configuration.
    
    Args:
        name: Logger name (usually __name__)
        context: Additional context to include in all log entries
        
    Returns:
        ContextualLogger: Configured logger instance
    """
    config = get_config()
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    log_level = getattr(logging, config.log_level.upper())
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        # Set formatter
        if config.is_production_environment():
            # Use structured JSON format in production
            formatter = StructuredFormatter()
        else:
            # Use simple format for development
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Add default context
    default_context = {
        'service': 'finops-analyzer',
        'version': '4.0.0',
        'environment': 'production' if config.is_production_environment() else 'development'
    }
    
    if context:
        default_context.update(context)
    
    return ContextualLogger(logger, default_context)


def get_performance_logger() -> ContextualLogger:
    """Get logger specifically for performance metrics."""
    return setup_logger('performance', {'category': 'performance'})


def get_security_logger() -> ContextualLogger:
    """Get logger specifically for security events."""
    return setup_logger('security', {'category': 'security'})


def get_business_logger() -> ContextualLogger:
    """Get logger specifically for business events."""
    return setup_logger('business', {'category': 'business'})