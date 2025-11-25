"""
Configuration Management System

This module provides centralized configuration management for the FinOps application.
Follows 12-factor app principles with environment-based configuration,
validation, and type safety.

Features:
- Environment-based configuration
- Type validation with Pydantic
- Secrets management integration
- Configuration validation at startup
- Hot reloading support (development)
- Multi-environment support (dev, staging, prod)
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseSettings):
    """Database configuration"""

    # Connection settings
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="finops", env="DB_NAME")
    username: str = Field(default="finops_user", env="DB_USER")
    password: str = Field(default="finops_password", env="DB_PASSWORD")

    # Connection pool settings
    min_connections: int = Field(default=5, env="DB_MIN_CONNECTIONS")
    max_connections: int = Field(default=20, env="DB_MAX_CONNECTIONS")
    max_queries: int = Field(default=50000, env="DB_MAX_QUERIES")
    max_inactive_connection_lifetime: float = Field(default=300.0, env="DB_MAX_INACTIVE_LIFETIME")

    # Performance settings
    command_timeout: float = Field(default=30.0, env="DB_COMMAND_TIMEOUT")

    # SSL settings
    ssl_enabled: bool = Field(default=False, env="DB_SSL_ENABLED")
    ssl_cert_path: Optional[str] = Field(default=None, env="DB_SSL_CERT_PATH")
    ssl_key_path: Optional[str] = Field(default=None, env="DB_SSL_KEY_PATH")
    ssl_ca_path: Optional[str] = Field(default=None, env="DB_SSL_CA_PATH")

    @property
    def connection_url(self) -> str:
        """Get database connection URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class RedisConfig(BaseSettings):
    """Redis configuration"""

    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    database: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # Connection pool settings
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    connection_timeout: float = Field(default=5.0, env="REDIS_CONNECTION_TIMEOUT")

    # SSL settings
    ssl_enabled: bool = Field(default=False, env="REDIS_SSL_ENABLED")

    @property
    def connection_url(self) -> str:
        """Get Redis connection URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.database}"

    class Config:
        env_prefix = "REDIS_"
        case_sensitive = False


class SecurityConfig(BaseSettings):
    """Security configuration"""

    # JWT settings
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, env="JWT_EXPIRATION_MINUTES")
    jwt_refresh_expiration_days: int = Field(default=7, env="JWT_REFRESH_EXPIRATION_DAYS")

    # API security
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window_minutes: int = Field(default=1, env="RATE_LIMIT_WINDOW_MINUTES")

    # CORS settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")

    # Encryption
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")

    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v, values):
        if v == "your-secret-key-change-in-production":
            env = values.get('environment', Environment.DEVELOPMENT)
            if env == Environment.PRODUCTION:
                raise ValueError("JWT secret key must be changed in production")
        return v

    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


class AWSConfig(BaseSettings):
    """AWS configuration"""

    # AWS credentials
    access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    session_token: Optional[str] = Field(default=None, env="AWS_SESSION_TOKEN")

    # AWS settings
    region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")
    profile: Optional[str] = Field(default=None, env="AWS_PROFILE")

    # Service-specific settings
    s3_bucket: Optional[str] = Field(default=None, env="AWS_S3_BUCKET")
    bedrock_model_id: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", env="BEDROCK_MODEL_ID")

    # Cost and billing
    cost_explorer_enabled: bool = Field(default=True, env="AWS_COST_EXPLORER_ENABLED")
    billing_account_id: Optional[str] = Field(default=None, env="AWS_BILLING_ACCOUNT_ID")

    class Config:
        env_prefix = "AWS_"
        case_sensitive = False


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration"""

    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    log_file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")

    # Metrics
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8080, env="METRICS_PORT")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")

    # Tracing
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")

    # Health checks
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    # External monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    datadog_api_key: Optional[str] = Field(default=None, env="DATADOG_API_KEY")

    class Config:
        env_prefix = "MONITORING_"
        case_sensitive = False


class FinOpsConfig(BaseSettings):
    """FinOps-specific configuration"""

    # Cost thresholds
    cost_threshold_warning: float = Field(default=1000.0, env="COST_THRESHOLD_WARNING")
    cost_threshold_critical: float = Field(default=5000.0, env="COST_THRESHOLD_CRITICAL")

    # Budget settings
    default_budget_currency: str = Field(default="USD", env="DEFAULT_BUDGET_CURRENCY")
    budget_alert_thresholds: List[float] = Field(
        default=[0.8, 0.9, 1.0],
        env="BUDGET_ALERT_THRESHOLDS"
    )

    # Optimization settings
    optimization_confidence_threshold: float = Field(default=0.7, env="OPTIMIZATION_CONFIDENCE_THRESHOLD")
    min_savings_threshold: float = Field(default=10.0, env="MIN_SAVINGS_THRESHOLD")

    # Data collection
    cost_collection_interval_hours: int = Field(default=1, env="COST_COLLECTION_INTERVAL_HOURS")
    metrics_retention_days: int = Field(default=90, env="METRICS_RETENTION_DAYS")

    # ML/AI settings
    enable_ml_recommendations: bool = Field(default=True, env="ENABLE_ML_RECOMMENDATIONS")
    ml_model_update_interval_hours: int = Field(default=24, env="ML_MODEL_UPDATE_INTERVAL_HOURS")

    class Config:
        env_prefix = "FINOPS_"
        case_sensitive = False


