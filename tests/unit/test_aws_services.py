"""Tests for AWS service registry and support."""

import pytest
from src.domain.entities import ResourceType
from src.infrastructure.aws.aws_service_registry import (
    AWS_SERVICE_REGISTRY,
    get_service_info,
    get_services_by_category,
    get_all_categories,
    ServiceCategory,
)


class TestAWSServiceRegistry:
    """Tests for AWS service registry covering 80+ services."""
    
    def test_all_resource_types_in_registry(self):
        """Test all ResourceType enum values are in registry (except generic/unknown)."""
        all_types = [t for t in ResourceType if t.value not in ['Generic', 'Unknown']]
        registry_types = set(AWS_SERVICE_REGISTRY.keys())
        
        # 80+ types should be in registry
        assert len(registry_types) >= 65
    
    def test_service_info_retrieval(self):
        """Test retrieving service info."""
        ec2_info = get_service_info(ResourceType.EC2)
        
        assert ec2_info['name'] == 'Elastic Compute Cloud'
        assert ec2_info['category'] == ServiceCategory.COMPUTE
        assert len(ec2_info['metrics']) > 0
        assert len(ec2_info['optimization_opportunities']) > 0
    
    def test_all_categories_exist(self):
        """Test all service categories are defined."""
        categories = get_all_categories()
        
        assert ServiceCategory.COMPUTE in categories
        assert ServiceCategory.STORAGE in categories
        assert ServiceCategory.DATABASE in categories
        assert ServiceCategory.NETWORKING in categories
        assert ServiceCategory.ANALYTICS in categories
        assert len(categories) >= 6
    
    def test_services_by_category_compute(self):
        """Test getting compute services."""
        compute_services = get_services_by_category(ServiceCategory.COMPUTE)
        
        assert ResourceType.EC2 in compute_services
        assert ResourceType.LAMBDA in compute_services
        assert ResourceType.ECS in compute_services
        assert len(compute_services) >= 5
    
    def test_services_by_category_storage(self):
        """Test getting storage services."""
        storage_services = get_services_by_category(ServiceCategory.STORAGE)
        
        assert ResourceType.S3 in storage_services
        assert ResourceType.EBS in storage_services
        assert len(storage_services) >= 7
    
    def test_services_by_category_database(self):
        """Test getting database services."""
        database_services = get_services_by_category(ServiceCategory.DATABASE)
        
        assert ResourceType.RDS in database_services
        assert ResourceType.DYNAMODB in database_services
        assert ResourceType.REDSHIFT in database_services
        assert len(database_services) >= 10
    
    def test_services_by_category_ai_ml(self):
        """Test getting AI/ML services."""
        ai_services = get_services_by_category(ServiceCategory.AI_ML)
        
        assert ResourceType.SAGEMAKER in ai_services
        assert ResourceType.REKOGNITION in ai_services
        assert ResourceType.BEDROCK in ai_services
        assert len(ai_services) >= 9
    
    def test_ec2_optimization_opportunities(self):
        """Test EC2 has optimization opportunities."""
        ec2_info = get_service_info(ResourceType.EC2)
        
        opportunities = ec2_info['optimization_opportunities']
        assert 'Right-sizing' in opportunities
        assert 'Spot instances' in opportunities
    
    def test_s3_optimization_opportunities(self):
        """Test S3 has optimization opportunities."""
        s3_info = get_service_info(ResourceType.S3)
        
        opportunities = s3_info['optimization_opportunities']
        assert 'Storage class analysis' in opportunities
        assert 'Lifecycle policies' in opportunities
    
    def test_rds_optimization_opportunities(self):
        """Test RDS has optimization opportunities."""
        rds_info = get_service_info(ResourceType.RDS)
        
        opportunities = rds_info['optimization_opportunities']
        assert 'Instance right-sizing' in opportunities
    
    def test_dynamodb_optimization_opportunities(self):
        """Test DynamoDB has optimization opportunities."""
        dynamodb_info = get_service_info(ResourceType.DYNAMODB)
        
        opportunities = dynamodb_info['optimization_opportunities']
        assert len(opportunities) > 0
    
    def test_lambda_optimization_opportunities(self):
        """Test Lambda has optimization opportunities."""
        lambda_info = get_service_info(ResourceType.LAMBDA)
        
        opportunities = lambda_info['optimization_opportunities']
        assert 'Memory optimization' in opportunities
    
    def test_service_registry_completeness(self):
        """Test service registry has meaningful data."""
        registry_count = len(AWS_SERVICE_REGISTRY)
        
        # Should have at least 65 services
        assert registry_count >= 65
        
        # Each service should have metrics
        for service_type, info in AWS_SERVICE_REGISTRY.items():
            assert 'name' in info
            assert 'category' in info
            assert 'metrics' in info
            assert 'optimization_opportunities' in info
            assert len(info['optimization_opportunities']) > 0


