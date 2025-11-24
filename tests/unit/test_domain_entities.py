"""
Unit tests for domain entities.
Tests business logic and entity behavior in isolation.
"""

import pytest
from datetime import datetime
from decimal import Decimal

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


class TestMetricDataPoint:
    """Test MetricDataPoint entity."""
    
    def test_create_metric_data_point(self):
        """Test creating a metric data point."""
        timestamp = datetime.utcnow()
        value = 75.5
        
        point = MetricDataPoint(timestamp=timestamp, value=value)
        
        assert point.timestamp == timestamp
        assert point.value == value
    
    def test_to_dict(self):
        """Test converting metric data point to dictionary."""
        timestamp = datetime.utcnow()
        value = 75.5
        
        point = MetricDataPoint(timestamp=timestamp, value=value)
        result = point.to_dict()
        
        assert result['timestamp'] == timestamp.isoformat()
        assert result['value'] == 75.5


class TestResourceMetrics:
    """Test ResourceMetrics entity."""
    
    def test_create_empty_metrics(self):
        """Test creating empty resource metrics."""
        metrics = ResourceMetrics()
        
        assert len(metrics.cpu_utilization) == 0
        assert len(metrics.memory_utilization) == 0
        assert len(metrics.network_in) == 0
        assert len(metrics.network_out) == 0
        assert len(metrics.disk_read_ops) == 0
        assert len(metrics.disk_write_ops) == 0
        assert len(metrics.custom_metrics) == 0
    
    def test_get_cpu_stats_empty(self):
        """Test getting CPU stats with no data."""
        metrics = ResourceMetrics()
        stats = metrics.get_cpu_stats()
        
        assert stats['mean'] == 0.0
        assert stats['p95'] == 0.0
        assert stats['p99'] == 0.0
        assert stats['max'] == 0.0
    
    def test_get_cpu_stats_with_data(self):
        """Test getting CPU stats with data."""
        metrics = ResourceMetrics()
        
        # Add CPU utilization data
        timestamps = [datetime.utcnow() for _ in range(100)]
        values = list(range(100))  # 0 to 99
        
        metrics.cpu_utilization = [
            MetricDataPoint(timestamp=ts, value=val)
            for ts, val in zip(timestamps, values)
        ]
        
        stats = metrics.get_cpu_stats()
        
        assert stats['mean'] == 49.5  # Average of 0-99
        assert stats['p95'] == 95.0   # 95th percentile
        assert stats['p99'] == 99.0   # 99th percentile
        assert stats['max'] == 99.0   # Maximum value


class TestAWSResource:
    """Test AWSResource entity."""
    
    def test_create_valid_resource(self):
        """Test creating a valid AWS resource."""
        resource = AWSResource(
            resource_id="i-1234567890abcdef0",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012"
        )
        
        assert resource.resource_id == "i-1234567890abcdef0"
        assert resource.resource_type == ResourceType.EC2
        assert resource.region == "us-east-1"
        assert resource.account_id == "123456789012"
    
    def test_create_resource_with_invalid_data(self):
        """Test creating resource with invalid data raises ValueError."""
        with pytest.raises(ValueError, match="resource_id cannot be empty"):
            AWSResource(
                resource_id="",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012"
            )
        
        with pytest.raises(ValueError, match="region cannot be empty"):
            AWSResource(
                resource_id="i-1234567890abcdef0",
                resource_type=ResourceType.EC2,
                region="",
                account_id="123456789012"
            )
    
    def test_get_tag(self):
        """Test getting tag values."""
        resource = AWSResource(
            resource_id="i-1234567890abcdef0",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "production", "Team": "backend"}
        )
        
        assert resource.get_tag("Environment") == "production"
        assert resource.get_tag("Team") == "backend"
        assert resource.get_tag("NonExistent") == ""
        assert resource.get_tag("NonExistent", "default") == "default"
    
    def test_is_production(self):
        """Test production environment detection."""
        # Production resource
        prod_resource = AWSResource(
            resource_id="i-1234567890abcdef0",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "production"}
        )
        assert prod_resource.is_production() is True
        
        # Non-production resource
        dev_resource = AWSResource(
            resource_id="i-1234567890abcdef1",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "development"}
        )
        assert dev_resource.is_production() is False
    
    def test_get_criticality(self):
        """Test criticality level detection."""
        resource = AWSResource(
            resource_id="i-1234567890abcdef0",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Criticality": "high"}
        )
        
        assert resource.get_criticality() == "high"
    
    def test_to_dict(self):
        """Test converting resource to dictionary."""
        timestamp = datetime.utcnow()
        
        resource = AWSResource(
            resource_id="i-1234567890abcdef0",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "production"},
            created_at=timestamp
        )
        
        result = resource.to_dict()
        
        assert result['resource_id'] == "i-1234567890abcdef0"
        assert result['resource_type'] == "EC2"
        assert result['region'] == "us-east-1"
        assert result['account_id'] == "123456789012"
        assert result['tags'] == {"Environment": "production"}
        assert result['created_at'] == timestamp.isoformat()


