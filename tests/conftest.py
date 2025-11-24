"""
Shared test fixtures for AWS FinOps Analyzer v4.0
Provides reusable fixtures for all test layers.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any

from src.domain.entities import (
    ResourceType,
    UsagePattern,
    Priority,
    RiskLevel,
    MetricDataPoint,
    ResourceMetrics,
    AWSResource,
    CostData,
    OptimizationRecommendation,
    AnalysisReport
)


@pytest.fixture
def sample_timestamp():
    """Provide a consistent timestamp for tests."""
    return datetime(2025, 11, 24, 12, 0, 0)


@pytest.fixture
def sample_ec2_resource():
    """Create a sample EC2 resource."""
    return AWSResource(
        resource_id="i-1234567890abcdef0",
        resource_type=ResourceType.EC2,
        region="us-east-1",
        account_id="123456789012",
        tags={"Environment": "production", "Team": "backend"},
        configuration={"instance_type": "t3a.large", "state": "running"}
    )


@pytest.fixture
def sample_rds_resource():
    """Create a sample RDS resource."""
    return AWSResource(
        resource_id="db-instance-1",
        resource_type=ResourceType.RDS,
        region="us-west-2",
        account_id="123456789012",
        tags={"Environment": "development", "Team": "data"},
        configuration={"db_instance_class": "db.r5.xlarge", "engine": "postgres"}
    )


@pytest.fixture
def sample_lambda_resource():
    """Create a sample Lambda resource."""
    return AWSResource(
        resource_id="my-lambda-function",
        resource_type=ResourceType.LAMBDA,
        region="eu-west-1",
        account_id="123456789012",
        tags={"Environment": "staging"},
        configuration={"memory_size": 512, "runtime": "python3.11"}
    )


@pytest.fixture
def sample_s3_resource():
    """Create a sample S3 resource."""
    return AWSResource(
        resource_id="my-bucket",
        resource_type=ResourceType.S3,
        region="us-east-1",
        account_id="123456789012",
        tags={"Environment": "production", "DataClassification": "confidential"}
    )


@pytest.fixture
def sample_metrics_low_cpu():
    """Create metrics with low CPU utilization."""
    metrics = ResourceMetrics()
    timestamps = [datetime(2025, 11, 24, i, 0, 0) for i in range(24)]
    metrics.cpu_utilization = [
        MetricDataPoint(timestamp=ts, value=5.0 + (i % 3))
        for i, ts in enumerate(timestamps)
    ]
    return metrics


@pytest.fixture
def sample_metrics_high_cpu():
    """Create metrics with high CPU utilization."""
    metrics = ResourceMetrics()
    timestamps = [datetime(2025, 11, 24, i, 0, 0) for i in range(24)]
    metrics.cpu_utilization = [
        MetricDataPoint(timestamp=ts, value=75.0 + (i % 10))
        for i, ts in enumerate(timestamps)
    ]
    return metrics


@pytest.fixture
def sample_metrics_idle():
    """Create metrics for idle resource."""
    metrics = ResourceMetrics()
    timestamps = [datetime(2025, 11, 24, i, 0, 0) for i in range(24)]
    metrics.cpu_utilization = [
        MetricDataPoint(timestamp=ts, value=0.0)
        for ts in timestamps
    ]
    return metrics


@pytest.fixture
def sample_cost_data():
    """Create sample cost data."""
    return CostData(
        total_cost_usd=Decimal('5000.00'),
        period_days=30,
        cost_by_service={
            'EC2': Decimal('2000.00'),
            'RDS': Decimal('1500.00'),
            'S3': Decimal('800.00'),
            'Lambda': Decimal('400.00'),
            'CloudWatch': Decimal('300.00')
        }
    )


@pytest.fixture
def sample_recommendation_downsize():
    """Create a downsize recommendation."""
    return OptimizationRecommendation(
        resource_id="i-1234567890abcdef0",
        resource_type=ResourceType.EC2,
        current_config="t3a.large",
        recommended_action="downsize",
        recommendation_details="Downsize from t3a.large to t3a.medium",
        reasoning="Average CPU utilization is 15%, well below the 40% threshold",
        monthly_savings_usd=Decimal('50.00'),
        annual_savings_usd=Decimal('600.00'),
        savings_percentage=30.0,
        risk_level=RiskLevel.LOW,
        priority=Priority.HIGH,
        implementation_steps=[
            "Create AMI backup of current instance",
            "Launch new t3a.medium instance",
            "Migrate workload to new instance",
            "Terminate old instance"
        ],
        usage_pattern=UsagePattern.STEADY,
        confidence_score=0.85
    )


@pytest.fixture
def sample_recommendation_delete():
    """Create a delete recommendation."""
    return OptimizationRecommendation(
        resource_id="i-0987654321fedcba0",
        resource_type=ResourceType.EC2,
        current_config="t3a.medium",
        recommended_action="delete",
        recommendation_details="Delete idle EC2 instance",
        reasoning="Instance has been stopped for 30+ days with no activity",
        monthly_savings_usd=Decimal('75.00'),
        annual_savings_usd=Decimal('900.00'),
        savings_percentage=100.0,
        risk_level=RiskLevel.HIGH,
        priority=Priority.MEDIUM,
        implementation_steps=[
            "Verify instance is not needed",
            "Create final AMI backup",
            "Terminate instance",
            "Delete associated EBS volumes"
        ],
        usage_pattern=UsagePattern.IDLE,
        confidence_score=0.95
    )


@pytest.fixture
def sample_recommendation_reserved():
    """Create a reserved instances recommendation."""
    return OptimizationRecommendation(
        resource_id="i-abcdef1234567890",
        resource_type=ResourceType.EC2,
        current_config="On-Demand t3a.xlarge",
        recommended_action="purchase_reserved",
        recommendation_details="Purchase 1-year Reserved Instance",
        reasoning="Steady 24/7 workload pattern suitable for RI",
        monthly_savings_usd=Decimal('120.00'),
        annual_savings_usd=Decimal('1440.00'),
        savings_percentage=40.0,
        risk_level=RiskLevel.LOW,
        priority=Priority.HIGH,
        usage_pattern=UsagePattern.STEADY,
        confidence_score=0.90
    )


@pytest.fixture
def sample_recommendations_list(
    sample_recommendation_downsize,
    sample_recommendation_delete,
    sample_recommendation_reserved
):
    """Create a list of sample recommendations."""
    return [
        sample_recommendation_downsize,
        sample_recommendation_delete,
        sample_recommendation_reserved
    ]


@pytest.fixture
def sample_analysis_report(sample_recommendations_list, sample_cost_data, sample_timestamp):
    """Create a sample analysis report."""
    return AnalysisReport(
        generated_at=sample_timestamp,
        version="4.0.0",
        model_used="anthropic.claude-3-sonnet-20240229-v1:0",
        analysis_period_days=30,
        total_resources_analyzed=150,
        total_monthly_savings_usd=Decimal('245.00'),
        total_annual_savings_usd=Decimal('2940.00'),
        recommendations=sample_recommendations_list,
        cost_data=sample_cost_data
    )


@pytest.fixture
def sample_aws_regions():
    """Provide list of common AWS regions."""
    return [
        "us-east-1",
        "us-west-2",
        "eu-west-1",
        "ap-southeast-1",
        "ap-northeast-1"
    ]


@pytest.fixture
def mock_bedrock_response():
    """Provide mock Bedrock AI response."""
    return {
        "recommendations": [
            {
                "resource_id": "i-1234567890abcdef0",
                "resource_type": "EC2",
                "action": "downsize",
                "details": "Downsize to t3a.medium",
                "reasoning": "Low CPU utilization",
                "monthly_savings": 50.00,
                "risk": "low",
                "priority": "high"
            }
        ],
        "summary": {
            "total_resources": 10,
            "total_savings": 150.00
        }
    }


@pytest.fixture
def all_resource_types():
    """Provide all ResourceType enum values."""
    return [rt for rt in ResourceType if rt not in [ResourceType.GENERIC, ResourceType.UNKNOWN]]


@pytest.fixture
def compute_resource_types():
    """Provide compute ResourceType enum values."""
    return [
        ResourceType.EC2,
        ResourceType.LAMBDA,
        ResourceType.ECS,
        ResourceType.EKS,
        ResourceType.FARGATE,
        ResourceType.BATCH,
        ResourceType.LIGHTSAIL
    ]


@pytest.fixture
def storage_resource_types():
    """Provide storage ResourceType enum values."""
    return [
        ResourceType.S3,
        ResourceType.EBS,
        ResourceType.EFS,
        ResourceType.FSX,
        ResourceType.S3_GLACIER
    ]


@pytest.fixture
def database_resource_types():
    """Provide database ResourceType enum values."""
    return [
        ResourceType.RDS,
        ResourceType.AURORA,
        ResourceType.DYNAMODB,
        ResourceType.ELASTICACHE,
        ResourceType.REDSHIFT,
        ResourceType.DOCUMENTDB,
        ResourceType.NEPTUNE
    ]
