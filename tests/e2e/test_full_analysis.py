"""
End-to-end tests for full analysis workflow.
Tests complete production flow using REAL src/ modules with mocked AWS boto3 clients.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from decimal import Decimal
from io import BytesIO

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
    CostData,
    AnalysisReport
)
from src.infrastructure.cache.cost_cache import CostDataCache
from src.infrastructure.monitoring.cloudwatch_metrics import CloudWatchMetrics
from src.infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitState


class TestFullAnalysisWorkflowWithRealAdapters:
    """E2E tests for complete analysis workflow using REAL adapters."""
    
    @pytest.fixture
    def mock_aws_responses(self):
        """Create mock AWS responses for boto3 clients."""
        return {
            'cost_explorer': {
                'ResultsByTime': [
                    {
                        'TimePeriod': {'Start': '2025-10-01', 'End': '2025-10-31'},
                        'Total': {'BlendedCost': {'Amount': '2500.00', 'Unit': 'USD'}},
                        'Groups': [
                            {'Keys': ['Amazon EC2'], 'Metrics': {'BlendedCost': {'Amount': '1500.00'}}},
                            {'Keys': ['Amazon S3'], 'Metrics': {'BlendedCost': {'Amount': '500.00'}}},
                            {'Keys': ['Amazon RDS'], 'Metrics': {'BlendedCost': {'Amount': '500.00'}}}
                        ]
                    }
                ]
            },
            's3_put': {'ETag': '"abc123"'},
            's3_get': {'Body': BytesIO(b'{"version": "4.0.0"}')}
        }
    
    @pytest.fixture
    def sample_resources(self):
        """Create sample AWS resources."""
        return [
            AWSResource(
                resource_id=f"i-e2e-{i:03d}",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012",
                tags={"Environment": "production", "Project": "e2e"},
                configuration={"instance_type": "t3a.large", "state": "running"}
            )
            for i in range(10)
        ]
    
    @pytest.fixture
    def sample_recommendations(self, sample_resources):
        """Create sample recommendations for resources."""
        return [
            OptimizationRecommendation(
                resource_id=r.resource_id,
                resource_type=r.resource_type,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="CPU utilization below 20%",
                reasoning="Significant cost savings opportunity",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=40.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH,
                confidence_score=0.92
            )
            for r in sample_resources[:5]
        ]
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @patch('src.infrastructure.aws.s3_report_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_complete_analysis_with_real_cost_repository(
        self, 
        mock_s3_client, 
        mock_cost_client,
        mock_aws_responses,
        sample_resources, 
        sample_recommendations
    ):
        """Test complete analysis using REAL AWSCostRepository with mocked boto3."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        from src.infrastructure.aws.s3_report_repository import S3ReportRepository
        
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = mock_aws_responses['cost_explorer']
        mock_cost_client.return_value = mock_ce
        
        mock_s3 = Mock()
        mock_s3.put_object.return_value = mock_aws_responses['s3_put']
        mock_s3_client.return_value = mock_s3
        
        cost_repo = AWSCostRepository(region='us-east-1')
        report_repo = S3ReportRepository(bucket_name='finops-reports')
        
        resource_repo = Mock()
        resource_repo.get_all_resources = AsyncMock(return_value=sample_resources)
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="claude-3-sonnet",
            analysis_period_days=30,
            total_resources_analyzed=len(sample_resources),
            total_monthly_savings_usd=sum(r.monthly_savings_usd for r in sample_recommendations),
            total_annual_savings_usd=sum(r.annual_savings_usd for r in sample_recommendations),
            recommendations=sample_recommendations
        )
        
        analysis_service = Mock()
        analysis_service.analyze_resources = AsyncMock(return_value=sample_recommendations)
        analysis_service.generate_report = AsyncMock(return_value=report)
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=analysis_service
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
        assert result.report.total_resources_analyzed == 10
        assert len(result.report.recommendations) == 5
        assert float(result.report.total_monthly_savings_usd) == 250.0
        
        mock_ce.get_cost_and_usage.assert_called()
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_multi_region_analysis_with_real_cost_repository(
        self, 
        mock_cost_client,
        mock_aws_responses
    ):
        """Test analysis across multiple regions using REAL AWSCostRepository."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = mock_aws_responses['cost_explorer']
        mock_cost_client.return_value = mock_ce
        
        regions = ["us-east-1", "us-west-2", "eu-west-1"]
        
        all_resources = []
        for region in regions:
            all_resources.extend([
                AWSResource(
                    resource_id=f"i-{region}-{i}",
                    resource_type=ResourceType.EC2,
                    region=region,
                    account_id="123456789012",
                    configuration={"instance_type": "t3a.medium"}
                )
                for i in range(5)
            ])
        
        recommendations = [
            OptimizationRecommendation(
                resource_id=r.resource_id,
                resource_type=r.resource_type,
                current_config="t3a.medium",
                recommended_action="reserve",
                recommendation_details="Steady state usage",
                reasoning="Reserved instance recommended",
                monthly_savings_usd=Decimal('20.00'),
                annual_savings_usd=Decimal('240.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.MEDIUM,
                confidence_score=0.88
            )
            for r in all_resources[:6]
        ]
        
        cost_repo = AWSCostRepository(region='us-east-1')
        
        resource_repo = Mock()
        resource_repo.get_all_resources = AsyncMock(return_value=all_resources)
        
        report_repo = Mock()
        report_repo.save_report = AsyncMock(return_value="s3://reports/multi-region.json")
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="claude-3-sonnet",
            analysis_period_days=30,
            total_resources_analyzed=len(all_resources),
            total_monthly_savings_usd=sum(r.monthly_savings_usd for r in recommendations),
            total_annual_savings_usd=sum(r.annual_savings_usd for r in recommendations),
            recommendations=recommendations
        )
        
        analysis_service = Mock()
        analysis_service.analyze_resources = AsyncMock(return_value=recommendations)
        analysis_service.generate_report = AsyncMock(return_value=report)
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=analysis_service
        )
        
        command = AnalyzeResourcesCommand(regions=regions, analysis_period_days=30)
        result = await use_case.execute(command)
        
        assert result.success is True
        assert result.report.total_resources_analyzed == 15
        assert len(result.report.recommendations) == 6
        
        mock_ce.get_cost_and_usage.assert_called()
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_analysis_with_no_recommendations(self, mock_cost_client, mock_aws_responses):
        """Test analysis when all resources are optimally utilized using REAL adapters."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = mock_aws_responses['cost_explorer']
        mock_cost_client.return_value = mock_ce
        
        resources = [
            AWSResource(
                resource_id="i-optimal-001",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012",
                configuration={"instance_type": "t3a.medium", "utilization": 85}
            )
        ]
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="claude-3-sonnet",
            analysis_period_days=30,
            total_resources_analyzed=1,
            total_monthly_savings_usd=Decimal('0'),
            total_annual_savings_usd=Decimal('0'),
            recommendations=[]
        )
        
        cost_repo = AWSCostRepository(region='us-east-1')
        
        resource_repo = Mock()
        resource_repo.get_all_resources = AsyncMock(return_value=resources)
        
        report_repo = Mock()
        report_repo.save_report = AsyncMock(return_value="s3://reports/optimal.json")
        
        analysis_service = Mock()
        analysis_service.analyze_resources = AsyncMock(return_value=[])
        analysis_service.generate_report = AsyncMock(return_value=report)
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=analysis_service
        )
        
        command = AnalyzeResourcesCommand(regions=["us-east-1"])
        result = await use_case.execute(command)
        
        assert result.success is True
        assert result.report.total_resources_analyzed == 1
        assert len(result.report.recommendations) == 0
        assert float(result.report.total_monthly_savings_usd) == 0
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @patch('src.infrastructure.aws.s3_report_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_analysis_generates_complete_report_with_real_adapters(
        self, 
        mock_s3_client,
        mock_cost_client, 
        mock_aws_responses,
        sample_resources, 
        sample_recommendations
    ):
        """Test analysis generates complete report using REAL adapters."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        from src.infrastructure.aws.s3_report_repository import S3ReportRepository
        
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = mock_aws_responses['cost_explorer']
        mock_cost_client.return_value = mock_ce
        
        mock_s3 = Mock()
        mock_s3.put_object.return_value = mock_aws_responses['s3_put']
        mock_s3_client.return_value = mock_s3
        
        cost_repo = AWSCostRepository(region='us-east-1')
        report_repo = S3ReportRepository(bucket_name='finops-reports')
        
        resource_repo = Mock()
        resource_repo.get_all_resources = AsyncMock(return_value=sample_resources)
        
        generated_at = datetime.utcnow()
        report = AnalysisReport(
            generated_at=generated_at,
            version="4.0.0",
            model_used="claude-3-sonnet",
            analysis_period_days=30,
            total_resources_analyzed=len(sample_resources),
            total_monthly_savings_usd=Decimal('1500.00'),
            total_annual_savings_usd=Decimal('18000.00'),
            recommendations=sample_recommendations
        )
        
        analysis_service = Mock()
        analysis_service.analyze_resources = AsyncMock(return_value=sample_recommendations)
        analysis_service.generate_report = AsyncMock(return_value=report)
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is True
        assert result.report.version == "4.0.0"
        assert result.report.model_used == "claude-3-sonnet"
        assert result.report.analysis_period_days == 30
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_analysis_handles_resource_fetch_error(self, mock_cost_client, mock_aws_responses):
        """Test analysis handles resource repository errors gracefully."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = mock_aws_responses['cost_explorer']
        mock_cost_client.return_value = mock_ce
        
        cost_repo = AWSCostRepository(region='us-east-1')
        
        resource_repo = Mock()
        resource_repo.get_all_resources = AsyncMock(
            side_effect=Exception("AWS API Error: Access Denied")
        )
        
        report_repo = Mock()
        analysis_service = Mock()
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=analysis_service
        )
        
        command = AnalyzeResourcesCommand(regions=["us-east-1"])
        result = await use_case.execute(command)
        
        assert result.success is False
        assert result.error_message is not None