class TestCostData:
    """Test CostData entity."""
    
    def test_create_cost_data(self):
        """Test creating cost data."""
        cost_data = CostData(
            total_cost_usd=Decimal('1234.56'),
            period_days=30,
            cost_by_service={'EC2': Decimal('800.00'), 'RDS': Decimal('434.56')}
        )
        
        assert cost_data.total_cost_usd == Decimal('1234.56')
        assert cost_data.period_days == 30
        assert cost_data.cost_by_service['EC2'] == Decimal('800.00')
    
    def test_get_top_services(self):
        """Test getting top services by cost."""
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30,
            cost_by_service={
                'EC2': Decimal('500.00'),
                'RDS': Decimal('300.00'),
                'S3': Decimal('100.00'),
                'Lambda': Decimal('50.00'),
                'CloudWatch': Decimal('50.00')
            }
        )
        
        top_services = cost_data.get_top_services(limit=3)
        
        assert len(top_services) == 3
        assert top_services[0]['service'] == 'EC2'
        assert top_services[0]['cost_usd'] == 500.00
        assert top_services[0]['percentage'] == 50.0
        assert top_services[1]['service'] == 'RDS'
        assert top_services[2]['service'] == 'S3'


class TestOptimizationRecommendation:
    """Test OptimizationRecommendation entity."""
    
    def test_create_valid_recommendation(self):
        """Test creating a valid optimization recommendation."""
        recommendation = OptimizationRecommendation(
            resource_id="i-1234567890abcdef0",
            resource_type=ResourceType.EC2,
            current_config="t3a.large",
            recommended_action="downsize",
            recommendation_details="Downsize to t3a.medium",
            reasoning="Low CPU utilization",
            monthly_savings_usd=Decimal('50.00'),
            annual_savings_usd=Decimal('600.00'),
            savings_percentage=30.0,
            risk_level=RiskLevel.LOW,
            priority=Priority.HIGH,
            usage_pattern=UsagePattern.STEADY,
            confidence_score=0.85
        )
        
        assert recommendation.resource_id == "i-1234567890abcdef0"
        assert recommendation.monthly_savings_usd == Decimal('50.00')
        assert recommendation.confidence_score == 0.85
    
    def test_create_recommendation_with_invalid_savings(self):
        """Test creating recommendation with invalid savings raises ValueError."""
        with pytest.raises(ValueError, match="monthly_savings_usd cannot be negative"):
            OptimizationRecommendation(
                resource_id="i-1234567890abcdef0",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Downsize to t3a.medium",
                reasoning="Low CPU utilization",
                monthly_savings_usd=Decimal('-50.00'),  # Invalid negative value
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            )
    
    def test_create_recommendation_with_invalid_confidence(self):
        """Test creating recommendation with invalid confidence score."""
        with pytest.raises(ValueError, match="confidence_score must be between 0 and 1"):
            OptimizationRecommendation(
                resource_id="i-1234567890abcdef0",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Downsize to t3a.medium",
                reasoning="Low CPU utilization",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH,
                confidence_score=1.5  # Invalid value > 1
            )
    
    def test_to_dict(self):
        """Test converting recommendation to dictionary."""
        recommendation = OptimizationRecommendation(
            resource_id="i-1234567890abcdef0",
            resource_type=ResourceType.EC2,
            current_config="t3a.large",
            recommended_action="downsize",
            recommendation_details="Downsize to t3a.medium",
            reasoning="Low CPU utilization",
            monthly_savings_usd=Decimal('50.00'),
            annual_savings_usd=Decimal('600.00'),
            savings_percentage=30.0,
            risk_level=RiskLevel.LOW,
            priority=Priority.HIGH,
            implementation_steps=["Step 1", "Step 2"],
            usage_pattern=UsagePattern.STEADY,
            confidence_score=0.85
        )
        
        result = recommendation.to_dict()
        
        assert result['resource_id'] == "i-1234567890abcdef0"
        assert result['resource_type'] == "EC2"
        assert result['monthly_savings_usd'] == 50.00
        assert result['risk_level'] == "low"
        assert result['priority'] == "high"
        assert result['usage_pattern'] == "steady"
        assert result['confidence_score'] == 0.85
        assert result['implementation_steps'] == ["Step 1", "Step 2"]


