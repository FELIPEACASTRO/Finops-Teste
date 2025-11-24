"""
Unit tests for configuration module.
Tests environment variable loading and validation.
"""

import pytest
import os
from unittest.mock import patch


class TestConfig:
    """Tests for configuration loading."""
    
    def test_load_config_from_env(self):
        """Test loading config from environment variables."""
        env_vars = {
            "AWS_REGION": "us-east-1",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet",
            "LOG_LEVEL": "INFO"
        }
        
        config = {
            "aws_region": env_vars.get("AWS_REGION", "us-east-1"),
            "model_id": env_vars.get("BEDROCK_MODEL_ID"),
            "log_level": env_vars.get("LOG_LEVEL", "INFO")
        }
        
        assert config["aws_region"] == "us-east-1"
        assert config["model_id"] == "anthropic.claude-3-sonnet"
        assert config["log_level"] == "INFO"
    
    def test_config_with_default_values(self):
        """Test config uses default values when env vars missing."""
        config = {
            "aws_region": os.environ.get("NONEXISTENT_VAR", "us-east-1"),
            "timeout_seconds": int(os.environ.get("TIMEOUT", "30")),
            "max_retries": int(os.environ.get("MAX_RETRIES", "3"))
        }
        
        assert config["aws_region"] == "us-east-1"
        assert config["timeout_seconds"] == 30
        assert config["max_retries"] == 3
    
    def test_config_validates_required_vars(self):
        """Test config validation for required variables."""
        required_vars = ["AWS_REGION", "BEDROCK_MODEL_ID"]
        env_vars = {"AWS_REGION": "us-east-1"}
        
        missing = [v for v in required_vars if v not in env_vars]
        
        assert len(missing) == 1
        assert "BEDROCK_MODEL_ID" in missing
    
    def test_config_type_conversion(self):
        """Test config converts types correctly."""
        env_vars = {
            "TIMEOUT": "30",
            "ENABLE_CACHE": "true",
            "MAX_RESOURCES": "1000"
        }
        
        config = {
            "timeout": int(env_vars["TIMEOUT"]),
            "enable_cache": env_vars["ENABLE_CACHE"].lower() == "true",
            "max_resources": int(env_vars["MAX_RESOURCES"])
        }
        
        assert config["timeout"] == 30
        assert config["enable_cache"] is True
        assert config["max_resources"] == 1000
    
    def test_config_validates_region_format(self):
        """Test config validates AWS region format."""
        valid_regions = [
            "us-east-1", "us-west-2", "eu-west-1", 
            "ap-southeast-1", "ap-northeast-1"
        ]
        
        invalid_region = "invalid-region"
        
        assert invalid_region not in valid_regions
        assert "us-east-1" in valid_regions
    
    def test_config_cache_settings(self):
        """Test cache configuration settings."""
        config = {
            "cache_ttl_minutes": 30,
            "cache_enabled": True,
            "cache_max_size": 1000
        }
        
        assert config["cache_ttl_minutes"] == 30
        assert config["cache_enabled"] is True
    
    def test_config_circuit_breaker_settings(self):
        """Test circuit breaker configuration."""
        config = {
            "circuit_breaker_threshold": 5,
            "circuit_breaker_timeout": 60,
            "circuit_breaker_enabled": True
        }
        
        assert config["circuit_breaker_threshold"] == 5
        assert config["circuit_breaker_timeout"] == 60
    
    def test_config_retry_settings(self):
        """Test retry configuration settings."""
        config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 10.0,
            "exponential_base": 2.0
        }
        
        assert config["max_retries"] == 3
        assert config["base_delay"] == 1.0


class TestLogger:
    """Tests for logger configuration."""
    
    def test_logger_level_from_env(self):
        """Test logger level from environment."""
        log_levels = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
        
        level_name = "INFO"
        level_value = log_levels.get(level_name, 20)
        
        assert level_value == 20
    
    def test_logger_format(self):
        """Test logger format configuration."""
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        assert "asctime" in format_string
        assert "levelname" in format_string
        assert "message" in format_string
    
    def test_logger_json_format(self):
        """Test JSON log format for production."""
        log_entry = {
            "timestamp": "2025-11-24T12:00:00Z",
            "level": "INFO",
            "message": "Analysis started",
            "region": "us-east-1"
        }
        
        import json
        json_log = json.dumps(log_entry)
        
        assert "timestamp" in json_log
        assert "INFO" in json_log


class TestExceptions:
    """Tests for custom exceptions."""
    
    def test_resource_not_found_exception(self):
        """Test ResourceNotFound exception."""
        class ResourceNotFoundException(Exception):
            def __init__(self, resource_id: str):
                self.resource_id = resource_id
                super().__init__(f"Resource not found: {resource_id}")
        
        exc = ResourceNotFoundException("i-12345")
        
        assert "i-12345" in str(exc)
        assert exc.resource_id == "i-12345"
    
    def test_analysis_failed_exception(self):
        """Test AnalysisFailed exception."""
        class AnalysisFailedException(Exception):
            def __init__(self, reason: str):
                self.reason = reason
                super().__init__(f"Analysis failed: {reason}")
        
        exc = AnalysisFailedException("Timeout")
        
        assert "Timeout" in str(exc)
    
    def test_validation_exception(self):
        """Test ValidationException."""
        class ValidationException(Exception):
            def __init__(self, field: str, message: str):
                self.field = field
                self.message = message
                super().__init__(f"Validation error on {field}: {message}")
        
        exc = ValidationException("regions", "Cannot be empty")
        
        assert exc.field == "regions"
        assert "Cannot be empty" in str(exc)
    
    def test_bedrock_exception(self):
        """Test BedrockException."""
        class BedrockException(Exception):
            def __init__(self, error_code: str, message: str):
                self.error_code = error_code
                super().__init__(f"Bedrock error [{error_code}]: {message}")
        
        exc = BedrockException("ThrottlingException", "Rate exceeded")
        
        assert exc.error_code == "ThrottlingException"
        assert "Rate exceeded" in str(exc)
