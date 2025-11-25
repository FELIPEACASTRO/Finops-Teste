"""
Structured Logging System

This module provides a comprehensive logging system following observability
best practices. Features structured JSON logging, correlation IDs,
performance tracking, and integration with monitoring systems.

Features:
- Structured JSON logging for machine readability
- Correlation ID tracking across requests
- Performance and latency tracking
- Error tracking with stack traces
- Log level management
- Integration with external logging systems
- Security-aware logging (no sensitive data)
"""

import json
import logging
import sys
import time
import traceback
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import uuid4

from pydantic import BaseSettings, Field


class LoggingConfig(BaseSettings):
    """Logging configuration settings"""
    
    # Log levels
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    root_log_level: str = Field(default="WARNING", env="ROOT_LOG_LEVEL")
    
    # Output settings
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    log_output: str = Field(default="stdout", env="LOG_OUTPUT")  # stdout, file, or both
    log_file_path: str = Field(default="/var/log/finops/app.log", env="LOG_FILE_PATH")
    
    # Structured logging settings
    service_name: str = Field(default="finops-teste", env="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Performance tracking
    enable_performance_logging: bool = Field(default=True, env="ENABLE_PERFORMANCE_LOGGING")
    slow_query_threshold_ms: float = Field(default=1000.0, env="SLOW_QUERY_THRESHOLD_MS")
    
    # External integrations
    enable_sentry: bool = Field(default=False, env="ENABLE_SENTRY")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Security settings
    mask_sensitive_data: bool = Field(default=True, env="MASK_SENSITIVE_DATA")
    sensitive_fields: list = Field(
        default_factory=lambda: ["password", "token", "key", "secret", "authorization"]
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def __init__(self, config: LoggingConfig):
        super().__init__()
        self.config = config
        self.sensitive_fields = [field.lower() for field in config.sensitive_fields]
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": {
                "name": self.config.service_name,
                "version": self.config.service_version,
                "environment": self.config.environment
            }
        }
        
        # Add context information
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_entry["user_id"] = user_id
        
        # Add source information
        log_entry["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName
        }
        
        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'message', 'exc_info', 'exc_text',
                          'stack_info', 'getMessage']:
                extra_fields[key] = self._mask_sensitive_data(key, value)
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        # Add exception information
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add performance information if available
        if hasattr(record, 'duration_ms'):
            log_entry["performance"] = {
                "duration_ms": record.duration_ms,
                "is_slow": record.duration_ms > self.config.slow_query_threshold_ms
            }
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)
    
    def _mask_sensitive_data(self, key: str, value: Any) -> Any:
        """Mask sensitive data in log entries"""
        if not self.config.mask_sensitive_data:
            return value
        
        key_lower = key.lower()
        
        # Check if key contains sensitive field names
        for sensitive_field in self.sensitive_fields:
            if sensitive_field in key_lower:
                if isinstance(value, str) and len(value) > 4:
                    return value[:2] + "*" * (len(value) - 4) + value[-2:]
                else:
                    return "***MASKED***"
        
        # Mask dictionary values recursively
        if isinstance(value, dict):
            return {k: self._mask_sensitive_data(k, v) for k, v in value.items()}
        
        return value


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.extra_data = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation}", extra=self.extra_data)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        extra_data = {
            **self.extra_data,
            "duration_ms": duration_ms,
            "operation": self.operation
        }
        
        if exc_type:
            self.logger.error(
                f"Operation failed: {self.operation}",
                extra=extra_data,
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            log_level = logging.WARNING if duration_ms > 1000 else logging.INFO
            self.logger.log(
                log_level,
                f"Operation completed: {self.operation}",
                extra=extra_data
            )


class FinOpsLogger:
    """Enhanced logger with FinOps-specific functionality"""
    
    def __init__(self, name: str, config: LoggingConfig):
        self.config = config
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with appropriate handlers and formatters"""
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Create formatter
        if self.config.log_format.lower() == "json":
            formatter = StructuredFormatter(self.config)
        else:
            formatter = TextFormatter()
        
        # Add stdout handler
        if self.config.log_output in ["stdout", "both"]:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(formatter)
            self.logger.addHandler(stdout_handler)
        
        # Add file handler
        if self.config.log_output in ["file", "both"]:
            try:
                file_handler = logging.FileHandler(self.config.log_file_path)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                # Fallback to stdout if file logging fails
                print(f"Failed to setup file logging: {e}", file=sys.stderr)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)
    
    def performance(self, operation: str, **kwargs) -> PerformanceLogger:
        """Create performance logging context"""
        return PerformanceLogger(self.logger, operation, **kwargs)
    
    def cost_analysis(self, message: str, cost_data: Dict[str, Any], **kwargs):
        """Log cost analysis specific information"""
        extra = {
            **kwargs,
            "cost_data": cost_data,
            "event_type": "cost_analysis"
        }
        self.info(message, **extra)
    
    def optimization(self, message: str, optimization_data: Dict[str, Any], **kwargs):
        """Log optimization specific information"""
        extra = {
            **kwargs,
            "optimization_data": optimization_data,
            "event_type": "optimization"
        }
        self.info(message, **extra)
    
    def budget_alert(self, message: str, budget_data: Dict[str, Any], **kwargs):
        """Log budget alert information"""
        extra = {
            **kwargs,
            "budget_data": budget_data,
            "event_type": "budget_alert"
        }
        self.warning(message, **extra)
    
    def security_event(self, message: str, security_data: Dict[str, Any], **kwargs):
        """Log security-related events"""
        extra = {
            **kwargs,
            "security_data": security_data,
            "event_type": "security"
        }
        self.warning(message, **extra)
    
    def api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """Log API request information"""
        extra = {
            **kwargs,
            "http": {
                "method": method,
                "path": path,
                "status_code": status_code
            },
            "duration_ms": duration_ms,
            "event_type": "api_request"
        }
        
        log_level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
        self.logger.log(log_level, f"{method} {path} - {status_code}", extra=extra)


# Global logging configuration
_config: Optional[LoggingConfig] = None
_loggers: Dict[str, FinOpsLogger] = {}


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Setup global logging configuration"""
    global _config
    
    if config is None:
        config = LoggingConfig()
    
    _config = config
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.root_log_level.upper()))
    
    # Setup Sentry integration if enabled
    if config.enable_sentry and config.sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            sentry_logging = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
            
            sentry_sdk.init(
                dsn=config.sentry_dsn,
                integrations=[sentry_logging],
                environment=config.environment,
                release=config.service_version
            )
        except ImportError:
            print("Sentry SDK not installed, skipping Sentry integration", file=sys.stderr)