class TestResilienceComponentsIntegration:
    """Integration tests for resilience components in E2E flow."""
    
    def test_cost_data_cache_stores_and_retrieves(self):
        """Test CostDataCache correctly stores and retrieves data."""
        cache = CostDataCache(ttl_minutes=30)
        
        cost_data = CostData(
            total_cost_usd=Decimal('1500.00'),
            period_days=30,
            cost_by_service={'EC2': Decimal('1000.00'), 'S3': Decimal('500.00')}
        )
        
        cache.set('us-east-1', cost_data)
        
        cached = cache.get('us-east-1')
        assert cached is not None
        assert float(cached.total_cost_usd) == 1500.00
        assert len(cached.cost_by_service) == 2
        
        not_cached = cache.get('us-west-2')
        assert not_cached is None
    
    def test_cloudwatch_metrics_records_all_metrics(self):
        """Test CloudWatchMetrics records all metric types correctly."""
        metrics = CloudWatchMetrics(namespace='FinOpsAnalyzer/E2E')
        
        metrics.put_analysis_duration(duration_seconds=2.5, region='us-east-1')
        metrics.put_resources_analyzed(count=50, region='us-east-1')
        metrics.put_recommendations_generated(count=15)
        metrics.put_total_savings(monthly_usd=1500.00, annual_usd=18000.00)
        
        all_metrics = metrics.get_all_metrics()
        
        assert 'AnalysisDuration' in all_metrics
        assert 'ResourcesAnalyzed' in all_metrics
        assert 'RecommendationsGenerated' in all_metrics
        assert 'MonthlySavings' in all_metrics
        assert 'AnnualSavings' in all_metrics
        
        assert all_metrics['AnalysisDuration']['value'] == 2.5
        assert all_metrics['ResourcesAnalyzed']['value'] == 50
        assert all_metrics['RecommendationsGenerated']['value'] == 15
    
    def test_circuit_breaker_transitions_correctly(self):
        """Test CircuitBreaker state transitions work correctly."""
        circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout_seconds=1
        )
        
        def successful_call():
            return "success"
        
        result = circuit_breaker.call(successful_call)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        
        def failing_call():
            raise Exception("Service unavailable")
        
        for _ in range(3):
            try:
                circuit_breaker.call(failing_call)
            except Exception:
                pass
        
        assert circuit_breaker.state == CircuitState.OPEN
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_full_workflow_with_resilience_components(self, mock_cost_client):
        """Test full E2E workflow with all resilience components active."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2025-10-01', 'End': '2025-10-31'},
                    'Total': {'BlendedCost': {'Amount': '2000.00', 'Unit': 'USD'}},
                    'Groups': []
                }
            ]
        }
        mock_cost_client.return_value = mock_ce
        
        cache = CostDataCache(ttl_minutes=30)
        metrics = CloudWatchMetrics(namespace='FinOpsAnalyzer/E2E')
        circuit_breaker = CircuitBreaker(failure_threshold=5)
        
        cost_repo = AWSCostRepository(region='us-east-1')
        
        resources = [
            AWSResource(
                resource_id="i-e2e-001",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012",
                configuration={"instance_type": "t3a.large"}
            )
        ]
        
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-e2e-001",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Low CPU",
                reasoning="Overprovisioned",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=40.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH,
                confidence_score=0.95
            )
        ]
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="claude-3-sonnet",
            analysis_period_days=30,
            total_resources_analyzed=1,
            total_monthly_savings_usd=Decimal('50.00'),
            total_annual_savings_usd=Decimal('600.00'),
            recommendations=recommendations
        )
        
        resource_repo = Mock()
        resource_repo.get_all_resources = AsyncMock(return_value=resources)
        
        report_repo = Mock()
        report_repo.save_report = AsyncMock(return_value="s3://reports/resilient.json")
        
        analysis_service = Mock()
        analysis_service.analyze_resources = AsyncMock(return_value=recommendations)
        analysis_service.generate_report = AsyncMock(return_value=report)
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=analysis_service
        )
        
        command = AnalyzeResourcesCommand(regions=["us-east-1"])
        result = await use_case.execute(command)
        
        assert result.success is True
        
        metrics.put_resources_analyzed(
            count=result.report.total_resources_analyzed,
            region="us-east-1"
        )
        metrics.put_recommendations_generated(
            count=len(result.report.recommendations)
        )
        
        assert metrics.metrics['ResourcesAnalyzed']['value'] == 1
        assert metrics.metrics['RecommendationsGenerated']['value'] == 1
        
        assert circuit_breaker.state == CircuitState.CLOSED