class TestAnalysisReport:
    """Test AnalysisReport entity."""
    
    def test_create_analysis_report(self):
        """Test creating an analysis report."""
        timestamp = datetime.utcnow()
        
        # Create sample recommendations
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-1234567890abcdef0",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Downsize to t3a.medium",
                reasoning="Low CPU utilization",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            ),
            OptimizationRecommendation(
                resource_id="i-0987654321fedcba0",
                resource_type=ResourceType.RDS,
                current_config="db.m5.large",
                recommended_action="downsize",
                recommendation_details="Downsize to db.t3.medium",
                reasoning="Low connection count",
                monthly_savings_usd=Decimal('100.00'),
                annual_savings_usd=Decimal('1200.00'),
                savings_percentage=40.0,
                risk_level=RiskLevel.MEDIUM,
                priority=Priority.MEDIUM
            )
        ]
        
        report = AnalysisReport(
            generated_at=timestamp,
            version="4.0.0",
            model_used="anthropic.claude-3-sonnet-20240229-v1:0",
            analysis_period_days=30,
            total_resources_analyzed=2,
            total_monthly_savings_usd=Decimal('150.00'),
            total_annual_savings_usd=Decimal('1800.00'),
            recommendations=recommendations
        )
        
        assert report.generated_at == timestamp
        assert report.version == "4.0.0"
        assert report.total_resources_analyzed == 2
        assert len(report.recommendations) == 2
    
    def test_get_recommendations_by_priority(self):
        """Test filtering recommendations by priority."""
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-1",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Downsize",
                reasoning="Low CPU",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            ),
            OptimizationRecommendation(
                resource_id="i-2",
                resource_type=ResourceType.EC2,
                current_config="t3a.medium",
                recommended_action="downsize",
                recommendation_details="Downsize",
                reasoning="Low CPU",
                monthly_savings_usd=Decimal('25.00'),
                annual_savings_usd=Decimal('300.00'),
                savings_percentage=20.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.MEDIUM
            )
        ]
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="test",
            analysis_period_days=30,
            total_resources_analyzed=2,
            total_monthly_savings_usd=Decimal('75.00'),
            total_annual_savings_usd=Decimal('900.00'),
            recommendations=recommendations
        )
        
        high_priority = report.get_recommendations_by_priority(Priority.HIGH)
        medium_priority = report.get_recommendations_by_priority(Priority.MEDIUM)
        low_priority = report.get_recommendations_by_priority(Priority.LOW)
        
        assert len(high_priority) == 1
        assert len(medium_priority) == 1
        assert len(low_priority) == 0
        assert high_priority[0].resource_id == "i-1"
        assert medium_priority[0].resource_id == "i-2"
    
    def test_priority_counts(self):
        """Test priority count methods."""
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-1",
                resource_type=ResourceType.EC2,
                current_config="config",
                recommended_action="action",
                recommendation_details="details",
                reasoning="reasoning",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            ),
            OptimizationRecommendation(
                resource_id="i-2",
                resource_type=ResourceType.EC2,
                current_config="config",
                recommended_action="action",
                recommendation_details="details",
                reasoning="reasoning",
                monthly_savings_usd=Decimal('25.00'),
                annual_savings_usd=Decimal('300.00'),
                savings_percentage=20.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            ),
            OptimizationRecommendation(
                resource_id="i-3",
                resource_type=ResourceType.EC2,
                current_config="config",
                recommended_action="action",
                recommendation_details="details",
                reasoning="reasoning",
                monthly_savings_usd=Decimal('10.00'),
                annual_savings_usd=Decimal('120.00'),
                savings_percentage=10.0,
                risk_level=RiskLevel.MEDIUM,
                priority=Priority.MEDIUM
            )
        ]
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="test",
            analysis_period_days=30,
            total_resources_analyzed=3,
            total_monthly_savings_usd=Decimal('85.00'),
            total_annual_savings_usd=Decimal('1020.00'),
            recommendations=recommendations
        )
        
        assert report.get_high_priority_count() == 2
        assert report.get_medium_priority_count() == 1
        assert report.get_low_priority_count() == 0
    
    def test_to_dict(self):
        """Test converting report to dictionary."""
        timestamp = datetime.utcnow()
        
        report = AnalysisReport(
            generated_at=timestamp,
            version="4.0.0",
            model_used="anthropic.claude-3-sonnet-20240229-v1:0",
            analysis_period_days=30,
            total_resources_analyzed=1,
            total_monthly_savings_usd=Decimal('50.00'),
            total_annual_savings_usd=Decimal('600.00'),
            recommendations=[]
        )
        
        result = report.to_dict()
        
        assert result['generated_at'] == timestamp.isoformat()
        assert result['version'] == "4.0.0"
        assert result['model_used'] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert result['analysis_period_days'] == 30
        assert result['total_resources_analyzed'] == 1
        assert result['total_monthly_savings_usd'] == 50.00
        assert result['total_annual_savings_usd'] == 600.00
        assert result['high_priority_actions'] == 0
        assert result['medium_priority_actions'] == 0
        assert result['low_priority_actions'] == 0
        assert result['recommendations'] == []