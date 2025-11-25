"""
Configuration management following the Singleton pattern.
Centralizes all application configuration.
"""

import os
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Config:
    """
    Application configuration class.
    
    Follows the Singleton pattern to ensure consistent configuration
    across the application. Uses environment variables with sensible defaults.
    """
    
    # AWS Configuration
    aws_region: str = os.getenv('AWS_REGION', 'us-east-1')
    
    # S3 Configuration
    s3_bucket_name: str = os.getenv('S3_BUCKET_NAME', 'finops-reports')
    
    # Bedrock Configuration
    bedrock_model_id: str = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    # Analysis Configuration
    historical_days: int = int(os.getenv('HISTORICAL_DAYS', '30'))
    batch_size: int = int(os.getenv('BATCH_SIZE', '10'))
    
    # Email Configuration
    email_from: Optional[str] = os.getenv('EMAIL_FROM')
    email_to: Optional[str] = os.getenv('EMAIL_TO')
    
    # Logging Configuration
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Performance Configuration
    max_concurrent_requests: int = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
    request_timeout_seconds: int = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '300'))
    
    # Feature Flags
    enable_cost_anomaly_detection: bool = os.getenv('ENABLE_COST_ANOMALY_DETECTION', 'false').lower() == 'true'
    enable_rightsizing_recommendations: bool = os.getenv('ENABLE_RIGHTSIZING_RECOMMENDATIONS', 'true').lower() == 'true'
    enable_detailed_metrics: bool = os.getenv('ENABLE_DETAILED_METRICS', 'true').lower() == 'true'
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if self.historical_days <= 0 or self.historical_days > 365:
            raise ValueError("HISTORICAL_DAYS must be between 1 and 365")
        
        if self.batch_size <= 0 or self.batch_size > 100:
            raise ValueError("BATCH_SIZE must be between 1 and 100")
        
        if not self.s3_bucket_name:
            raise ValueError("S3_BUCKET_NAME is required")
        
        if not self.bedrock_model_id:
            raise ValueError("BEDROCK_MODEL_ID is required")
        
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    
    def get_supported_regions(self) -> List[str]:
        """Get list of supported AWS regions."""
        return [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
            'ca-central-1', 'sa-east-1'
        ]
    
    def get_supported_resource_types(self) -> List[str]:
        """Get list of supported resource types."""
        return ['EC2', 'RDS', 'ELB', 'Lambda', 'EBS']
    
    def is_production_environment(self) -> bool:
        """Check if running in production environment."""
        env = os.getenv('ENVIRONMENT', 'development').lower()
        return env in ['production', 'prod']
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'aws_region': self.aws_region,
            's3_bucket_name': self.s3_bucket_name,
            'bedrock_model_id': self.bedrock_model_id,
            'historical_days': self.historical_days,
            'batch_size': self.batch_size,
            'email_from': self.email_from,
            'email_to': self.email_to,
            'log_level': self.log_level,
            'max_concurrent_requests': self.max_concurrent_requests,
            'request_timeout_seconds': self.request_timeout_seconds,
            'enable_cost_anomaly_detection': self.enable_cost_anomaly_detection,
            'enable_rightsizing_recommendations': self.enable_rightsizing_recommendations,
            'enable_detailed_metrics': self.enable_detailed_metrics,
            'supported_regions': self.get_supported_regions(),
            'supported_resource_types': self.get_supported_resource_types(),
            'is_production': self.is_production_environment()
        }


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get configuration instance (Singleton pattern).
    
    Returns:
        Config: Configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance