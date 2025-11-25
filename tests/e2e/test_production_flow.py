"""End-to-end production flow tests."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from decimal import Decimal

from src.application.use_cases.analyze_resources_use_case import (
    AnalyzeResourcesUseCase,
    AnalyzeResourcesCommand
)
from src.domain.entities import (
    AWSResource,
    ResourceType,
    OptimizationRecommendation,
    Priority,
    RiskLevel,
    UsagePattern,
    CostData,
    AnalysisReport
)
from src.infrastructure.cache.cost_cache import CostDataCache
from src.infrastructure.monitoring.cloudwatch_metrics import CloudWatchMetrics


class TestProductionFlow:
    """End-to-end tests simulating production flow."""
    
    @pytest.fixture
    def production_setup(self):
        """Set up production-like environment."""
        # Repositories
        resource_repo = Mock()
        cost_repo = Mock()
        report_repo = Mock()
        
        # Analysis service
        analysis_service = Mock()
        
        # Resilience components
        cache = CostDataCache(ttl_minutes=30)
        metrics = CloudWatchMetrics()
        
        # Mock resources
        resources = [
            AWSResource(
                resource_id="i-prod-001",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012",
                tags={"Environment": "production"},
                configuration={"instance_type": "t3a.xlarge", "state": "running"}
            ),
            AWSResource(
                resource_id="i-prod-002",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012",
                tags={"Environment": "production"},
                configuration={"instance_type": "t3a.large", "state": "running"}
            ),
            AWSResource(
                resource_id="db-prod-001",
                resource_type=ResourceType.RDS,
                region="us-east-1",
                account_id="123456789012",
                tags={"Environment": "production"},
                configuration={"db_instance_class": "db.m5.xlarge", "engine": "postgres"}
            )
        ]
        
        # Mock cost data
        cost_data = CostData(
            total_cost_usd=Decimal('5000.00'),
            period_days=30,
            cost_by_service={
                'EC2': Decimal('3000.00'),
                'RDS': Decimal('2000.00')
            }
        )
        
        # Mock recommendations
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-prod-001",
                resource_type=ResourceType.EC2,
                current_config="t3a.xlarge",
                recommended_action="downsize",
                recommendation_details="CPU 15% avg",
                reasoning="Significant headroom",
                monthly_savings_usd=Decimal('100.00'),
                annual_savings_usd=Decimal('1200.00'),
                savings_percentage=50.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH,
                confidence_score=0.95
            )
        ]
        
        resource_repo.get_all_resources = AsyncMock(return_value=resources)
        cost_repo.get_cost_data = AsyncMock(return_value=cost_data)
        report_repo.save_report = AsyncMock(return_value="s3://reports/report.json")
        analysis_service.analyze_resources = AsyncMock(return_value=recommendations)
        analysis_service.generate_report = AsyncMock(
            return_value=AnalysisReport(
                generated_at=datetime.utcnow(),
                version="4.0.0",
                model_used="claude-3",
                analysis_period_days=30,
                total_resources_analyzed=3,
                total_monthly_savings_usd=Decimal('100.00'),
                total_annual_savings_usd=Decimal('1200.00'),
                recommendations=recommendations
            )
        )
        
        return {
            'resource_repo': resource_repo,
            'cost_repo': cost_repo,
            'report_repo': report_repo,
            'analysis_service': analysis_service,
            'cache': cache,
            'metrics': metrics,
            'resources': resources,
            'cost_data': cost_data,
            'recommendations': recommendations
        }
    
    @pytest.mark.asyncio
    async def test_complete_production_flow(self, production_setup):
        """Test complete production workflow."""
        setup = production_setup
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=setup['resource_repo'],
            cost_repository=setup['cost_repo'],
            report_repository=setup['report_repo'],
            analysis_service=setup['analysis_service']
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is True
        assert result.report is not None
        assert result.report_location == "s3://reports/report.json"
        assert result.report.total_resources_analyzed == 3
        assert result.report.total_annual_savings_usd == Decimal('1200.00')
    
    @pytest.mark.asyncio
    async def test_production_flow_with_cache(self, production_setup):
        """Test production flow leveraging cache."""
        setup = production_setup
        cache = setup['cache']
        
        # Pre-populate cache
        cache.set("us-east-1-cost", setup['cost_data'])
        
        # Retrieve from cache (should not hit repository)
        cached = cache.get("us-east-1-cost")
        assert cached is not None
        assert cached.total_cost_usd == Decimal('5000.00')
        
        # Verify metrics
        metrics = setup['metrics']
        metrics.put_analysis_duration(2.5, "us-east-1")
        metrics.put_resources_analyzed(3, "us-east-1")
        metrics.put_recommendations_generated(1)
        metrics.put_total_savings(100.0, 1200.0)
        
        all_metrics = metrics.get_all_metrics()
        assert "AnalysisDuration" in all_metrics
        assert "ResourcesAnalyzed" in all_metrics
        assert "RecommendationsGenerated" in all_metrics
    
    @pytest.mark.asyncio
    async def test_production_flow_multi_region(self, production_setup):
        """Test production flow with multiple regions."""
        setup = production_setup
        
        # Mock multiple regions
        setup['resource_repo'].get_all_resources = AsyncMock(return_value=setup['resources'])
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=setup['resource_repo'],
            cost_repository=setup['cost_repo'],
            report_repository=setup['report_repo'],
            analysis_service=setup['analysis_service']
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1", "us-west-2", "eu-west-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is True
        # Called once per region
        assert setup['resource_repo'].get_all_resources.call_count == 3
    
    @pytest.mark.asyncio
    async def test_production_performance(self, production_setup):
        """Test production flow completes within SLA."""
        import time
        
        setup = production_setup
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=setup['resource_repo'],
            cost_repository=setup['cost_repo'],
            report_repository=setup['report_repo'],
            analysis_service=setup['analysis_service']
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        start = time.time()
        result = await use_case.execute(command)
        elapsed = time.time() - start
        
        # Should complete in < 5 seconds (with mocks)
        assert elapsed < 5.0
        assert result.success is True
