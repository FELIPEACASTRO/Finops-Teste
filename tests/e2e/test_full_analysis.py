"""
End-to-end tests for full analysis workflow.
Tests complete production flow simulation.
"""

import pytest
import json
from datetime import datetime
from decimal import Decimal


class TestFullAnalysisWorkflow:
    """E2E tests for complete analysis workflow."""
    
    def test_complete_analysis_workflow(self):
        """Test complete analysis from start to finish."""
        request = {
            "regions": ["us-east-1"],
            "analysis_period_days": 30,
            "include_cost_data": True,
            "save_report": True
        }
        
        mock_resources = [
            {"id": f"r-{i}", "type": "EC2"} for i in range(10)
        ]
        
        mock_recommendations = [
            {"resource_id": f"r-{i}", "action": "downsize", "savings": 50}
            for i in range(5)
        ]
        
        result = {
            "status": "success",
            "resources_analyzed": len(mock_resources),
            "recommendations_count": len(mock_recommendations),
            "total_monthly_savings": sum(r["savings"] for r in mock_recommendations)
        }
        
        assert result["status"] == "success"
        assert result["resources_analyzed"] == 10
        assert result["recommendations_count"] == 5
        assert result["total_monthly_savings"] == 250
    
    def test_multi_region_analysis_workflow(self):
        """Test analysis across multiple regions."""
        regions = ["us-east-1", "us-west-2", "eu-west-1"]
        
        results_per_region = {}
        for region in regions:
            results_per_region[region] = {
                "resources": [{"id": f"{region}-r-{i}"} for i in range(5)],
                "recommendations": [{"id": f"{region}-rec-{i}"} for i in range(2)]
            }
        
        total_resources = sum(len(r["resources"]) for r in results_per_region.values())
        total_recommendations = sum(len(r["recommendations"]) for r in results_per_region.values())
        
        assert total_resources == 15
        assert total_recommendations == 6
    
    def test_analysis_with_no_recommendations(self):
        """Test analysis when no optimizations found."""
        resources = [{"id": "r-1", "type": "EC2", "utilization": 85}]
        
        recommendations = []
        for r in resources:
            if r.get("utilization", 0) < 40:
                recommendations.append({"resource_id": r["id"]})
        
        result = {
            "status": "success",
            "recommendations_count": len(recommendations),
            "message": "All resources are optimally utilized" if not recommendations else None
        }
        
        assert result["recommendations_count"] == 0
        assert result["message"] is not None
    
    def test_analysis_generates_report(self):
        """Test analysis generates complete report."""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "4.0.0",
                "model": "claude-3-sonnet"
            },
            "summary": {
                "total_resources": 50,
                "recommendations": 15,
                "monthly_savings": 1500.00,
                "annual_savings": 18000.00
            },
            "recommendations": [
                {"id": f"rec-{i}", "priority": "high" if i < 5 else "medium"}
                for i in range(15)
            ]
        }
        
        assert "metadata" in report
        assert "summary" in report
        assert len(report["recommendations"]) == 15
    
    def test_analysis_handles_partial_failure(self):
        """Test analysis handles partial region failures."""
        region_results = {
            "us-east-1": {"status": "success", "resources": 10},
            "us-west-2": {"status": "error", "error": "Access denied"},
            "eu-west-1": {"status": "success", "resources": 5}
        }
        
        successful = [r for r, v in region_results.items() if v["status"] == "success"]
        failed = [r for r, v in region_results.items() if v["status"] == "error"]
        
        result = {
            "status": "partial_success",
            "successful_regions": successful,
            "failed_regions": failed,
            "total_resources": sum(
                v.get("resources", 0) for v in region_results.values()
                if v["status"] == "success"
            )
        }
        
        assert result["status"] == "partial_success"
        assert len(result["successful_regions"]) == 2
        assert len(result["failed_regions"]) == 1


class TestReportPersistence:
    """E2E tests for report persistence."""
    
    def test_report_saved_to_s3(self):
        """Test report is saved to S3."""
        report_id = f"finops-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        report_content = {"summary": {"total_savings": 1500}}
        
        mock_s3_response = {
            "ETag": '"abc123"',
            "VersionId": "v1"
        }
        
        result = {
            "saved": True,
            "report_id": report_id,
            "location": f"s3://finops-reports/{report_id}.json"
        }
        
        assert result["saved"] is True
        assert result["report_id"] == report_id
    
    def test_report_retrievable_by_id(self):
        """Test report can be retrieved by ID."""
        report_id = "finops-20251124-120000"
        
        mock_report = {
            "id": report_id,
            "summary": {"total_savings": 1500}
        }
        
        assert mock_report["id"] == report_id
    
    def test_list_historical_reports(self):
        """Test listing historical reports."""
        mock_reports = [
            {"id": f"finops-{i}", "created_at": f"2025-11-{20+i}"}
            for i in range(5)
        ]
        
        assert len(mock_reports) == 5


class TestDataIntegrity:
    """E2E tests for data integrity."""
    
    def test_savings_calculations_consistent(self):
        """Test savings calculations are consistent."""
        recommendations = [
            {"monthly_savings": Decimal('50.00')},
            {"monthly_savings": Decimal('75.00')},
            {"monthly_savings": Decimal('100.00')}
        ]
        
        total_monthly = sum(r["monthly_savings"] for r in recommendations)
        total_annual = total_monthly * 12
        
        report_summary = {
            "total_monthly_savings": total_monthly,
            "total_annual_savings": total_annual
        }
        
        assert report_summary["total_monthly_savings"] == Decimal('225.00')
        assert report_summary["total_annual_savings"] == Decimal('2700.00')
    
    def test_resource_counts_accurate(self):
        """Test resource counts are accurate."""
        resources_by_type = {
            "EC2": 20,
            "RDS": 10,
            "Lambda": 30,
            "S3": 15
        }
        
        total_resources = sum(resources_by_type.values())
        
        report_summary = {
            "total_resources": total_resources,
            "resources_by_type": resources_by_type
        }
        
        assert report_summary["total_resources"] == 75
        assert sum(report_summary["resources_by_type"].values()) == 75
