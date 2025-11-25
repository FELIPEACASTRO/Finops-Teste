"""
Configuration Management for FinOps-Teste

This module implements configuration management following the 12-factor app methodology
and Clean Architecture principles. All configuration is externalized and validated.

Key Features:
- Environment-based configuration
- Type safety with Pydantic
- Secrets management integration
- FinOps-specific settings
- Performance tuning parameters
- Security configuration

Author: Manus AI
Date: November 25, 2025
"""

import os
from functools import lru_cache
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseSettings, Field, validator, AnyHttpUrl
from pydantic.networks import PostgresDsn


class Environment(str, Enum):
    """Application environment enumeration."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class FinOpsSettings(BaseSettings):
    """FinOps-specific configuration settings."""
    
    # Cost optimization settings
    cost_optimization_enabled: bool = Field(True, description="Enable automated cost optimization")
    rightsizing_threshold: float = Field(0.7, description="CPU utilization threshold for rightsizing recommendations")
    waste_detection_enabled: bool = Field(True, description="Enable waste detection algorithms")
    
    # Budget and alerting
    default_budget_threshold: float = Field(0.8, description="Default budget alert threshold (80%)")
    anomaly_detection_sensitivity: float = Field(0.95, description="Anomaly detection sensitivity (95%)")
    
    # Forecasting
    forecasting_enabled: bool = Field(True, description="Enable cost forecasting")
    forecasting_horizon_days: int = Field(90, description="Forecasting horizon in days")
    
    # Tagging strategy
    required_tags: List[str] = Field(
        default=["Owner", "CostCenter", "Project", "Environment"],
        description="Required tags for all resources"
    )
    
    # Cloud provider settings
    aws_regions: List[str] = Field(
        default=["us-east-1", "us-west-2", "eu-west-1"],
        description="AWS regions to monitor"
    )
    azure_regions: List[str] = Field(
        default=["eastus", "westus2", "westeurope"],
        description="Azure regions to monitor"
    )
    gcp_regions: List[str] = Field(
        default=["us-central1", "us-west1", "europe-west1"],
        description="GCP regions to monitor"
    )


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # Connection settings
    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    name: str = Field("finops_teste", description="Database name")
    username: str = Field("finops_user", description="Database username")
    password: str = Field("", description="Database password", env="DB_PASSWORD")
    
    # Connection pool settings
    pool_size: int = Field(20, description="Connection pool size")
    max_overflow: int = Field(30, description="Maximum pool overflow")
    pool_timeout: int = Field(30, description="Pool timeout in seconds")
    pool_recycle: int = Field(3600, description="Pool recycle time in seconds")
    
    # Performance settings
    echo: bool = Field(False, description="Echo SQL queries")
    echo_pool: bool = Field(False, description="Echo pool events")
    
    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def async_url(self) -> str:
        """Generate async database URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    host: str = Field("localhost", description="Redis host")
    port: int = Field(6379, description="Redis port")
    password: str = Field("", description="Redis password", env="REDIS_PASSWORD")
    db: int = Field(0, description="Redis database number")
    
    # Connection pool settings
    max_connections: int = Field(100, description="Maximum Redis connections")
    retry_on_timeout: bool = Field(True, description="Retry on timeout")
    socket_timeout: int = Field(5, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(5, description="Socket connect timeout")
    
    # Cache settings
    default_ttl: int = Field(3600, description="Default TTL in seconds")
    session_ttl: int = Field(86400, description="Session TTL in seconds")
    
    @property
    def url(self) -> str:
        """Generate Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    # JWT settings
    jwt_secret_key: str = Field("", description="JWT secret key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(30, description="Access token expiration")
    jwt_refresh_token_expire_days: int = Field(7, description="Refresh token expiration")
    
    # Password settings
    password_min_length: int = Field(8, description="Minimum password length")
    password_require_uppercase: bool = Field(True, description="Require uppercase letters")
    password_require_lowercase: bool = Field(True, description="Require lowercase letters")
    password_require_numbers: bool = Field(True, description="Require numbers")
    password_require_special: bool = Field(True, description="Require special characters")
    
    # Rate limiting
    rate_limit_requests: int = Field(1000, description="Requests per minute per IP")
    rate_limit_window: int = Field(60, description="Rate limit window in seconds")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # API key settings
    api_key_header: str = Field("X-API-Key", description="API key header name")
    api_key_length: int = Field(32, description="API key length")
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret key."""
        if not v:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""
    
    # Metrics
    metrics_enabled: bool = Field(True, description="Enable metrics collection")
    metrics_port: int = Field(9090, description="Metrics server port")
    
    # Tracing
    tracing_enabled: bool = Field(True, description="Enable distributed tracing")
    jaeger_endpoint: str = Field("http://localhost:14268/api/traces", description="Jaeger endpoint")
    trace_sample_rate: float = Field(0.1, description="Trace sampling rate")
    
    # Logging
    log_level: LogLevel = Field(LogLevel.INFO, description="Logging level")
    log_format: str = Field("json", description="Log format (json|text)")
    log_file: Optional[str] = Field(None, description="Log file path")
    
    # Health checks
    health_check_interval: int = Field(30, description="Health check interval in seconds")
    health_check_timeout: int = Field(5, description="Health check timeout in seconds")
    
    # Alerting
    alerting_enabled: bool = Field(True, description="Enable alerting")
    slack_webhook_url: str = Field("", description="Slack webhook URL", env="SLACK_WEBHOOK_URL")
    email_alerts_enabled: bool = Field(True, description="Enable email alerts")


class PerformanceSettings(BaseSettings):
    """Performance optimization settings."""
    
    # Server settings
    workers: int = Field(4, description="Number of worker processes")
    worker_connections: int = Field(1000, description="Worker connections")
    max_requests: int = Field(1000000, description="Max requests per worker")
    max_requests_jitter: int = Field(100, description="Max requests jitter")
    
    # Timeouts
    request_timeout: int = Field(30, description="Request timeout in seconds")
    keep_alive_timeout: int = Field(5, description="Keep-alive timeout")
    graceful_timeout: int = Field(30, description="Graceful shutdown timeout")
    
    # Caching
    cache_enabled: bool = Field(True, description="Enable caching")
    cache_default_ttl: int = Field(3600, description="Default cache TTL")
    cache_max_size: int = Field(1000, description="Max cache size")
    
    # Connection limits
    max_connections: int = Field(10000, description="Maximum concurrent connections")
    backlog: int = Field(2048, description="TCP backlog size")
    
    # Performance targets (SLOs)
    target_p95_latency_ms: int = Field(200, description="Target P95 latency in ms")
    target_throughput_tps: int = Field(2000, description="Target throughput in TPS")
    target_availability: float = Field(0.999, description="Target availability (99.9%)")


class Settings(BaseSettings):
    """
    Main application settings combining all configuration sections.
    
    This follows the composition pattern to organize related settings
    while maintaining a single configuration interface.
    """
    
    # Application settings
    app_name: str = Field("FinOps-Teste", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    environment: Environment = Field(Environment.DEVELOPMENT, description="Application environment")
    debug: bool = Field(False, description="Debug mode")
    
    # Server settings
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    
    # Component settings
    finops: FinOpsSettings = Field(default_factory=FinOpsSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    
    # Computed properties
    @property
    def database_url(self) -> str:
        """Get database URL."""
        return self.database.url
    
    @property
    def async_database_url(self) -> str:
        """Get async database URL."""
        return self.database.async_url
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        return self.redis.url
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins."""
        return self.security.cors_origins
    
    @property
    def workers(self) -> int:
        """Get number of workers (production only)."""
        if self.environment == Environment.PRODUCTION:
            return self.performance.workers
        return 1
    
    @validator("environment", pre=True)
    def validate_environment(cls, v: str) -> Environment:
        """Validate and convert environment string."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow environment variables to override nested settings
        env_nested_delimiter = "__"
        
        # Example: DATABASE__HOST=localhost sets database.host
        # Example: FINOPS__COST_OPTIMIZATION_ENABLED=false sets finops.cost_optimization_enabled


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Uses LRU cache to ensure settings are loaded only once per process.
    This is safe because settings don't change during runtime.
    
    Returns:
        Settings: Application configuration
    """
    return Settings()


def get_test_settings() -> Settings:
    """
    Get test-specific settings.
    
    Returns settings configured for testing environment with
    in-memory databases and disabled external services.
    
    Returns:
        Settings: Test configuration
    """
    return Settings(
        environment=Environment.TESTING,
        debug=True,
        database=DatabaseSettings(
            name="finops_teste_test",
            host="localhost",
            port=5432
        ),
        redis=RedisSettings(
            db=1  # Use different Redis DB for tests
        ),
        monitoring=MonitoringSettings(
            metrics_enabled=False,
            tracing_enabled=False,
            alerting_enabled=False
        )
    )