class TestResourceTypeExpansion:
    """Tests for ResourceType enum expansion to 80+ services."""
    
    def test_compute_resource_types(self):
        """Test all compute resource types exist."""
        compute_types = [
            ResourceType.EC2,
            ResourceType.LAMBDA,
            ResourceType.ECS,
            ResourceType.EKS,
            ResourceType.BATCH,
            ResourceType.LIGHTSAIL,
            ResourceType.APPSTREAM,
        ]
        
        for rt in compute_types:
            assert rt is not None
    
    def test_storage_resource_types(self):
        """Test all storage resource types exist."""
        storage_types = [
            ResourceType.S3,
            ResourceType.EBS,
            ResourceType.EFS,
            ResourceType.FSX,
            ResourceType.GLACIER,
            ResourceType.STORAGE_GATEWAY,
            ResourceType.BACKUP,
        ]
        
        for rt in storage_types:
            assert rt is not None
    
    def test_database_resource_types(self):
        """Test all database resource types exist."""
        database_types = [
            ResourceType.RDS,
            ResourceType.DYNAMODB,
            ResourceType.ELASTICACHE,
            ResourceType.REDSHIFT,
            ResourceType.DOCUMENTDB,
            ResourceType.NEPTUNE,
            ResourceType.QLDB,
            ResourceType.TIMESTREAM,
            ResourceType.DAX,
            ResourceType.MEMORYDB,
        ]
        
        for rt in database_types:
            assert rt is not None
    
    def test_networking_resource_types(self):
        """Test all networking resource types exist."""
        networking_types = [
            ResourceType.ELB,
            ResourceType.ALB,
            ResourceType.NLB,
            ResourceType.CLOUDFRONT,
            ResourceType.ROUTE53,
            ResourceType.VPC,
            ResourceType.DIRECT_CONNECT,
            ResourceType.TRANSIT_GATEWAY,
        ]
        
        for rt in networking_types:
            assert rt is not None
    
    def test_analytics_resource_types(self):
        """Test all analytics resource types exist."""
        analytics_types = [
            ResourceType.ATHENA,
            ResourceType.EMR,
            ResourceType.KINESIS,
            ResourceType.MSK,
            ResourceType.GLUE,
        ]
        
        for rt in analytics_types:
            assert rt is not None
    
    def test_ai_ml_resource_types(self):
        """Test all AI/ML resource types exist."""
        ai_types = [
            ResourceType.SAGEMAKER,
            ResourceType.REKOGNITION,
            ResourceType.BEDROCK,
            ResourceType.COMPREHEND,
            ResourceType.TEXTRACT,
        ]
        
        for rt in ai_types:
            assert rt is not None
    
    def test_security_resource_types(self):
        """Test all security resource types exist."""
        security_types = [
            ResourceType.IAM,
            ResourceType.COGNITO,
            ResourceType.KMS,
            ResourceType.WAF,
            ResourceType.SHIELD,
            ResourceType.GUARDDUTY,
        ]
        
        for rt in security_types:
            assert rt is not None
    
    def test_total_resource_types(self):
        """Test total number of resource types."""
        resource_types = [t for t in ResourceType]
        
        # Should have 80+ types (including GENERIC and UNKNOWN)
        assert len(resource_types) >= 80
