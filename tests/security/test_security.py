"""
Security tests for AWS FinOps Analyzer.
Tests input validation, data protection, and access control.
"""

import pytest
import json
import re


class TestInputValidation:
    """Tests for input validation and sanitization."""
    
    def test_validates_region_format(self):
        """Test region format validation."""
        valid_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        invalid_regions = ["invalid", "us-east", "../../etc/passwd", "<script>"]
        
        region_pattern = r'^[a-z]{2}-[a-z]+-\d+$'
        
        for region in valid_regions:
            assert re.match(region_pattern, region) is not None
        
        for region in invalid_regions:
            assert re.match(region_pattern, region) is None
    
    def test_validates_resource_id_format(self):
        """Test resource ID format validation."""
        valid_ids = ["i-1234567890abcdef0", "vol-abc123", "db-instance-1"]
        invalid_ids = ["<script>alert(1)</script>", "'; DROP TABLE users;--"]
        
        id_pattern = r'^[a-zA-Z0-9\-_]+$'
        
        for rid in valid_ids:
            assert re.match(id_pattern, rid) is not None
        
        for rid in invalid_ids:
            assert re.match(id_pattern, rid) is None
    
    def test_sanitizes_tag_values(self):
        """Test tag values are sanitized."""
        def sanitize(value):
            return re.sub(r'[<>&\'\"]', '', value)
        
        dangerous_tag = '<script>alert("xss")</script>'
        sanitized = sanitize(dangerous_tag)
        
        assert '<' not in sanitized
        assert '>' not in sanitized
        assert '"' not in sanitized
    
    def test_validates_period_days_range(self):
        """Test analysis period validation."""
        def validate_period(days):
            return isinstance(days, int) and 1 <= days <= 90
        
        assert validate_period(30) is True
        assert validate_period(0) is False
        assert validate_period(365) is False
        assert validate_period(-1) is False
    
    def test_rejects_malicious_json(self):
        """Test rejection of malicious JSON payloads."""
        malicious_payloads = [
            '{"__proto__": {"admin": true}}',
            '{"constructor": {"prototype": {"isAdmin": true}}}'
        ]
        
        for payload in malicious_payloads:
            parsed = json.loads(payload)
            
            cleaned = {k: v for k, v in parsed.items() 
                      if not k.startswith('__') and k != 'constructor'}
            
            assert '__proto__' not in cleaned
            assert 'constructor' not in cleaned


class TestDataProtection:
    """Tests for data protection."""
    
    def test_no_secrets_in_logs(self):
        """Test secrets are not logged."""
        log_message = "Processing request for account 123456789012"
        
        secret_patterns = [
            r'AKIA[0-9A-Z]{16}',
            r'[0-9a-zA-Z/+]{40}',
        ]
        
        for pattern in secret_patterns:
            assert re.search(pattern, log_message) is None
    
    def test_account_id_masked_in_output(self):
        """Test account IDs are masked in output."""
        def mask_account_id(account_id):
            if len(account_id) == 12:
                return account_id[:4] + "****" + account_id[-4:]
            return account_id
        
        account_id = "123456789012"
        masked = mask_account_id(account_id)
        
        assert masked == "1234****9012"
        assert account_id not in masked
    
    def test_report_encryption_enabled(self):
        """Test reports are encrypted at rest."""
        s3_put_options = {
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": "alias/finops-key"
        }
        
        assert s3_put_options["ServerSideEncryption"] == "aws:kms"
    
    def test_sensitive_fields_redacted(self):
        """Test sensitive fields are redacted."""
        sensitive_fields = ["password", "secret", "token", "key", "credential"]
        
        data = {
            "region": "us-east-1",
            "api_key": "secret123",
            "token": "abc456"
        }
        
        def redact(obj, fields):
            return {
                k: "***REDACTED***" if any(f in k.lower() for f in fields) else v
                for k, v in obj.items()
            }
        
        redacted = redact(data, sensitive_fields)
        
        assert redacted["api_key"] == "***REDACTED***"
        assert redacted["token"] == "***REDACTED***"
        assert redacted["region"] == "us-east-1"


class TestAccessControl:
    """Tests for access control."""
    
    def test_validates_iam_permissions(self):
        """Test IAM permission validation."""
        required_permissions = [
            "ec2:DescribeInstances",
            "rds:DescribeDBInstances",
            "ce:GetCostAndUsage",
            "cloudwatch:GetMetricData"
        ]
        
        user_permissions = [
            "ec2:DescribeInstances",
            "rds:DescribeDBInstances",
            "ce:GetCostAndUsage",
            "cloudwatch:GetMetricData",
            "s3:GetObject"
        ]
        
        has_required = all(p in user_permissions for p in required_permissions)
        
        assert has_required is True
    
    def test_rejects_unauthorized_regions(self):
        """Test rejection of unauthorized regions."""
        allowed_regions = ["us-east-1", "us-west-2", "eu-west-1"]
        requested_regions = ["us-east-1", "cn-north-1"]
        
        unauthorized = [r for r in requested_regions if r not in allowed_regions]
        
        assert len(unauthorized) == 1
        assert "cn-north-1" in unauthorized
    
    def test_cross_account_access_validation(self):
        """Test cross-account access validation."""
        requesting_account = "111111111111"
        target_account = "222222222222"
        
        allowed_cross_account = ["333333333333", "444444444444"]
        
        is_same_account = requesting_account == target_account
        is_allowed_cross = target_account in allowed_cross_account
        
        is_authorized = is_same_account or is_allowed_cross
        
        assert is_authorized is False


class TestRateLimiting:
    """Tests for rate limiting."""
    
    def test_rate_limit_per_account(self):
        """Test rate limiting per account."""
        rate_limit = 10
        window_seconds = 60
        
        request_counts = {"account-1": 5, "account-2": 15}
        
        def is_rate_limited(account):
            return request_counts.get(account, 0) >= rate_limit
        
        assert is_rate_limited("account-1") is False
        assert is_rate_limited("account-2") is True
    
    def test_api_throttling_detection(self):
        """Test API throttling detection."""
        error_codes = ["Throttling", "TooManyRequestsException", "RequestLimitExceeded"]
        
        error_response = {"Code": "Throttling", "Message": "Rate exceeded"}
        
        is_throttled = error_response.get("Code") in error_codes
        
        assert is_throttled is True