def get_logger(name: str) -> FinOpsLogger:
    """Get or create a logger instance"""
    global _config, _loggers
    
    if _config is None:
        setup_logging()
    
    if name not in _loggers:
        _loggers[name] = FinOpsLogger(name, _config)
    
    return _loggers[name]


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context"""
    correlation_id_var.set(correlation_id)


def set_request_id(request_id: str) -> None:
    """Set request ID for current context"""
    request_id_var.set(request_id)


def set_user_id(user_id: str) -> None:
    """Set user ID for current context"""
    user_id_var.set(user_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid4())


# Context manager for request tracking
class RequestContext:
    """Context manager for request-scoped logging context"""
    
    def __init__(
        self,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        self.correlation_id = correlation_id or generate_correlation_id()
        self.request_id = request_id
        self.user_id = user_id
        
        self.correlation_token = None
        self.request_token = None
        self.user_token = None
    
    def __enter__(self):
        self.correlation_token = correlation_id_var.set(self.correlation_id)
        if self.request_id:
            self.request_token = request_id_var.set(self.request_id)
        if self.user_id:
            self.user_token = user_id_var.set(self.user_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.correlation_token:
            correlation_id_var.reset(self.correlation_token)
        if self.request_token:
            request_id_var.reset(self.request_token)
        if self.user_token:
            user_id_var.reset(self.user_token)