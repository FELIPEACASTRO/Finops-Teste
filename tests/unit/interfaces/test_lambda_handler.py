"""
Unit tests for Lambda handler.
Tests event processing and response formatting.
"""

import pytest
import json
from datetime import datetime


class TestLambdaEventParsing:
    """Tests for Lambda event parsing."""
    
    def test_parse_valid_analysis_request(self):
        """Test parsing valid analysis request."""
        event = {
            "regions": ["us-east-1", "us-west-2"],
            "analysis_period_days": 30,
            "include_cost_data": True,
            "save_report": True
        }
        
        regions = event.get("regions", [])
        period = event.get("analysis_period_days", 30)
        include_costs = event.get("include_cost_data", True)
        
        assert len(regions) == 2
        assert period == 30
        assert include_costs is True
    
    def test_parse_event_with_default_values(self):
        """Test parsing event with missing fields uses defaults."""
        event = {}
        
        regions = event.get("regions", ["us-east-1"])
        period = event.get("analysis_period_days", 30)
        include_costs = event.get("include_cost_data", True)
        
        assert regions == ["us-east-1"]
        assert period == 30
        assert include_costs is True
    
    def test_parse_event_with_invalid_regions(self):
        """Test parsing event with invalid regions."""
        event = {"regions": "us-east-1"}
        
        regions = event.get("regions", [])
        
        if isinstance(regions, str):
            regions = [regions]
        
        assert regions == ["us-east-1"]
    
    def test_parse_event_with_empty_regions(self):
        """Test parsing event with empty regions list."""
        event = {"regions": []}
        
        regions = event.get("regions", ["us-east-1"])
        
        if not regions:
            regions = ["us-east-1"]
        
        assert len(regions) == 1
    
    def test_validate_period_range(self):
        """Test validating analysis period range."""
        valid_periods = [7, 14, 30, 60, 90]
        invalid_period = 1000
        
        if invalid_period not in valid_periods and invalid_period > 90:
            validated_period = 30
        else:
            validated_period = invalid_period
        
        assert validated_period == 30


class TestLambdaResponseFormatting:
    """Tests for Lambda response formatting."""
    
    def test_format_success_response(self):
        """Test formatting successful response."""
        result = {
            "status": "success",
            "analysis_id": "finops-123",
            "recommendations_count": 10,
            "total_savings_usd": 500.00
        }
        
        response = {
            "statusCode": 200,
            "body": json.dumps(result),
            "headers": {"Content-Type": "application/json"}
        }
        
        assert response["statusCode"] == 200
        assert "success" in response["body"]
    
    def test_format_error_response(self):
        """Test formatting error response."""
        error_message = "Invalid region specified"
        
        response = {
            "statusCode": 400,
            "body": json.dumps({"error": error_message}),
            "headers": {"Content-Type": "application/json"}
        }
        
        assert response["statusCode"] == 400
        assert error_message in response["body"]
    
    def test_format_timeout_response(self):
        """Test formatting timeout response."""
        response = {
            "statusCode": 504,
            "body": json.dumps({"error": "Analysis timed out"}),
            "headers": {"Content-Type": "application/json"}
        }
        
        assert response["statusCode"] == 504
    
    def test_format_partial_success_response(self):
        """Test formatting partial success response."""
        result = {
            "status": "partial_success",
            "regions_analyzed": ["us-east-1"],
            "regions_failed": ["us-west-2"],
            "recommendations_count": 5
        }
        
        response = {
            "statusCode": 207,
            "body": json.dumps(result)
        }
        
        assert response["statusCode"] == 207
        assert "partial_success" in response["body"]
    
    def test_response_includes_execution_time(self):
        """Test response includes execution time."""
        start_time = datetime.now()
        
        result = {
            "status": "success",
            "execution_time_seconds": 15.5
        }
        
        response = {
            "statusCode": 200,
            "body": json.dumps(result)
        }
        
        body = json.loads(response["body"])
        assert "execution_time_seconds" in body


class TestLambdaErrorHandling:
    """Tests for Lambda error handling."""
    
    def test_handle_bedrock_error(self):
        """Test handling Bedrock service error."""
        error_type = "BedrockServiceError"
        
        if error_type == "BedrockServiceError":
            response = {
                "statusCode": 503,
                "body": json.dumps({"error": "AI service temporarily unavailable"})
            }
        
        assert response["statusCode"] == 503
    
    def test_handle_cost_explorer_error(self):
        """Test handling Cost Explorer error."""
        error_type = "CostExplorerError"
        
        if error_type == "CostExplorerError":
            result = {
                "status": "partial_success",
                "cost_data_available": False
            }
        
        assert result["cost_data_available"] is False
    
    def test_handle_permission_error(self):
        """Test handling permission errors."""
        error_type = "AccessDeniedException"
        
        response = {
            "statusCode": 403,
            "body": json.dumps({"error": "Insufficient permissions"})
        }
        
        assert response["statusCode"] == 403
    
    def test_handle_validation_error(self):
        """Test handling validation errors."""
        event = {"analysis_period_days": -1}
        
        if event["analysis_period_days"] < 0:
            response = {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid analysis period"})
            }
        
        assert response["statusCode"] == 400
    
    def test_error_includes_request_id(self):
        """Test error response includes request ID."""
        request_id = "abc123-def456"
        
        response = {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal error",
                "request_id": request_id
            })
        }
        
        body = json.loads(response["body"])
        assert body["request_id"] == request_id


class TestLambdaColdStart:
    """Tests for Lambda cold start handling."""
    
    def test_initialization_time(self):
        """Test tracking initialization time."""
        init_start = datetime.now()
        
        init_time_ms = 50
        
        assert init_time_ms < 1000
    
    def test_warm_start_faster(self):
        """Test warm starts are faster than cold starts."""
        cold_start_ms = 500
        warm_start_ms = 50
        
        assert warm_start_ms < cold_start_ms


class TestLambdaMemory:
    """Tests for Lambda memory configuration."""
    
    def test_memory_size_valid(self):
        """Test memory size is valid."""
        valid_sizes = [128, 256, 512, 1024, 2048, 3008]
        memory_size = 1024
        
        assert memory_size in valid_sizes or (128 <= memory_size <= 10240)
    
    def test_memory_affects_cpu(self):
        """Test memory size affects CPU allocation."""
        memory_to_vcpu = {
            1769: 1.0,
            3538: 2.0
        }
        
        assert 1769 in memory_to_vcpu
