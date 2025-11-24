"""
Unit tests for AWS infrastructure clients.
Tests AWS clients with mocked boto3 dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from src.domain.entities import ResourceType, AWSResource


class TestAWSClientCostExplorer:
    """Tests for AWS Cost Explorer client interactions."""
    
    @patch('boto3.client')
    def test_cost_explorer_get_cost_and_usage(self, mock_boto_client):
        """Test Cost Explorer get_cost_and_usage call."""
        mock_ce = Mock()
        mock_boto_client.return_value = mock_ce
        
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'TimePeriod': {
                        'Start': '2025-10-24',
                        'End': '2025-11-24'
                    },
                    'Groups': [
                        {
                            'Keys': ['Amazon Elastic Compute Cloud - Compute'],
                            'Metrics': {
                                'UnblendedCost': {'Amount': '1500.00', 'Unit': 'USD'}
                            }
                        },
                        {
                            'Keys': ['Amazon Simple Storage Service'],
                            'Metrics': {
                                'UnblendedCost': {'Amount': '300.00', 'Unit': 'USD'}
                            }
                        }
                    ],
                    'Total': {
                        'UnblendedCost': {'Amount': '1800.00', 'Unit': 'USD'}
                    }
                }
            ]
        }
        
        ce = mock_boto_client('ce')
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': '2025-10-24',
                'End': '2025-11-24'
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        assert 'ResultsByTime' in response
        assert len(response['ResultsByTime']) == 1
        assert len(response['ResultsByTime'][0]['Groups']) == 2
        
        total = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        assert total == '1800.00'
    
    @patch('boto3.client')
    def test_cost_explorer_handles_empty_results(self, mock_boto_client):
        """Test Cost Explorer handles empty results."""
        mock_ce = Mock()
        mock_boto_client.return_value = mock_ce
        
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': []
        }
        
        ce = mock_boto_client('ce')
        response = ce.get_cost_and_usage(
            TimePeriod={'Start': '2025-10-24', 'End': '2025-11-24'},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        assert response['ResultsByTime'] == []


class TestAWSClientEC2:
    """Tests for AWS EC2 client interactions."""
    
    @patch('boto3.client')
    def test_ec2_describe_instances(self, mock_boto_client):
        """Test EC2 describe_instances call."""
        mock_ec2 = Mock()
        mock_boto_client.return_value = mock_ec2
        
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3a.large',
                            'State': {'Name': 'running'},
                            'Tags': [
                                {'Key': 'Name', 'Value': 'WebServer'},
                                {'Key': 'Environment', 'Value': 'production'}
                            ]
                        },
                        {
                            'InstanceId': 'i-0987654321fedcba0',
                            'InstanceType': 't3a.medium',
                            'State': {'Name': 'stopped'},
                            'Tags': [
                                {'Key': 'Name', 'Value': 'DevServer'},
                                {'Key': 'Environment', 'Value': 'development'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        ec2 = mock_boto_client('ec2')
        response = ec2.describe_instances()
        
        assert 'Reservations' in response
        instances = response['Reservations'][0]['Instances']
        assert len(instances) == 2
        assert instances[0]['InstanceId'] == 'i-1234567890abcdef0'
        assert instances[0]['State']['Name'] == 'running'
    
    @patch('boto3.client')
    def test_ec2_describe_instances_with_filters(self, mock_boto_client):
        """Test EC2 describe_instances with filters."""
        mock_ec2 = Mock()
        mock_boto_client.return_value = mock_ec2
        
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-running123',
                            'State': {'Name': 'running'}
                        }
                    ]
                }
            ]
        }
        
        ec2 = mock_boto_client('ec2')
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        instances = response['Reservations'][0]['Instances']
        assert all(i['State']['Name'] == 'running' for i in instances)


class TestAWSClientCloudWatch:
    """Tests for AWS CloudWatch client interactions."""
    
    @patch('boto3.client')
    def test_cloudwatch_get_metric_statistics(self, mock_boto_client):
        """Test CloudWatch get_metric_statistics call."""
        mock_cw = Mock()
        mock_boto_client.return_value = mock_cw
        
        mock_cw.get_metric_statistics.return_value = {
            'Datapoints': [
                {
                    'Timestamp': datetime(2025, 11, 24, 12, 0),
                    'Average': 45.5,
                    'Maximum': 78.3,
                    'Minimum': 12.1
                },
                {
                    'Timestamp': datetime(2025, 11, 24, 13, 0),
                    'Average': 52.3,
                    'Maximum': 85.0,
                    'Minimum': 15.2
                }
            ]
        }
        
        cw = mock_boto_client('cloudwatch')
        response = cw.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}
            ],
            StartTime=datetime(2025, 11, 23, 12, 0),
            EndTime=datetime(2025, 11, 24, 12, 0),
            Period=3600,
            Statistics=['Average', 'Maximum', 'Minimum']
        )
        
        assert 'Datapoints' in response
        assert len(response['Datapoints']) == 2
        assert response['Datapoints'][0]['Average'] == 45.5
    
    @patch('boto3.client')
    def test_cloudwatch_empty_metrics(self, mock_boto_client):
        """Test CloudWatch handles empty metrics."""
        mock_cw = Mock()
        mock_boto_client.return_value = mock_cw
        
        mock_cw.get_metric_statistics.return_value = {
            'Datapoints': []
        }
        
        cw = mock_boto_client('cloudwatch')
        response = cw.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {'Name': 'InstanceId', 'Value': 'i-nonexistent'}
            ],
            StartTime=datetime(2025, 11, 23, 12, 0),
            EndTime=datetime(2025, 11, 24, 12, 0),
            Period=3600,
            Statistics=['Average']
        )
        
        assert response['Datapoints'] == []


class TestAWSClientRDS:
    """Tests for AWS RDS client interactions."""
    
    @patch('boto3.client')
    def test_rds_describe_db_instances(self, mock_boto_client):
        """Test RDS describe_db_instances call."""
        mock_rds = Mock()
        mock_boto_client.return_value = mock_rds
        
        mock_rds.describe_db_instances.return_value = {
            'DBInstances': [
                {
                    'DBInstanceIdentifier': 'production-db',
                    'DBInstanceClass': 'db.r5.large',
                    'Engine': 'postgres',
                    'DBInstanceStatus': 'available',
                    'AllocatedStorage': 100,
                    'MultiAZ': True
                }
            ]
        }
        
        rds = mock_boto_client('rds')
        response = rds.describe_db_instances()
        
        assert 'DBInstances' in response
        assert len(response['DBInstances']) == 1
        assert response['DBInstances'][0]['DBInstanceIdentifier'] == 'production-db'


class TestAWSClientS3:
    """Tests for AWS S3 client interactions."""
    
    @patch('boto3.client')
    def test_s3_list_buckets(self, mock_boto_client):
        """Test S3 list_buckets call."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        mock_s3.list_buckets.return_value = {
            'Buckets': [
                {
                    'Name': 'my-app-data',
                    'CreationDate': datetime(2025, 1, 1, 0, 0)
                },
                {
                    'Name': 'my-app-logs',
                    'CreationDate': datetime(2025, 2, 1, 0, 0)
                }
            ]
        }
        
        s3 = mock_boto_client('s3')
        response = s3.list_buckets()
        
        assert 'Buckets' in response
        assert len(response['Buckets']) == 2
    
    @patch('boto3.client')
    def test_s3_put_object(self, mock_boto_client):
        """Test S3 put_object for report storage."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        mock_s3.put_object.return_value = {
            'ETag': '"abc123"',
            'VersionId': 'v1'
        }
        
        s3 = mock_boto_client('s3')
        response = s3.put_object(
            Bucket='reports-bucket',
            Key='finops/report-2025-11-24.json',
            Body='{"total_savings": 1500}'
        )
        
        assert 'ETag' in response


class TestAWSClientErrorHandling:
    """Tests for AWS client error handling."""
    
    @patch('boto3.client')
    def test_handles_access_denied(self, mock_boto_client):
        """Test handling AccessDeniedException."""
        from botocore.exceptions import ClientError
        
        mock_ce = Mock()
        mock_boto_client.return_value = mock_ce
        
        mock_ce.get_cost_and_usage.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access Denied'}},
            'GetCostAndUsage'
        )
        
        ce = mock_boto_client('ce')
        
        with pytest.raises(ClientError) as exc_info:
            ce.get_cost_and_usage(
                TimePeriod={'Start': '2025-10-24', 'End': '2025-11-24'},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
        
        assert exc_info.value.response['Error']['Code'] == 'AccessDeniedException'
    
    @patch('boto3.client')
    def test_handles_throttling(self, mock_boto_client):
        """Test handling ThrottlingException."""
        from botocore.exceptions import ClientError
        
        mock_ec2 = Mock()
        mock_boto_client.return_value = mock_ec2
        
        call_count = 0
        def throttle_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ClientError(
                    {'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
                    'DescribeInstances'
                )
            return {'Reservations': []}
        
        mock_ec2.describe_instances.side_effect = throttle_then_succeed
        
        ec2 = mock_boto_client('ec2')
        
        result = None
        for attempt in range(3):
            try:
                result = ec2.describe_instances()
                break
            except ClientError:
                continue
        
        assert result is not None
        assert call_count == 3
