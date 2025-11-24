"""
End-to-end production pipeline tests.
These tests exercise the complete production flow using REAL infrastructure adapters
with boto3 mocked at the module level.
"""

import pytest
import json
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


class TestProductionPipelineWithRealAdapters:
    """E2E tests using real infrastructure adapters with mocked boto3."""
    
    @pytest.fixture
    def mock_boto3_clients(self):
        """Create mock boto3 clients for all AWS services."""
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2025-10-01', 'End': '2025-10-31'},
                    'Total': {'BlendedCost': {'Amount': '5000.00', 'Unit': 'USD'}},
                    'Groups': [
                        {'Keys': ['Amazon EC2'], 'Metrics': {'BlendedCost': {'Amount': '3000.00'}}},
                        {'Keys': ['Amazon RDS'], 'Metrics': {'BlendedCost': {'Amount': '2000.00'}}}
                    ]
                }
            ]
        }
        
        mock_ec2 = Mock()
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-prod-001',
                            'InstanceType': 't3a.xlarge',
                            'State': {'Name': 'running'},
                            'Tags': [
                                {'Key': 'Name', 'Value': 'WebServer'},
                                {'Key': 'Environment', 'Value': 'production'}
                            ]
                        },
                        {
                            'InstanceId': 'i-prod-002',
                            'InstanceType': 't3a.large',
                            'State': {'Name': 'running'},
                            'Tags': [
                                {'Key': 'Name', 'Value': 'APIServer'},
                                {'Key': 'Environment', 'Value': 'production'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        mock_s3 = Mock()
        mock_s3.put_object.return_value = {'ETag': '"abc123"'}
        mock_s3.get_object.return_value = {
            'Body': BytesIO(b'{"version": "4.0.0"}')
        }
        
        mock_cloudwatch = Mock()
        mock_cloudwatch.put_metric_data.return_value = {}
        
        return {
            'ce': mock_ce,
            'ec2': mock_ec2,
            's3': mock_s3,
            'cloudwatch': mock_cloudwatch
        }
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_cost_repository_in_production_flow(self, mock_boto_client, mock_boto3_clients):
        """Test AWSCostRepository adapter in full production flow."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        
        mock_boto_client.return_value = mock_boto3_clients['ce']
        
        repo = AWSCostRepository(region='us-east-1')
        
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 31)
        
        result = await repo.get_cost_data(start_date, end_date)
        
        assert result is not None
        assert isinstance(result, CostData)
        assert float(result.total_cost_usd) == 5000.0
        
        mock_boto3_clients['ce'].get_cost_and_usage.assert_called()
    
    @patch('src.infrastructure.aws.resource_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_resource_repository_in_production_flow(self, mock_boto_client, mock_boto3_clients):
        """Test AWSResourceRepository adapter in full production flow."""
        from src.infrastructure.aws.resource_repository import AWSResourceRepository
        
        mock_boto_client.return_value = mock_boto3_clients['ec2']
        
        repo = AWSResourceRepository(region='us-east-1')
        
        resources = await repo.get_resources_by_type(ResourceType.EC2, 'us-east-1')
        
        assert resources is not None
    
    @patch('src.infrastructure.aws.s3_report_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_s3_repository_in_production_flow(self, mock_boto_client, mock_boto3_clients):
        """Test S3ReportRepository adapter in full production flow."""
        from src.infrastructure.aws.s3_report_repository import S3ReportRepository
        
        mock_boto_client.return_value = mock_boto3_clients['s3']
        
        repo = S3ReportRepository(bucket_name='finops-reports-prod')
        
        report_data = {
            'version': '4.0.0',
            'generated_at': datetime.utcnow().isoformat(),
            'total_savings': 1500.00,
            'recommendations': [
                {'resource_id': 'i-prod-001', 'action': 'downsize'}
            ]
        }
        
        result = await repo.save_report(report_data, 'report-2025-10-31')
        
        assert result is not None
        mock_boto3_clients['s3'].put_object.assert_called()
    
    @patch('src.infrastructure.ai.bedrock_analysis_service.boto3.client')
    def test_bedrock_service_initialization(self, mock_boto_client, mock_boto3_clients):
        """Test BedrockAnalysisService adapter initialization."""
        from src.infrastructure.ai.bedrock_analysis_service import BedrockAnalysisService
        
        mock_bedrock = Mock()
        mock_boto_client.return_value = mock_bedrock
        
        service = BedrockAnalysisService()
        
        assert service is not None
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @patch('src.infrastructure.aws.resource_repository.boto3.client')
    @patch('src.infrastructure.aws.s3_report_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_full_pipeline_with_real_adapters(
        self, 
        mock_s3_client, 
        mock_resource_client, 
        mock_cost_client,
        mock_boto3_clients
    ):
        """Test complete pipeline using real adapters with mocked boto3."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        from src.infrastructure.aws.resource_repository import AWSResourceRepository
        from src.infrastructure.aws.s3_report_repository import S3ReportRepository
        
        mock_cost_client.return_value = mock_boto3_clients['ce']
        mock_resource_client.return_value = mock_boto3_clients['ec2']
        mock_s3_client.return_value = mock_boto3_clients['s3']
        
        cost_repo = AWSCostRepository(region='us-east-1')
        resource_repo = AWSResourceRepository(region='us-east-1')
        report_repo = S3ReportRepository(bucket_name='finops-reports')
        
        analysis_service = Mock()
        
        sample_recommendations = [
            OptimizationRecommendation(
                resource_id='i-prod-001',
                resource_type=ResourceType.EC2,
                current_config='t3a.xlarge',
                recommended_action='downsize',
                recommendation_details='CPU avg 15%',
                reasoning='Overprovisioned',
                monthly_savings_usd=Decimal('100.00'),
                annual_savings_usd=Decimal('1200.00'),
                savings_percentage=50.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH,
                confidence_score=0.95
            )
        ]
        
        sample_resources = [
            AWSResource(
                resource_id='i-prod-001',
                resource_type=ResourceType.EC2,
                region='us-east-1',
                account_id='123456789012',
                configuration={'instance_type': 't3a.xlarge'}
            )
        ]
        
        sample_report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version='4.0.0',
            model_used='claude-3-sonnet',
            analysis_period_days=30,
            total_resources_analyzed=1,
            total_monthly_savings_usd=Decimal('100.00'),
            total_annual_savings_usd=Decimal('1200.00'),
            recommendations=sample_recommendations
        )
        
        analysis_service.analyze_resources = AsyncMock(return_value=sample_recommendations)
        analysis_service.generate_report = AsyncMock(return_value=sample_report)
        
        resource_repo_mock = Mock()
        resource_repo_mock.get_all_resources = AsyncMock(return_value=sample_resources)
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo_mock,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=['us-east-1'],
            analysis_period_days=30,
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is True
        assert result.report is not None
        assert result.report.total_resources_analyzed == 1
        
        mock_boto3_clients['ce'].get_cost_and_usage.assert_called()


class TestProductionPipelineErrorHandling:
    """E2E tests for error handling in production pipeline."""
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_cost_repository_handles_api_error(self, mock_boto_client):
        """Test AWSCostRepository handles AWS API errors gracefully and returns empty data."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        from botocore.exceptions import ClientError
        
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access Denied'}},
            'GetCostAndUsage'
        )
        mock_boto_client.return_value = mock_ce
        
        repo = AWSCostRepository(region='us-east-1')
        
        result = await repo.get_cost_data(
            datetime(2025, 10, 1),
            datetime(2025, 10, 31)
        )
        
        assert result is not None
        assert float(result.total_cost_usd) == 0
    
    @patch('src.infrastructure.aws.s3_report_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_s3_repository_handles_bucket_not_found(self, mock_boto_client):
        """Test S3ReportRepository handles bucket errors."""
        from src.infrastructure.aws.s3_report_repository import S3ReportRepository
        from botocore.exceptions import ClientError
        
        mock_s3 = Mock()
        mock_s3.put_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
            'PutObject'
        )
        mock_boto_client.return_value = mock_s3
        
        repo = S3ReportRepository(bucket_name='nonexistent-bucket')
        
        with pytest.raises(ClientError):
            await repo.save_report({'test': 'data'}, 'report-001')


class TestProductionPipelineIntegration:
    """Integration tests for production pipeline components."""
    
    def test_cost_data_caching_in_pipeline(self):
        """Test CostDataCache integration in production pipeline."""
        from src.infrastructure.cache.cost_cache import CostDataCache
        
        cache = CostDataCache(ttl_minutes=30)
        
        cost_data = CostData(
            total_cost_usd=Decimal('5000.00'),
            period_days=30,
            cost_by_service={'EC2': Decimal('3000.00'), 'RDS': Decimal('2000.00')}
        )
        
        cache.set('us-east-1', cost_data)
        
        cached = cache.get('us-east-1')
        assert cached is not None
        assert float(cached.total_cost_usd) == 5000.0
        
        not_cached = cache.get('eu-west-1')
        assert not_cached is None
    
    def test_cloudwatch_metrics_in_pipeline(self):
        """Test CloudWatchMetrics integration in production pipeline."""
        from src.infrastructure.monitoring.cloudwatch_metrics import CloudWatchMetrics
        
        metrics = CloudWatchMetrics(namespace='FinOpsAnalyzer/Production')
        
        metrics.put_analysis_duration(duration_seconds=5.2, region='us-east-1')
        metrics.put_resources_analyzed(count=100, region='us-east-1')
        metrics.put_recommendations_generated(count=25)
        metrics.put_total_savings(monthly_usd=1500.00, annual_usd=18000.00)
        
        assert 'AnalysisDuration' in metrics.metrics
        assert metrics.metrics['AnalysisDuration']['value'] == 5.2
        assert metrics.metrics['ResourcesAnalyzed']['value'] == 100
        assert metrics.metrics['RecommendationsGenerated']['value'] == 25
        assert metrics.metrics['MonthlySavings']['value'] == 1500.00
    
    def test_circuit_breaker_in_pipeline(self):
        """Test CircuitBreaker integration in production pipeline."""
        from src.infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitState
        
        circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout_seconds=5
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
    
    def test_retry_mechanism_in_pipeline(self):
        """Test Retry mechanism integration in production pipeline."""
        from src.infrastructure.resilience.retry import retry_sync, RetryException
        
        call_count = 0
        
        @retry_sync(max_attempts=3, base_delay=0.01, max_delay=0.1, jitter=False)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = eventually_succeeds()
        assert result == "success"
        assert call_count == 3
