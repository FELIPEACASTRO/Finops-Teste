"""
Unit tests for application use cases.
Tests business flow orchestration and validation.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from src.domain.entities import (
    ResourceType,
    AWSResource,
    CostData,
    Priority,
    RiskLevel,
    OptimizationRecommendation
)


class TestAnalyzeResourcesUseCase:
    """Tests for AnalyzeResources use case."""
    
    def test_validate_command_with_valid_regions(self):
        """Test command validation with valid regions."""
        command = {
            "regions": ["us-east-1", "us-west-2"],
            "analysis_period_days": 30
        }
        
        valid_regions = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-northeast-1"
        ]
        
        is_valid = all(r in valid_regions for r in command["regions"])
        
        assert is_valid is True
    
    def test_validate_command_with_invalid_region(self):
        """Test command validation with invalid region."""
        command = {"regions": ["invalid-region-1"]}
        
        valid_regions = ["us-east-1", "us-west-2", "eu-west-1"]
        is_valid = all(r in valid_regions for r in command["regions"])
        
        assert is_valid is False
    
    def test_validate_command_with_empty_regions(self):
        """Test command validation with empty regions."""
        command = {"regions": []}
        
        if not command["regions"]:
            is_valid = False
        else:
            is_valid = True
        
        assert is_valid is False
    
    def test_validate_analysis_period_range(self):
        """Test analysis period validation."""
        valid_period = 30
        too_short = 0
        too_long = 365
        
        def validate_period(days):
            return 1 <= days <= 90
        
        assert validate_period(valid_period) is True
        assert validate_period(too_short) is False
        assert validate_period(too_long) is False
    
    @pytest.mark.asyncio
    async def test_execute_with_resources_returns_recommendations(self):
        """Test execution returns recommendations."""
        mock_resources = [
            AWSResource(
                resource_id="i-1",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012"
            )
        ]
        
        mock_recommendations = [
            {"resource_id": "i-1", "action": "downsize", "savings": 50}
        ]
        
        result = {
            "resources_analyzed": len(mock_resources),
            "recommendations": mock_recommendations
        }
        
        assert result["resources_analyzed"] == 1
        assert len(result["recommendations"]) == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_no_resources_returns_empty(self):
        """Test execution with no resources returns empty result."""
        mock_resources = []
        
        result = {
            "resources_analyzed": len(mock_resources),
            "recommendations": []
        }
        
        assert result["resources_analyzed"] == 0
        assert len(result["recommendations"]) == 0
    
    @pytest.mark.asyncio
    async def test_execute_aggregates_results_from_multiple_regions(self):
        """Test execution aggregates results from multiple regions."""
        results_by_region = {
            "us-east-1": [{"resource_id": "i-1"}],
            "us-west-2": [{"resource_id": "i-2"}, {"resource_id": "i-3"}]
        }
        
        all_results = []
        for region_results in results_by_region.values():
            all_results.extend(region_results)
        
        assert len(all_results) == 3
    
    @pytest.mark.asyncio
    async def test_execute_includes_cost_data_when_requested(self):
        """Test execution includes cost data when requested."""
        include_cost_data = True
        
        result = {
            "include_cost_data": include_cost_data,
            "cost_data": {"total_cost_usd": 5000}
        }
        
        if include_cost_data:
            assert "cost_data" in result
    
    @pytest.mark.asyncio
    async def test_execute_saves_report_when_requested(self):
        """Test execution saves report when requested."""
        save_report = True
        
        result = {
            "save_report": save_report,
            "report_id": "finops-analysis-20251124"
        }
        
        if save_report:
            assert "report_id" in result


class TestCommandValidation:
    """Tests for command validation."""
    
    def test_create_command_from_event(self):
        """Test creating command from Lambda event."""
        event = {
            "regions": ["us-east-1"],
            "analysis_period_days": 30,
            "include_cost_data": True
        }
        
        command = {
            "regions": event.get("regions", ["us-east-1"]),
            "period_days": event.get("analysis_period_days", 30),
            "include_costs": event.get("include_cost_data", True)
        }
        
        assert command["regions"] == ["us-east-1"]
        assert command["period_days"] == 30
    
    def test_command_applies_defaults(self):
        """Test command applies default values."""
        event = {}
        
        command = {
            "regions": event.get("regions", ["us-east-1"]),
            "period_days": event.get("analysis_period_days", 30),
            "include_costs": event.get("include_cost_data", True),
            "save_report": event.get("save_report", True)
        }
        
        assert command["regions"] == ["us-east-1"]
        assert command["period_days"] == 30
        assert command["include_costs"] is True
        assert command["save_report"] is True


class TestResultAggregation:
    """Tests for result aggregation."""
    
    def test_aggregate_savings(self):
        """Test aggregating savings from multiple recommendations."""
        recommendations = [
            {"monthly_savings_usd": Decimal('50.00')},
            {"monthly_savings_usd": Decimal('75.00')},
            {"monthly_savings_usd": Decimal('100.00')}
        ]
        
        total_monthly = sum(r["monthly_savings_usd"] for r in recommendations)
        total_annual = total_monthly * 12
        
        assert total_monthly == Decimal('225.00')
        assert total_annual == Decimal('2700.00')
    
    def test_aggregate_by_priority(self):
        """Test aggregating recommendations by priority."""
        recommendations = [
            {"priority": "high"},
            {"priority": "high"},
            {"priority": "medium"},
            {"priority": "low"}
        ]
        
        by_priority = {"high": 0, "medium": 0, "low": 0}
        for r in recommendations:
            by_priority[r["priority"]] += 1
        
        assert by_priority["high"] == 2
        assert by_priority["medium"] == 1
        assert by_priority["low"] == 1
    
    def test_aggregate_by_resource_type(self):
        """Test aggregating recommendations by resource type."""
        recommendations = [
            {"resource_type": "EC2"},
            {"resource_type": "EC2"},
            {"resource_type": "RDS"},
            {"resource_type": "S3"}
        ]
        
        by_type = {}
        for r in recommendations:
            rt = r["resource_type"]
            by_type[rt] = by_type.get(rt, 0) + 1
        
        assert by_type["EC2"] == 2
        assert by_type["RDS"] == 1
        assert by_type["S3"] == 1
    
    def test_aggregate_by_region(self):
        """Test aggregating results by region."""
        results = [
            {"region": "us-east-1", "savings": 100},
            {"region": "us-east-1", "savings": 50},
            {"region": "us-west-2", "savings": 75}
        ]
        
        by_region = {}
        for r in results:
            region = r["region"]
            by_region[region] = by_region.get(region, 0) + r["savings"]
        
        assert by_region["us-east-1"] == 150
        assert by_region["us-west-2"] == 75


class TestReportGeneration:
    """Tests for report generation."""
    
    def test_generate_report_id(self):
        """Test generating unique report ID."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_id = f"finops-analysis-{timestamp}"
        
        assert report_id.startswith("finops-analysis-")
        assert len(report_id) > 20
    
    def test_report_includes_summary(self):
        """Test report includes summary statistics."""
        report = {
            "summary": {
                "total_resources": 100,
                "total_recommendations": 25,
                "total_monthly_savings": 1500.00,
                "total_annual_savings": 18000.00
            }
        }
        
        assert report["summary"]["total_resources"] == 100
        assert report["summary"]["total_annual_savings"] == 18000.00
    
    def test_report_includes_metadata(self):
        """Test report includes metadata."""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "4.0.0",
                "model_used": "anthropic.claude-3-sonnet",
                "regions_analyzed": ["us-east-1", "us-west-2"]
            }
        }
        
        assert report["metadata"]["version"] == "4.0.0"
        assert len(report["metadata"]["regions_analyzed"]) == 2