class APIConfig(BaseSettings):
    """API configuration"""

    # Server settings
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    workers: int = Field(default=1, env="API_WORKERS")

    # API versioning
    api_version: str = Field(default="v1", env="API_VERSION")
    api_prefix: str = Field(default="/api", env="API_PREFIX")

    # Documentation
    docs_enabled: bool = Field(default=True, env="API_DOCS_ENABLED")
    docs_url: str = Field(default="/docs", env="API_DOCS_URL")
    redoc_url: str = Field(default="/redoc", env="API_REDOC_URL")

    # Request/Response settings
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")

    # Pagination
    default_page_size: int = Field(default=50, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=1000, env="MAX_PAGE_SIZE")

    @validator('workers')
    def validate_workers(cls, v):
        if v < 1:
            raise ValueError("Workers must be at least 1")
        return v

    class Config:
        env_prefix = "API_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """Main application configuration"""

    # Application metadata
    app_name: str = Field(default="FinOps-Teste", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_description: str = Field(default="Enterprise FinOps Platform", env="APP_DESCRIPTION")

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")

    # Timezone
    timezone: str = Field(default="UTC", env="TIMEZONE")

    # Feature flags
    enable_cost_analysis: bool = Field(default=True, env="ENABLE_COST_ANALYSIS")
    enable_optimization: bool = Field(default=True, env="ENABLE_OPTIMIZATION")
    enable_budget_management: bool = Field(default=True, env="ENABLE_BUDGET_MANAGEMENT")
    enable_reporting: bool = Field(default=True, env="ENABLE_REPORTING")

    # External integrations
    enable_webhooks: bool = Field(default=True, env="ENABLE_WEBHOOKS")
    webhook_timeout: int = Field(default=10, env="WEBHOOK_TIMEOUT")

    # Background tasks
    enable_background_tasks: bool = Field(default=True, env="ENABLE_BACKGROUND_TASKS")
    task_queue_url: Optional[str] = Field(default=None, env="TASK_QUEUE_URL")

    @validator('environment')
    def validate_environment(cls, v):
        if v == Environment.PRODUCTION:
            # Additional production validations can be added here
            pass
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class Settings:
    """Main settings container"""

    def __init__(self, env_file: Optional[str] = None):
        # Load environment file if specified
        if env_file and Path(env_file).exists():
            os.environ.setdefault("ENV_FILE", env_file)

        # Initialize all configuration sections
        self.app = AppConfig()
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.security = SecurityConfig()
        self.aws = AWSConfig()
        self.monitoring = MonitoringConfig()
        self.finops = FinOpsConfig()
        self.api = APIConfig()

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self):
        """Validate configuration consistency"""

        # Production-specific validations
        if self.app.environment == Environment.PRODUCTION:
            if self.app.debug:
                raise ValueError("Debug mode cannot be enabled in production")

            if self.security.jwt_secret_key == "your-secret-key-change-in-production":
                raise ValueError("JWT secret key must be changed in production")

            if not self.monitoring.sentry_dsn:
                print("Warning: Sentry DSN not configured for production")

        # Database validation
        if self.app.environment == Environment.PRODUCTION and not self.database.ssl_enabled:
            print("Warning: SSL not enabled for database in production")

        # AWS validation
        if self.finops.enable_ml_recommendations and not self.aws.bedrock_model_id:
            raise ValueError("Bedrock model ID required when ML recommendations are enabled")

    def get_database_url(self) -> str:
        """Get database connection URL"""
        return self.database.connection_url

    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        return self.redis.connection_url

    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.app.environment == Environment.DEVELOPMENT

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.app.environment == Environment.PRODUCTION

    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.app.environment == Environment.TESTING or self.app.testing

    def get_cors_config(self) -> Dict[str, Union[List[str], bool]]:
        """Get CORS configuration for FastAPI"""
        return {
            "allow_origins": self.security.cors_origins,
            "allow_methods": self.security.cors_methods,
            "allow_headers": self.security.cors_headers,
            "allow_credentials": True
        }

    def to_dict(self) -> Dict[str, Dict]:
        """Convert settings to dictionary (excluding sensitive data)"""
        return {
            "app": self.app.dict(exclude={"debug"}),
            "database": self.database.dict(exclude={"password"}),
            "redis": self.redis.dict(exclude={"password"}),
            "security": self.security.dict(exclude={"jwt_secret_key", "encryption_key"}),
            "aws": self.aws.dict(exclude={"access_key_id", "secret_access_key", "session_token"}),
            "monitoring": self.monitoring.dict(exclude={"sentry_dsn", "datadog_api_key"}),
            "finops": self.finops.dict(),
            "api": self.api.dict()
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(env_file: Optional[str] = None) -> Settings:
    """Get global settings instance"""
    global _settings

    if _settings is None:
        _settings = Settings(env_file)

    return _settings


def reload_settings(env_file: Optional[str] = None) -> Settings:
    """Reload settings (useful for development)"""
    global _settings
    _settings = Settings(env_file)
    return _settings


# Convenience functions for common configurations
def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return get_settings().database


def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return get_settings().security


def get_aws_config() -> AWSConfig:
    """Get AWS configuration"""
    return get_settings().aws


def get_finops_config() -> FinOpsConfig:
    """Get FinOps configuration"""
    return get_settings().finops
