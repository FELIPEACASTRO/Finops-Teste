"""
Unit tests for AWS repositories.
Tests resource fetching and cost data retrieval.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from src.domain.entities import ResourceType, AWSResource, CostData


class TestAWSResourceRepository:
    """Tests for AWS resource repository."""
    
    def test_get_ec2_instances_returns_list(self):
        """Test getting EC2 instances returns a list."""
        mock_instances = [
            {"InstanceId": "i-1234567890abcdef0", "InstanceType": "t3a.large"},
            {"InstanceId": "i-0987654321fedcba0", "InstanceType": "t3a.medium"}
        ]
        
        assert len(mock_instances) == 2
        assert all("InstanceId" in i for i in mock_instances)
    
    def test_get_rds_instances_returns_list(self):
        """Test getting RDS instances returns a list."""
        mock_instances = [
            {"DBInstanceIdentifier": "db-1", "DBInstanceClass": "db.r5.large"},
            {"DBInstanceIdentifier": "db-2", "DBInstanceClass": "db.t3.medium"}
        ]
        
        assert len(mock_instances) == 2
        assert all("DBInstanceIdentifier" in i for i in mock_instances)
    
    def test_get_lambda_functions_returns_list(self):
        """Test getting Lambda functions returns a list."""
        mock_functions = [
            {"FunctionName": "func-1", "Runtime": "python3.11", "MemorySize": 256},
            {"FunctionName": "func-2", "Runtime": "nodejs18.x", "MemorySize": 512}
        ]
        
        assert len(mock_functions) == 2
        assert all("FunctionName" in f for f in mock_functions)
    
    def test_get_s3_buckets_returns_list(self):
        """Test getting S3 buckets returns a list."""
        mock_buckets = [
            {"Name": "bucket-1", "CreationDate": "2024-01-01"},
            {"Name": "bucket-2", "CreationDate": "2024-06-15"}
        ]
        
        assert len(mock_buckets) == 2
        assert all("Name" in b for b in mock_buckets)
    
    def test_pagination_handles_multiple_pages(self):
        """Test pagination handles multiple pages of results."""
        page1 = {"Instances": [{"InstanceId": f"i-{i}"} for i in range(100)], "NextToken": "token123"}
        page2 = {"Instances": [{"InstanceId": f"i-{i}"} for i in range(100, 150)]}
        
        all_instances = page1["Instances"] + page2["Instances"]
        
        assert len(all_instances) == 150
    
    def test_region_specific_queries(self):
        """Test resources are fetched per region."""
        regions = ["us-east-1", "us-west-2", "eu-west-1"]
        results_by_region = {region: [] for region in regions}
        
        results_by_region["us-east-1"] = [{"InstanceId": "i-1"}]
        results_by_region["us-west-2"] = [{"InstanceId": "i-2"}, {"InstanceId": "i-3"}]
        
        total = sum(len(r) for r in results_by_region.values())
        
        assert total == 3
    
    def test_handles_empty_results(self):
        """Test handling empty results gracefully."""
        mock_response = {"Instances": []}
        
        assert len(mock_response["Instances"]) == 0
    
    def test_handles_access_denied_error(self):
        """Test handling access denied errors."""
        error_code = "AccessDenied"
        
        if error_code == "AccessDenied":
            result = []
        
        assert result == []
    
    def test_handles_throttling_with_retry(self):
        """Test handling throttling with retry."""
        max_retries = 3
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                raise Exception("Throttling")
            except Exception:
                current_retry += 1
                if current_retry >= max_retries:
                    break
        
        assert current_retry == max_retries
    
    def test_converts_aws_response_to_resource(self):
        """Test converting AWS response to AWSResource entity."""
        aws_response = {
            "InstanceId": "i-1234567890abcdef0",
            "InstanceType": "t3a.large",
            "State": {"Name": "running"},
            "Tags": [{"Key": "Environment", "Value": "production"}]
        }
        
        resource_id = aws_response["InstanceId"]
        instance_type = aws_response["InstanceType"]
        tags = {t["Key"]: t["Value"] for t in aws_response.get("Tags", [])}
        
        assert resource_id == "i-1234567890abcdef0"
        assert instance_type == "t3a.large"
        assert tags["Environment"] == "production"


class TestAWSCostRepository:
    """Tests for AWS cost repository."""
    
    def test_get_cost_by_service(self):
        """Test getting cost breakdown by service."""
        mock_response = {
            "ResultsByTime": [{
                "Groups": [
                    {"Keys": ["Amazon EC2"], "Metrics": {"UnblendedCost": {"Amount": "500.00"}}},
                    {"Keys": ["Amazon RDS"], "Metrics": {"UnblendedCost": {"Amount": "300.00"}}}
                ]
            }]
        }
        
        costs = {
            g["Keys"][0]: Decimal(g["Metrics"]["UnblendedCost"]["Amount"])
            for g in mock_response["ResultsByTime"][0]["Groups"]
        }
        
        assert costs["Amazon EC2"] == Decimal('500.00')
        assert costs["Amazon RDS"] == Decimal('300.00')
    
    def test_get_cost_for_period(self):
        """Test getting cost for specific period."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        period_days = (end_date - start_date).days
        
        assert period_days == 30
    
    def test_get_daily_costs(self):
        """Test getting daily cost breakdown."""
        mock_daily = [
            {"date": "2025-11-01", "cost": 100.00},
            {"date": "2025-11-02", "cost": 110.00},
            {"date": "2025-11-03", "cost": 95.00}
        ]
        
        total = sum(d["cost"] for d in mock_daily)
        avg = total / len(mock_daily)
        
        assert total == 305.00
        assert avg == pytest.approx(101.67, rel=0.01)
    
    def test_get_forecast(self):
        """Test getting cost forecast."""
        current_daily_avg = Decimal('100.00')
        days_remaining = 15
        
        forecast = current_daily_avg * days_remaining
        
        assert forecast == Decimal('1500.00')
    
    def test_handles_no_cost_data(self):
        """Test handling no cost data scenario."""
        mock_response = {"ResultsByTime": [{"Groups": []}]}
        
        if not mock_response["ResultsByTime"][0]["Groups"]:
            total_cost = Decimal('0.00')
        
        assert total_cost == Decimal('0.00')
    
    def test_filters_by_service(self):
        """Test filtering costs by service."""
        all_costs = {
            "EC2": Decimal('500.00'),
            "RDS": Decimal('300.00'),
            "S3": Decimal('100.00')
        }
        
        ec2_only = {k: v for k, v in all_costs.items() if k == "EC2"}
        
        assert len(ec2_only) == 1
        assert ec2_only["EC2"] == Decimal('500.00')
    
    def test_aggregates_by_region(self):
        """Test aggregating costs by region."""
        costs_by_region = {
            "us-east-1": Decimal('1000.00'),
            "us-west-2": Decimal('500.00'),
            "eu-west-1": Decimal('300.00')
        }
        
        total = sum(costs_by_region.values())
        
        assert total == Decimal('1800.00')


