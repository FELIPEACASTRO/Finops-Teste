"""
AWS implementation of resource repository.
Handles data collection from AWS services.
"""

import boto3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ...domain.entities import (
    AWSResource, 
    ResourceType, 
    ResourceMetrics, 
    MetricDataPoint
)
from ...domain.repositories.resource_repository import IResourceRepository


class AWSResourceRepository(IResourceRepository):
    """
    AWS implementation of resource repository.
    
    Follows the Adapter Pattern to adapt AWS APIs to domain interfaces.
    Implements the Repository Pattern for data access abstraction.
    """

    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.logger = logging.getLogger(__name__)
        
        # Initialize AWS clients (Singleton pattern for client reuse)
        self._clients = {}
        self._session = boto3.Session()

    def _get_client(self, service_name: str, region: str = None) -> Any:
        """
        Get AWS client with caching (Singleton pattern).
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        region = region or self.region
        client_key = f"{service_name}_{region}"
        
        if client_key not in self._clients:
            self._clients[client_key] = self._session.client(service_name, region_name=region)
        
        return self._clients[client_key]

    async def get_resources_by_type(self, resource_type: ResourceType, region: str) -> List[AWSResource]:
        """
        Get all resources of a specific type in a region.
        
        Time Complexity: O(n) where n is number of resources
        Space Complexity: O(n)
        """
        try:
            if resource_type == ResourceType.EC2:
                return await self._get_ec2_instances(region)
            elif resource_type == ResourceType.RDS:
                return await self._get_rds_instances(region)
            elif resource_type == ResourceType.ELB:
                return await self._get_load_balancers(region)
            elif resource_type == ResourceType.LAMBDA:
                return await self._get_lambda_functions(region)
            elif resource_type == ResourceType.EBS:
                return await self._get_ebs_volumes(region)
            else:
                self.logger.warning(f"Resource type {resource_type} not implemented")
                return []
        except Exception as e:
            self.logger.error(f"Failed to get {resource_type} resources in {region}: {str(e)}")
            return []

    async def get_resource_by_id(self, resource_id: str) -> Optional[AWSResource]:
        """Get a specific resource by ID."""
        # Implementation would depend on resource type detection
        # For now, return None
        return None

    async def get_resource_metrics(
        self, 
        resource_id: str, 
        resource_type: ResourceType,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific resource from CloudWatch.
        
        Time Complexity: O(m) where m is number of metric data points
        Space Complexity: O(m)
        """
        try:
            cloudwatch = self._get_client('cloudwatch')
            
            # Define metric configurations based on resource type
            metric_configs = self._get_metric_configs(resource_type, resource_id)
            
            metrics_data = {}
            
            for metric_name, config in metric_configs.items():
                response = cloudwatch.get_metric_statistics(
                    Namespace=config['namespace'],
                    MetricName=config['metric_name'],
                    Dimensions=config['dimensions'],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Average']
                )
                
                # Convert to MetricDataPoint objects
                data_points = [
                    MetricDataPoint(
                        timestamp=point['Timestamp'],
                        value=point['Average']
                    )
                    for point in response['Datapoints']
                ]
                
                # Sort by timestamp
                data_points.sort(key=lambda x: x.timestamp)
                metrics_data[metric_name] = data_points
            
            return metrics_data
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics for {resource_id}: {str(e)}")
            return {}

    async def get_all_resources(self, regions: List[str]) -> List[AWSResource]:
        """
        Get all resources across specified regions.
        
        Time Complexity: O(r * t * n) where r is regions, t is resource types, n is resources per type
        Space Complexity: O(r * n)
        """
        all_resources = []
        
        resource_types = [
            ResourceType.EC2,
            ResourceType.RDS,
            ResourceType.ELB,
            ResourceType.LAMBDA,
            ResourceType.EBS
        ]
        
        for region in regions:
            for resource_type in resource_types:
                try:
                    resources = await self.get_resources_by_type(resource_type, region)
                    all_resources.extend(resources)
                except Exception as e:
                    self.logger.error(f"Failed to get {resource_type} in {region}: {str(e)}")
                    continue
        
        return all_resources

    async def _get_ec2_instances(self, region: str) -> List[AWSResource]:
        """
        Get EC2 instances with their configuration and metrics.
        
        Time Complexity: O(n) where n is number of instances
        Space Complexity: O(n)
        """
        ec2 = self._get_client('ec2', region)
        
        try:
            response = ec2.describe_instances()
            resources = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Skip terminated instances
                    if instance['State']['Name'] == 'terminated':
                        continue
                    
                    # Extract tags
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    # Create configuration dict
                    configuration = {
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'launch_time': instance['LaunchTime'].isoformat(),
                        'availability_zone': instance['Placement']['AvailabilityZone'],
                        'vpc_id': instance.get('VpcId'),
                        'subnet_id': instance.get('SubnetId'),
                        'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                        'platform': instance.get('Platform', 'linux')
                    }
                    
                    # Get metrics for the last 30 days
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=30)
                    
                    metrics_data = await self.get_resource_metrics(
                        instance['InstanceId'],
                        ResourceType.EC2,
                        start_time,
                        end_time
                    )
                    
                    # Create ResourceMetrics object
                    metrics = ResourceMetrics(
                        cpu_utilization=metrics_data.get('cpu_utilization', []),
                        network_in=metrics_data.get('network_in', []),
                        network_out=metrics_data.get('network_out', [])
                    )
                    
                    # Create AWSResource
                    resource = AWSResource(
                        resource_id=instance['InstanceId'],
                        resource_type=ResourceType.EC2,
                        region=region,
                        account_id=self._extract_account_id(instance['InstanceId']),
                        tags=tags,
                        configuration=configuration,
                        metrics=metrics,
                        created_at=instance['LaunchTime'],
                        last_updated=datetime.utcnow()
                    )
                    
                    resources.append(resource)
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Failed to get EC2 instances in {region}: {str(e)}")
            return []

    async def _get_rds_instances(self, region: str) -> List[AWSResource]:
        """Get RDS instances."""
        rds = self._get_client('rds', region)
        
        try:
            response = rds.describe_db_instances()
            resources = []
            
            for db_instance in response['DBInstances']:
                # Skip deleted instances
                if db_instance['DBInstanceStatus'] == 'deleting':
                    continue
                
                # Extract tags
                tags_response = rds.list_tags_for_resource(
                    ResourceName=db_instance['DBInstanceArn']
                )
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}
                
                # Create configuration
                configuration = {
                    'db_instance_class': db_instance['DBInstanceClass'],
                    'engine': db_instance['Engine'],
                    'engine_version': db_instance['EngineVersion'],
                    'status': db_instance['DBInstanceStatus'],
                    'multi_az': db_instance['MultiAZ'],
                    'storage_type': db_instance['StorageType'],
                    'allocated_storage': db_instance['AllocatedStorage'],
                    'availability_zone': db_instance.get('AvailabilityZone'),
                    'backup_retention_period': db_instance['BackupRetentionPeriod']
                }
                
                # Get metrics
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=30)
                
                metrics_data = await self.get_resource_metrics(
                    db_instance['DBInstanceIdentifier'],
                    ResourceType.RDS,
                    start_time,
                    end_time
                )
                
                metrics = ResourceMetrics(
                    cpu_utilization=metrics_data.get('cpu_utilization', []),
                    custom_metrics={
                        'database_connections': metrics_data.get('database_connections', []),
                        'read_latency': metrics_data.get('read_latency', []),
                        'write_latency': metrics_data.get('write_latency', [])
                    }
                )
                
                resource = AWSResource(
                    resource_id=db_instance['DBInstanceIdentifier'],
                    resource_type=ResourceType.RDS,
                    region=region,
                    account_id=self._extract_account_id_from_arn(db_instance['DBInstanceArn']),
                    tags=tags,
                    configuration=configuration,
                    metrics=metrics,
                    created_at=db_instance.get('InstanceCreateTime'),
                    last_updated=datetime.utcnow()
                )
                
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Failed to get RDS instances in {region}: {str(e)}")
            return []

    async def _get_load_balancers(self, region: str) -> List[AWSResource]:
        """Get Elastic Load Balancers."""
        elbv2 = self._get_client('elbv2', region)
        
        try:
            response = elbv2.describe_load_balancers()
            resources = []
            
            for lb in response['LoadBalancers']:
                # Get tags
                tags_response = elbv2.describe_tags(ResourceArns=[lb['LoadBalancerArn']])
                tags = {}
                if tags_response['TagDescriptions']:
                    tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0]['Tags']}
                
                configuration = {
                    'type': lb['Type'],
                    'scheme': lb['Scheme'],
                    'state': lb['State']['Code'],
                    'availability_zones': [az['ZoneName'] for az in lb['AvailabilityZones']],
                    'vpc_id': lb['VpcId'],
                    'ip_address_type': lb.get('IpAddressType', 'ipv4')
                }
                
                # Get metrics
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=30)
                
                metrics_data = await self.get_resource_metrics(
                    lb['LoadBalancerName'],
                    ResourceType.ELB,
                    start_time,
                    end_time
                )
                
                metrics = ResourceMetrics(
                    custom_metrics={
                        'request_count': metrics_data.get('request_count', []),
                        'target_response_time': metrics_data.get('target_response_time', []),
                        'active_connection_count': metrics_data.get('active_connection_count', [])
                    }
                )
                
                resource = AWSResource(
                    resource_id=lb['LoadBalancerName'],
                    resource_type=ResourceType.ELB,
                    region=region,
                    account_id=self._extract_account_id_from_arn(lb['LoadBalancerArn']),
                    tags=tags,
                    configuration=configuration,
                    metrics=metrics,
                    created_at=lb.get('CreatedTime'),
                    last_updated=datetime.utcnow()
                )
                
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Failed to get load balancers in {region}: {str(e)}")
            return []

    async def _get_lambda_functions(self, region: str) -> List[AWSResource]:
        """Get Lambda functions."""
        lambda_client = self._get_client('lambda', region)
        
        try:
            response = lambda_client.list_functions()
            resources = []
            
            for function in response['Functions']:
                # Get tags
                try:
                    tags_response = lambda_client.list_tags(Resource=function['FunctionArn'])
                    tags = tags_response.get('Tags', {})
                except:
                    tags = {}
                
                configuration = {
                    'runtime': function['Runtime'],
                    'memory_size': function['MemorySize'],
                    'timeout': function['Timeout'],
                    'handler': function['Handler'],
                    'code_size': function['CodeSize'],
                    'last_modified': function['LastModified'],
                    'environment_variables': function.get('Environment', {}).get('Variables', {})
                }
                
                # Get metrics
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=30)
                
                metrics_data = await self.get_resource_metrics(
                    function['FunctionName'],
                    ResourceType.LAMBDA,
                    start_time,
                    end_time
                )
                
                metrics = ResourceMetrics(
                    custom_metrics={
                        'invocations': metrics_data.get('invocations', []),
                        'duration': metrics_data.get('duration', []),
                        'errors': metrics_data.get('errors', []),
                        'throttles': metrics_data.get('throttles', [])
                    }
                )
                
                resource = AWSResource(
                    resource_id=function['FunctionName'],
                    resource_type=ResourceType.LAMBDA,
                    region=region,
                    account_id=self._extract_account_id_from_arn(function['FunctionArn']),
                    tags=tags,
                    configuration=configuration,
                    metrics=metrics,
                    last_updated=datetime.utcnow()
                )
                
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Failed to get Lambda functions in {region}: {str(e)}")
            return []

    async def _get_ebs_volumes(self, region: str) -> List[AWSResource]:
        """Get EBS volumes."""
        ec2 = self._get_client('ec2', region)
        
        try:
            response = ec2.describe_volumes()
            resources = []
            
            for volume in response['Volumes']:
                # Extract tags
                tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                
                configuration = {
                    'volume_type': volume['VolumeType'],
                    'size': volume['Size'],
                    'state': volume['State'],
                    'availability_zone': volume['AvailabilityZone'],
                    'encrypted': volume['Encrypted'],
                    'iops': volume.get('Iops'),
                    'throughput': volume.get('Throughput'),
                    'attachments': volume.get('Attachments', [])
                }
                
                # Get metrics
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=30)
                
                metrics_data = await self.get_resource_metrics(
                    volume['VolumeId'],
                    ResourceType.EBS,
                    start_time,
                    end_time
                )
                
                metrics = ResourceMetrics(
                    disk_read_ops=metrics_data.get('read_ops', []),
                    disk_write_ops=metrics_data.get('write_ops', []),
                    custom_metrics={
                        'read_bytes': metrics_data.get('read_bytes', []),
                        'write_bytes': metrics_data.get('write_bytes', []),
                        'queue_depth': metrics_data.get('queue_depth', [])
                    }
                )
                
                resource = AWSResource(
                    resource_id=volume['VolumeId'],
                    resource_type=ResourceType.EBS,
                    region=region,
                    account_id=self._extract_account_id(volume['VolumeId']),
                    tags=tags,
                    configuration=configuration,
                    metrics=metrics,
                    created_at=volume.get('CreateTime'),
                    last_updated=datetime.utcnow()
                )
                
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Failed to get EBS volumes in {region}: {str(e)}")
            return []

    def _get_metric_configs(self, resource_type: ResourceType, resource_id: str) -> Dict[str, Dict]:
        """Get CloudWatch metric configurations for resource type."""
        configs = {
            ResourceType.EC2: {
                'cpu_utilization': {
                    'namespace': 'AWS/EC2',
                    'metric_name': 'CPUUtilization',
                    'dimensions': [{'Name': 'InstanceId', 'Value': resource_id}]
                },
                'network_in': {
                    'namespace': 'AWS/EC2',
                    'metric_name': 'NetworkIn',
                    'dimensions': [{'Name': 'InstanceId', 'Value': resource_id}]
                },
                'network_out': {
                    'namespace': 'AWS/EC2',
                    'metric_name': 'NetworkOut',
                    'dimensions': [{'Name': 'InstanceId', 'Value': resource_id}]
                }
            },
            ResourceType.RDS: {
                'cpu_utilization': {
                    'namespace': 'AWS/RDS',
                    'metric_name': 'CPUUtilization',
                    'dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': resource_id}]
                },
                'database_connections': {
                    'namespace': 'AWS/RDS',
                    'metric_name': 'DatabaseConnections',
                    'dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': resource_id}]
                }
            },
            ResourceType.ELB: {
                'request_count': {
                    'namespace': 'AWS/ApplicationELB',
                    'metric_name': 'RequestCount',
                    'dimensions': [{'Name': 'LoadBalancer', 'Value': resource_id}]
                }
            },
            ResourceType.LAMBDA: {
                'invocations': {
                    'namespace': 'AWS/Lambda',
                    'metric_name': 'Invocations',
                    'dimensions': [{'Name': 'FunctionName', 'Value': resource_id}]
                },
                'duration': {
                    'namespace': 'AWS/Lambda',
                    'metric_name': 'Duration',
                    'dimensions': [{'Name': 'FunctionName', 'Value': resource_id}]
                }
            },
            ResourceType.EBS: {
                'read_ops': {
                    'namespace': 'AWS/EBS',
                    'metric_name': 'VolumeReadOps',
                    'dimensions': [{'Name': 'VolumeId', 'Value': resource_id}]
                },
                'write_ops': {
                    'namespace': 'AWS/EBS',
                    'metric_name': 'VolumeWriteOps',
                    'dimensions': [{'Name': 'VolumeId', 'Value': resource_id}]
                }
            }
        }
        
        return configs.get(resource_type, {})

    def _extract_account_id(self, resource_id: str) -> str:
        """Extract AWS account ID from resource ID or ARN."""
        # For most resources, we'll need to get this from STS
        try:
            sts = self._get_client('sts')
            response = sts.get_caller_identity()
            return response['Account']
        except:
            return "unknown"

    def _extract_account_id_from_arn(self, arn: str) -> str:
        """Extract account ID from ARN."""
        try:
            # ARN format: arn:partition:service:region:account-id:resource
            return arn.split(':')[4]
        except:
            return "unknown"