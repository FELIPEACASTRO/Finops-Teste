"""
Unit tests for domain services.
Tests business logic for analysis and reporting.
"""

import pytest
from decimal import Decimal
from src.domain.services.analysis_service import ResourceAnalyzer, ReportGenerator
from src.domain.entities import (
    AWSResource, ResourceType, UsagePattern, Priority, RiskLevel,
    OptimizationRecommendation, MetricDataPoint
)
from datetime import datetime


class TestResourceAnalyzer:
    """Tests for ResourceAnalyzer domain service."""
    
    def test_calculate_usage_pattern_idle(self):
        """Test detecting idle usage pattern."""
        analyzer = ResourceAnalyzer()
        resource = AWSResource(
            resource_id="i-test",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012"
        )
        
        pattern = analyzer.calculate_usage_pattern(resource)
        assert pattern in [UsagePattern.IDLE, UsagePattern.UNKNOWN]
    
    def test_calculate_priority_high(self):
        """Test high priority calculation."""
        analyzer = ResourceAnalyzer()
        priority = analyzer.calculate_priority(
            savings_percentage=40.0,
            monthly_savings=Decimal('150.00'),
            risk_level=RiskLevel.LOW
        )
        assert priority == Priority.HIGH
    
    def test_calculate_priority_medium(self):
        """Test medium priority calculation."""
        analyzer = ResourceAnalyzer()
        priority = analyzer.calculate_priority(
            savings_percentage=25.0,
            monthly_savings=Decimal('75.00'),
            risk_level=RiskLevel.MEDIUM
        )
        assert priority == Priority.MEDIUM
    
    def test_calculate_priority_low(self):
        """Test low priority calculation."""
        analyzer = ResourceAnalyzer()
        priority = analyzer.calculate_priority(
            savings_percentage=10.0,
            monthly_savings=Decimal('20.00'),
            risk_level=RiskLevel.HIGH
        )
        assert priority == Priority.LOW
    
    def test_calculate_risk_production_high_change(self):
        """Test high risk for production with large change."""
        analyzer = ResourceAnalyzer()
        resource = AWSResource(
            resource_id="i-prod",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "production"}
        )
        
        risk = analyzer.calculate_risk_level(resource, 60.0)
        assert risk == RiskLevel.HIGH
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        analyzer = ResourceAnalyzer()
        resource = AWSResource(
            resource_id="i-test",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012"
        )
        
        confidence = analyzer.calculate_confidence_score(resource, 720)
        assert 0 <= confidence <= 1.0


class TestReportGenerator:
    """Tests for ReportGenerator domain service."""
    
    def test_aggregate_savings(self):
        """Test aggregating savings from recommendations."""
        generator = ReportGenerator()
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-1", resource_type=ResourceType.EC2,
                current_config="t3.large", recommended_action="downsize",
                recommendation_details="details", reasoning="reasoning",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW, priority=Priority.HIGH
            ),
            OptimizationRecommendation(
                resource_id="i-2", resource_type=ResourceType.EC2,
                current_config="t3.medium", recommended_action="downsize",
                recommendation_details="details", reasoning="reasoning",
                monthly_savings_usd=Decimal('30.00'),
                annual_savings_usd=Decimal('360.00'),
                savings_percentage=20.0,
                risk_level=RiskLevel.LOW, priority=Priority.MEDIUM
            )
        ]
        
        savings = generator.aggregate_savings(recommendations)
        
        assert savings['monthly'] == Decimal('80.00')
        assert savings['annual'] == Decimal('960.00')
    
    def test_categorize_recommendations(self):
        """Test categorizing recommendations by priority."""
        generator = ReportGenerator()
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-1", resource_type=ResourceType.EC2,
                current_config="config", recommended_action="action",
                recommendation_details="details", reasoning="reasoning",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW, priority=Priority.HIGH
            ),
            OptimizationRecommendation(
                resource_id="i-2", resource_type=ResourceType.EC2,
                current_config="config", recommended_action="action",
                recommendation_details="details", reasoning="reasoning",
                monthly_savings_usd=Decimal('30.00'),
                annual_savings_usd=Decimal('360.00'),
                savings_percentage=20.0,
                risk_level=RiskLevel.LOW, priority=Priority.MEDIUM
            )
        ]
        
        categorized = generator.categorize_recommendations(recommendations)
        
        assert len(categorized[Priority.HIGH]) == 1
        assert len(categorized[Priority.MEDIUM]) == 1
        assert len(categorized[Priority.LOW]) == 0
    
    def test_generate_summary_statistics(self):
        """Test generating summary statistics."""
        generator = ReportGenerator()
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-1", resource_type=ResourceType.EC2,
                current_config="config", recommended_action="action",
                recommendation_details="details", reasoning="reasoning",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW, priority=Priority.HIGH
            )
        ]
        
        stats = generator.generate_summary_statistics(recommendations)
        
        assert stats['total_recommendations'] == 1
        assert stats['high_priority'] == 1
        assert stats['total_monthly_savings'] == 50.0
        assert stats['total_annual_savings'] == 600.0
    
    def test_generate_summary_statistics_empty(self):
        """Test generating summary statistics with empty recommendations."""
        generator = ReportGenerator()
        
        stats = generator.generate_summary_statistics([])
        
        assert stats['total_recommendations'] == 0
        assert stats['high_priority'] == 0
        assert stats['total_monthly_savings'] == 0.0
