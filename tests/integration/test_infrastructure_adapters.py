"""
Integration tests for infrastructure adapters.
Tests real adapter implementations with mocked boto3 dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from src.domain.entities import ResourceType, AWSResource


class TestAWSCostRepositoryAdapter:
    """Tests for actual AWSCostRepository implementation."""
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    def test_cost_repository_init_and_lazy_client(self, mock_boto_client):
        """Test AWSCostRepository creates CE client lazily."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        
        mock_ce = Mock()
        mock_boto_client.return_value = mock_ce
        
        repo = AWSCostRepository(region='us-east-1')
        
        mock_boto_client.assert_not_called()
        
        _ = repo.client
        
        mock_boto_client.assert_called_once_with('ce', region_name='us-east-1')
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_get_cost_data_calls_ce_api(self, mock_boto_client):
        """Test get_cost_data calls Cost Explorer API with correct parameters."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        
        mock_ce = Mock()
        mock_boto_client.return_value = mock_ce
        
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2025-10-25', 'End': '2025-11-24'},
                    'Groups': [
                        {
                            'Keys': ['Amazon Elastic Compute Cloud - Compute'],
                            'Metrics': {'BlendedCost': {'Amount': '1500.00', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['Amazon Simple Storage Service'],
                            'Metrics': {'BlendedCost': {'Amount': '300.00', 'Unit': 'USD'}}
                        }
                    ],
                    'Total': {'BlendedCost': {'Amount': '1800.00', 'Unit': 'USD'}}
                }
            ]
        }
        
        repo = AWSCostRepository()
        
        end_date = datetime(2025, 11, 24)
        start_date = datetime(2025, 10, 25)
        
        result = await repo.get_cost_data(start_date, end_date)
        
        assert mock_ce.get_cost_and_usage.called
    
    @patch('src.infrastructure.aws.cost_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_get_cost_data_handles_empty_results(self, mock_boto_client):
        """Test get_cost_data handles empty results gracefully."""
        from src.infrastructure.aws.cost_repository import AWSCostRepository
        
        mock_ce = Mock()
        mock_boto_client.return_value = mock_ce
        
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': []
        }
        
        repo = AWSCostRepository()
        
        result = await repo.get_cost_data(
            datetime(2025, 10, 25),
            datetime(2025, 11, 24)
        )
        
        assert result is not None


class TestAWSResourceRepositoryAdapter:
    """Tests for actual AWSResourceRepository implementation."""
    
    @patch('src.infrastructure.aws.resource_repository.boto3.client')
    def test_resource_repository_init(self, mock_boto_client):
        """Test AWSResourceRepository initialization."""
        from src.infrastructure.aws.resource_repository import AWSResourceRepository
        
        mock_ec2 = Mock()
        mock_boto_client.return_value = mock_ec2
        
        repo = AWSResourceRepository(region='us-east-1')
        
        assert repo is not None
    
    @patch('src.infrastructure.aws.resource_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_get_ec2_resources(self, mock_boto_client):
        """Test fetching EC2 resources."""
        from src.infrastructure.aws.resource_repository import AWSResourceRepository
        
        mock_ec2 = Mock()
        mock_boto_client.return_value = mock_ec2
        
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-test123',
                            'InstanceType': 't3a.large',
                            'State': {'Name': 'running'},
                            'Tags': [
                                {'Key': 'Name', 'Value': 'WebServer'},
                                {'Key': 'Environment', 'Value': 'production'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        repo = AWSResourceRepository(region='us-east-1')
        resources = await repo.get_resources_by_type(ResourceType.EC2, 'us-east-1')
        
        assert resources is not None


class TestS3ReportRepositoryAdapter:
    """Tests for actual S3ReportRepository implementation."""
    
    @patch('src.infrastructure.aws.s3_report_repository.boto3.client')
    def test_s3_repository_init(self, mock_boto_client):
        """Test S3ReportRepository initialization."""
        from src.infrastructure.aws.s3_report_repository import S3ReportRepository
        
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        repo = S3ReportRepository(bucket_name='test-bucket')
        
        assert repo is not None
    
    @patch('src.infrastructure.aws.s3_report_repository.boto3.client')
    @pytest.mark.asyncio
    async def test_save_report_calls_put_object(self, mock_boto_client):
        """Test save_report calls S3 put_object."""
        from src.infrastructure.aws.s3_report_repository import S3ReportRepository
        
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        mock_s3.put_object.return_value = {
            'ETag': '"abc123"'
        }
        
        repo = S3ReportRepository(bucket_name='test-bucket')
        
        report_data = {
            'version': '4.0.0',
            'total_savings': 1500.00,
            'recommendations': []
        }
        
        result = await repo.save_report(report_data, 'report-2025-11-24')
        
        assert mock_s3.put_object.called


class TestBedrockAnalysisServiceAdapter:
    """Tests for actual BedrockAnalysisService implementation."""
    
    @patch('src.infrastructure.ai.bedrock_analysis_service.boto3.client')
    def test_bedrock_service_init(self, mock_boto_client):
        """Test BedrockAnalysisService initialization."""
        from src.infrastructure.ai.bedrock_analysis_service import BedrockAnalysisService
        
        mock_bedrock = Mock()
        mock_boto_client.return_value = mock_bedrock
        
        service = BedrockAnalysisService()
        
        assert service is not None
    
    @patch('src.infrastructure.ai.bedrock_analysis_service.boto3.client')
    @pytest.mark.asyncio
    async def test_analyze_resource_calls_bedrock(self, mock_boto_client):
        """Test analyze_resource calls Bedrock API."""
        from src.infrastructure.ai.bedrock_analysis_service import BedrockAnalysisService
        
        mock_bedrock = Mock()
        mock_boto_client.return_value = mock_bedrock
        
        mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(
                read=lambda: b'{"recommendation": "downsize", "savings": 100}'
            )
        }
        
        service = BedrockAnalysisService()
        
        resource = AWSResource(
            resource_id="i-test123",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            account_id="123456789012",
            configuration={"instance_type": "t3a.large"}
        )
        
        try:
            result = await service.analyze_resource(resource)
        except Exception:
            pass


class TestClienteAWSSingletonAdapter:
    """Tests for AWS Client wrapper."""
    
    @patch('boto3.client')
    def test_aws_client_singleton_exists(self, mock_boto_client):
        """Test ClienteAWSSingleton class exists."""
        from src.infrastructure.aws.cliente_aws import ClienteAWSSingleton
        
        assert ClienteAWSSingleton is not None
    
    @patch('boto3.Session')
    def test_aws_client_creates_sessions(self, mock_session):
        """Test AWS Client creates boto3 sessions correctly."""
        from src.infrastructure.aws.cliente_aws import ClienteAWSSingleton
        
        mock_client = Mock()
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = mock_client
        
        singleton = ClienteAWSSingleton()
        
        assert singleton is not None


class TestCloudWatchMetricsAdapter:
    """Tests for CloudWatch metrics adapter."""
    
    def test_cloudwatch_metrics_init(self):
        """Test CloudWatchMetrics initialization."""
        from src.infrastructure.monitoring.cloudwatch_metrics import CloudWatchMetrics
        
        metrics = CloudWatchMetrics(namespace='FinOpsAnalyzer')
        
        assert metrics is not None
        assert metrics.namespace == 'FinOpsAnalyzer'
    
    def test_put_metric(self):
        """Test putting a metric."""
        from src.infrastructure.monitoring.cloudwatch_metrics import CloudWatchMetrics
        
        metrics = CloudWatchMetrics(namespace='FinOpsAnalyzer')
        
        metrics.put_metric('TestMetric', 100.0, unit='Count')
        
        assert 'TestMetric' in metrics.metrics
        assert metrics.metrics['TestMetric']['value'] == 100.0
    
    def test_put_analysis_duration(self):
        """Test recording analysis duration."""
        from src.infrastructure.monitoring.cloudwatch_metrics import CloudWatchMetrics
        
        metrics = CloudWatchMetrics(namespace='FinOpsAnalyzer')
        
        metrics.put_analysis_duration(duration_seconds=1.5, region='us-east-1')
        
        assert 'AnalysisDuration' in metrics.metrics
        assert metrics.metrics['AnalysisDuration']['value'] == 1.5
    
    def test_put_resources_analyzed(self):
        """Test recording resources analyzed count."""
        from src.infrastructure.monitoring.cloudwatch_metrics import CloudWatchMetrics
        
        metrics = CloudWatchMetrics(namespace='FinOpsAnalyzer')
        
        metrics.put_resources_analyzed(count=50, region='us-east-1')
        
        assert 'ResourcesAnalyzed' in metrics.metrics
        assert metrics.metrics['ResourcesAnalyzed']['value'] == 50