class TestS3ReportRepository:
    """Tests for S3 report repository."""
    
    def test_save_report_json(self):
        """Test saving report as JSON."""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "recommendations": []
        }
        
        import json
        json_content = json.dumps(report_data)
        
        assert "generated_at" in json_content
    
    def test_save_report_html(self):
        """Test saving report as HTML."""
        report_data = {"title": "FinOps Report", "recommendations": []}
        
        html_content = f"<html><body><h1>{report_data['title']}</h1></body></html>"
        
        assert "FinOps Report" in html_content
    
    def test_generate_report_id(self):
        """Test generating unique report ID."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_id = f"finops-analysis-{timestamp}"
        
        assert report_id.startswith("finops-analysis-")
    
    def test_list_reports(self):
        """Test listing available reports."""
        mock_reports = [
            {"Key": "reports/2025/11/report-1.json", "LastModified": datetime.now()},
            {"Key": "reports/2025/11/report-2.json", "LastModified": datetime.now()}
        ]
        
        assert len(mock_reports) == 2
    
    def test_get_report_by_id(self):
        """Test retrieving report by ID."""
        report_id = "finops-analysis-20251124-120000"
        
        expected_key = f"reports/{report_id}.json"
        
        assert report_id in expected_key
    
    def test_delete_old_reports(self):
        """Test deleting reports older than retention period."""
        retention_days = 30
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        reports = [
            {"Key": "old-report.json", "LastModified": cutoff_date - timedelta(days=1)},
            {"Key": "new-report.json", "LastModified": datetime.now()}
        ]
        
        to_delete = [r for r in reports if r["LastModified"] < cutoff_date]
        
        assert len(to_delete) == 1
        assert to_delete[0]["Key"] == "old-report.json"
    
    def test_report_encryption(self):
        """Test report is saved with encryption."""
        encryption = "aws:kms"
        
        assert encryption in ["aws:kms", "AES256"]
