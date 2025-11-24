"""
Unit tests for domain services.
Tests actual production code implementations.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.domain.entities import (
    ResourceType,
    AWSResource,
    CostData,
    ResourceMetrics,
    MetricDataPoint,
    Priority,
    RiskLevel,
    UsagePattern,
    OptimizationRecommendation,
    AnalysisReport
)
from src.domain.services.analysis_service import ResourceAnalyzer


class TestResourceAnalyzer:
    """Tests for ResourceAnalyzer - actual implementation."""
    
    def test_create_resource_analyzer(self):
        """Test creating resource analyzer instance."""
        analyzer = ResourceAnalyzer()
        assert analyzer is not None
    
    def test_calculate_usage_pattern_idle(self):
        """Test calculating usage pattern for idle resource."""
        analyzer = ResourceAnalyzer()
        
        resource = AWSResource(
            resource_id="i-idle123",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012"
        )
        
        metrics = ResourceMetrics()
        timestamps = [datetime.utcnow() for _ in range(24)]
        metrics.cpu_utilization = [
            MetricDataPoint(timestamp=ts, value=2.0)
            for ts in timestamps
        ]
        resource.metrics = metrics
        
        pattern = analyzer.calculate_usage_pattern(resource)
        
        assert pattern == UsagePattern.IDLE
    
    def test_calculate_usage_pattern_steady(self):
        """Test calculating usage pattern for steady resource."""
        analyzer = ResourceAnalyzer()
        
        resource = AWSResource(
            resource_id="i-steady123",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012"
        )
        
        metrics = ResourceMetrics()
        timestamps = [datetime.utcnow() for _ in range(24)]
        metrics.cpu_utilization = [
            MetricDataPoint(timestamp=ts, value=50.0 + (i % 5))
            for i, ts in enumerate(timestamps)
        ]
        resource.metrics = metrics
        
        pattern = analyzer.calculate_usage_pattern(resource)
        
        assert pattern in [UsagePattern.STEADY, UsagePattern.VARIABLE, UsagePattern.UNKNOWN]
    
    def test_calculate_usage_pattern_unknown(self):
        """Test calculating usage pattern with no data."""
        analyzer = ResourceAnalyzer()
        
        resource = AWSResource(
            resource_id="i-nodata",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012"
        )
        
        resource.metrics = ResourceMetrics()
        
        pattern = analyzer.calculate_usage_pattern(resource)
        
        assert pattern == UsagePattern.UNKNOWN


class TestResourceMetricsStatistics:
    """Tests for ResourceMetrics - actual statistics methods."""
    
    def test_get_cpu_stats_calculates_correctly(self):
        """Test CPU statistics are calculated correctly."""
        metrics = ResourceMetrics()
        
        timestamps = [datetime.utcnow() for _ in range(100)]
        values = list(range(100))
        
        metrics.cpu_utilization = [
            MetricDataPoint(timestamp=ts, value=float(val))
            for ts, val in zip(timestamps, values)
        ]
        
        stats = metrics.get_cpu_stats()
        
        assert stats['mean'] == 49.5
        assert stats['p95'] == 95.0
        assert stats['p99'] == 99.0
        assert stats['max'] == 99.0
    
    def test_get_cpu_stats_empty_returns_zeros(self):
        """Test empty metrics return zero stats."""
        metrics = ResourceMetrics()
        
        stats = metrics.get_cpu_stats()
        
        assert stats['mean'] == 0.0
        assert stats['p95'] == 0.0
        assert stats['p99'] == 0.0
        assert stats['max'] == 0.0
    
    def test_get_cpu_stats_single_value(self):
        """Test single data point statistics."""
        metrics = ResourceMetrics()
        metrics.cpu_utilization = [
            MetricDataPoint(timestamp=datetime.utcnow(), value=50.0)
        ]
        
        stats = metrics.get_cpu_stats()
        
        assert stats['mean'] == 50.0
        assert stats['max'] == 50.0


class TestAWSResourceEntity:
    """Tests for AWSResource entity - actual methods."""
    
    def test_is_production_true(self):
        """Test is_production returns true for production tagged resources."""
        resource = AWSResource(
            resource_id="i-prod123",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "production"}
        )
        
        assert resource.is_production() is True
    
    def test_is_production_false(self):
        """Test is_production returns false for non-production resources."""
        resource = AWSResource(
            resource_id="i-dev123",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "development"}
        )
        
        assert resource.is_production() is False
    
    def test_is_production_with_prod_variant(self):
        """Test is_production handles 'prod' variant."""
        resource = AWSResource(
            resource_id="i-prod456",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "prod"}
        )
        
        assert resource.is_production() is True
    
    def test_get_tag_existing(self):
        """Test get_tag returns existing tag value."""
        resource = AWSResource(
            resource_id="i-tagged",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "production", "Team": "platform", "CostCenter": "CC001"}
        )
        
        assert resource.get_tag("Environment") == "production"
        assert resource.get_tag("Team") == "platform"
        assert resource.get_tag("CostCenter") == "CC001"
    
    def test_get_tag_missing(self):
        """Test get_tag returns empty string for missing tag."""
        resource = AWSResource(
            resource_id="i-notag",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012"
        )
        
        assert resource.get_tag("NonExistent") == ""
    
    def test_get_tag_missing_with_default(self):
        """Test get_tag returns default for missing tag."""
        resource = AWSResource(
            resource_id="i-default",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012"
        )
        
        assert resource.get_tag("NonExistent", "default-value") == "default-value"
    
    def test_get_criticality(self):
        """Test get_criticality returns criticality tag."""
        resource = AWSResource(
            resource_id="i-critical",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Criticality": "high"}
        )
        
        assert resource.get_criticality() == "high"
    
    def test_to_dict_serialization(self):
        """Test to_dict produces correct dictionary."""
        timestamp = datetime(2025, 11, 24, 12, 0, 0)
        
        resource = AWSResource(
            resource_id="i-serialized",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "test"},
            created_at=timestamp
        )
        
        result = resource.to_dict()
        
        assert result['resource_id'] == "i-serialized"
        assert result['resource_type'] == "EC2"
        assert result['region'] == "us-east-1"
        assert result['account_id'] == "123456789012"
        assert result['tags'] == {"Environment": "test"}
        assert result['created_at'] == timestamp.isoformat()


class TestCostDataEntity:
    """Tests for CostData entity - actual methods."""
    
    def test_get_top_services(self):
        """Test get_top_services returns sorted services."""
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30,
            cost_by_service={
                'EC2': Decimal('500.00'),
                'RDS': Decimal('200.00'),
                'S3': Decimal('150.00'),
                'Lambda': Decimal('100.00'),
                'CloudWatch': Decimal('50.00')
            }
        )
        
        top_3 = cost_data.get_top_services(limit=3)
        
        assert len(top_3) == 3
        assert top_3[0]['service'] == 'EC2'
        assert top_3[0]['cost_usd'] == 500.00
        assert top_3[0]['percentage'] == 50.0
        assert top_3[1]['service'] == 'RDS'
        assert top_3[2]['service'] == 'S3'
    
    def test_get_top_services_all(self):
        """Test get_top_services returns all when limit exceeds count."""
        cost_data = CostData(
            total_cost_usd=Decimal('300.00'),
            period_days=30,
            cost_by_service={
                'EC2': Decimal('200.00'),
                'S3': Decimal('100.00')
            }
        )
        
        top_10 = cost_data.get_top_services(limit=10)
        
        assert len(top_10) == 2
    
    def test_to_dict_serialization(self):
        """Test CostData to_dict produces correct output."""
        cost_data = CostData(
            total_cost_usd=Decimal('5000.00'),
            period_days=30,
            cost_by_service={'EC2': Decimal('3000.00'), 'RDS': Decimal('2000.00')}
        )
        
        result = cost_data.to_dict()
        
        assert result['total_cost_usd'] == 5000.00
        assert result['period_days'] == 30
        assert 'EC2' in result['cost_by_service']
        assert result['cost_by_service']['EC2'] == 3000.00


class TestOptimizationRecommendationEntity:
    """Tests for OptimizationRecommendation - actual validation."""
    
    def test_create_valid_recommendation(self):
        """Test creating valid recommendation."""
        rec = OptimizationRecommendation(
            resource_id="i-test",
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
        
        assert rec.resource_id == "i-test"
        assert rec.monthly_savings_usd == Decimal('50.00')
        assert rec.confidence_score == 0.85
    
    def test_negative_savings_raises_error(self):
        """Test negative savings raises ValueError."""
        with pytest.raises(ValueError, match="monthly_savings_usd cannot be negative"):
            OptimizationRecommendation(
                resource_id="i-invalid",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Test",
                reasoning="Test",
                monthly_savings_usd=Decimal('-50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            )
    
    def test_invalid_confidence_score_raises_error(self):
        """Test confidence score > 1 raises ValueError."""
        with pytest.raises(ValueError, match="confidence_score must be between 0 and 1"):
            OptimizationRecommendation(
                resource_id="i-invalid",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Test",
                reasoning="Test",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH,
                confidence_score=1.5
            )
    
    def test_invalid_savings_percentage_raises_error(self):
        """Test savings percentage > 100 raises ValueError."""
        with pytest.raises(ValueError, match="savings_percentage must be between 0 and 100"):
            OptimizationRecommendation(
                resource_id="i-invalid",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Test",
                reasoning="Test",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=150.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            )
    
    def test_to_dict_serialization(self):
        """Test recommendation to_dict serialization."""
        rec = OptimizationRecommendation(
            resource_id="i-test",
            resource_type=ResourceType.EC2,
            current_config="t3a.large",
            recommended_action="downsize",
            recommendation_details="Downsize to t3a.medium",
            reasoning="Low CPU",
            monthly_savings_usd=Decimal('50.00'),
            annual_savings_usd=Decimal('600.00'),
            savings_percentage=30.0,
            risk_level=RiskLevel.LOW,
            priority=Priority.HIGH,
            implementation_steps=["Step 1", "Step 2"],
            usage_pattern=UsagePattern.STEADY,
            confidence_score=0.85
        )
        
        result = rec.to_dict()
        
        assert result['resource_id'] == "i-test"
        assert result['resource_type'] == "EC2"
        assert result['monthly_savings_usd'] == 50.00
        assert result['risk_level'] == "low"
        assert result['priority'] == "high"
        assert result['implementation_steps'] == ["Step 1", "Step 2"]
        assert result['usage_pattern'] == "steady"
        assert result['confidence_score'] == 0.85


class TestAnalysisReportEntity:
    """Tests for AnalysisReport - actual methods."""
    
    def test_get_recommendations_by_priority(self):
        """Test filtering recommendations by priority."""
        recs = [
            OptimizationRecommendation(
                resource_id="i-high1",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Test",
                reasoning="Test",
                monthly_savings_usd=Decimal('100.00'),
                annual_savings_usd=Decimal('1200.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            ),
            OptimizationRecommendation(
                resource_id="i-medium1",
                resource_type=ResourceType.EC2,
                current_config="t3a.medium",
                recommended_action="downsize",
                recommendation_details="Test",
                reasoning="Test",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=20.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.MEDIUM
            )
        ]
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="claude-3-sonnet",
            analysis_period_days=30,
            total_resources_analyzed=2,
            total_monthly_savings_usd=Decimal('150.00'),
            total_annual_savings_usd=Decimal('1800.00'),
            recommendations=recs
        )
        
        high_priority = report.get_recommendations_by_priority(Priority.HIGH)
        medium_priority = report.get_recommendations_by_priority(Priority.MEDIUM)
        low_priority = report.get_recommendations_by_priority(Priority.LOW)
        
        assert len(high_priority) == 1
        assert len(medium_priority) == 1
        assert len(low_priority) == 0
        assert high_priority[0].resource_id == "i-high1"
    
    def test_priority_counts(self):
        """Test priority count methods."""
        recs = [
            OptimizationRecommendation(
                resource_id=f"i-{i}",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Test",
                reasoning="Test",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH if i < 2 else (Priority.MEDIUM if i < 3 else Priority.LOW)
            )
            for i in range(4)
        ]
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="test",
            analysis_period_days=30,
            total_resources_analyzed=4,
            total_monthly_savings_usd=Decimal('200.00'),
            total_annual_savings_usd=Decimal('2400.00'),
            recommendations=recs
        )
        
        assert report.get_high_priority_count() == 2
        assert report.get_medium_priority_count() == 1
        assert report.get_low_priority_count() == 1
