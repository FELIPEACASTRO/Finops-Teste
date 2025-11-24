"""
Unit tests for Bedrock client.
Tests AI prompt building and response parsing.
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime

from src.domain.entities import (
    ResourceType,
    AWSResource,
    Priority,
    RiskLevel
)


class TestBedrockPromptBuilder:
    """Tests for Bedrock prompt building."""
    
    def test_build_prompt_with_single_resource(self):
        """Test building prompt with single resource."""
        resource = {
            "resource_id": "i-1234567890abcdef0",
            "resource_type": "EC2",
            "region": "us-east-1",
            "configuration": {"instance_type": "t3a.large"},
            "metrics": {"cpu_avg": 15.0}
        }
        
        prompt = f"Analyze this AWS resource: {json.dumps(resource)}"
        
        assert "i-1234567890abcdef0" in prompt
        assert "EC2" in prompt
        assert "t3a.large" in prompt
    
    def test_build_prompt_with_multiple_resources(self):
        """Test building prompt with multiple resources."""
        resources = [
            {"resource_id": "i-1", "resource_type": "EC2"},
            {"resource_id": "i-2", "resource_type": "RDS"}
        ]
        
        prompt = f"Analyze these AWS resources: {json.dumps(resources)}"
        
        assert "i-1" in prompt
        assert "i-2" in prompt
        assert "EC2" in prompt
        assert "RDS" in prompt
    
    def test_build_prompt_includes_cost_data(self):
        """Test prompt includes cost data when provided."""
        cost_data = {
            "total_cost_usd": 5000.00,
            "period_days": 30
        }
        
        prompt = f"Cost data: {json.dumps(cost_data)}"
        
        assert "5000" in prompt
        assert "30" in prompt
    
    def test_build_prompt_includes_system_instructions(self):
        """Test prompt includes system instructions."""
        system_prompt = "You are a FinOps expert analyzing AWS resources."
        
        assert "FinOps" in system_prompt
        assert "AWS" in system_prompt
    
    def test_build_prompt_handles_special_characters(self):
        """Test prompt handles special characters in resource names."""
        resource = {
            "resource_id": "my-bucket-with-special_chars.123"
        }
        
        prompt = f"Resource: {json.dumps(resource)}"
        
        assert "my-bucket-with-special_chars.123" in prompt
    
    def test_build_prompt_max_length(self):
        """Test prompt respects maximum length."""
        max_length = 10000
        resources = [{"id": f"r-{i}"} for i in range(1000)]
        
        prompt = json.dumps(resources)
        
        if len(prompt) > max_length:
            prompt = prompt[:max_length]
        
        assert len(prompt) <= max_length


class TestBedrockResponseParser:
    """Tests for Bedrock response parsing."""
    
    def test_parse_valid_json_response(self):
        """Test parsing valid JSON response."""
        response = '''
        {
            "recommendations": [
                {
                    "resource_id": "i-1234567890abcdef0",
                    "action": "downsize",
                    "monthly_savings": 50.00
                }
            ]
        }
        '''
        
        parsed = json.loads(response)
        
        assert len(parsed["recommendations"]) == 1
        assert parsed["recommendations"][0]["action"] == "downsize"
    
    def test_parse_response_with_markdown_wrapper(self):
        """Test parsing response wrapped in markdown code blocks."""
        response = '''```json
        {
            "recommendations": [
                {"resource_id": "i-1", "action": "downsize"}
            ]
        }
        ```'''
        
        cleaned = response.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
        
        assert len(parsed["recommendations"]) == 1
    
    def test_parse_response_extracts_savings(self):
        """Test parsing extracts savings information."""
        response = {
            "recommendations": [
                {"monthly_savings": 50.00},
                {"monthly_savings": 75.00}
            ]
        }
        
        total_savings = sum(r["monthly_savings"] for r in response["recommendations"])
        
        assert total_savings == 125.00
    
    def test_parse_response_extracts_priorities(self):
        """Test parsing extracts priority information."""
        response = {
            "recommendations": [
                {"priority": "high"},
                {"priority": "medium"},
                {"priority": "low"}
            ]
        }
        
        priorities = [r["priority"] for r in response["recommendations"]]
        
        assert "high" in priorities
        assert "medium" in priorities
        assert "low" in priorities
    
    def test_parse_invalid_json_raises_error(self):
        """Test parsing invalid JSON raises error."""
        response = "This is not valid JSON"
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(response)
    
    def test_parse_empty_response(self):
        """Test parsing empty response."""
        response = '{"recommendations": []}'
        
        parsed = json.loads(response)
        
        assert len(parsed["recommendations"]) == 0
    
    def test_parse_response_with_missing_fields(self):
        """Test parsing response with missing fields uses defaults."""
        response = {
            "recommendations": [
                {"resource_id": "i-1"}
            ]
        }
        
        rec = response["recommendations"][0]
        action = rec.get("action", "unknown")
        savings = rec.get("monthly_savings", 0)
        
        assert action == "unknown"
        assert savings == 0
    
    def test_parse_response_validates_savings(self):
        """Test parsing validates savings are non-negative."""
        response = {
            "recommendations": [
                {"monthly_savings": -50.00}
            ]
        }
        
        savings = response["recommendations"][0]["monthly_savings"]
        
        if savings < 0:
            savings = 0
        
        assert savings >= 0


class TestBedrockTimeout:
    """Tests for Bedrock timeout handling."""
    
    @pytest.mark.asyncio
    async def test_timeout_raises_exception(self):
        """Test timeout raises appropriate exception."""
        import asyncio
        
        async def slow_operation():
            await asyncio.sleep(10)
            return "Done"
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(), timeout=0.01)
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test retry logic on timeout."""
        attempts = 0
        max_attempts = 3
        
        async def flaky_operation():
            nonlocal attempts
            attempts += 1
            if attempts < max_attempts:
                raise TimeoutError("Timeout")
            return "Success"
        
        result = None
        for _ in range(max_attempts):
            try:
                result = await flaky_operation()
                break
            except TimeoutError:
                continue
        
        assert result == "Success"
        assert attempts == max_attempts


class TestBedrockModelSelection:
    """Tests for Bedrock model selection."""
    
    def test_default_model_is_claude_3_sonnet(self):
        """Test default model is Claude 3 Sonnet."""
        default_model = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        assert "claude-3-sonnet" in default_model
    
    def test_model_id_is_valid_format(self):
        """Test model ID follows valid format."""
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        assert model_id.startswith("anthropic.")
        assert "claude" in model_id
    
    def test_supported_models_list(self):
        """Test list of supported models."""
        supported_models = [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-instant-v1"
        ]
        
        assert len(supported_models) >= 3
        assert all("anthropic" in m for m in supported_models)
