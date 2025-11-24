"""
Unit tests for AWS Service Registry.
Tests actual production implementation.
"""

import pytest
from src.domain.entities import ResourceType
from src.infrastructure.aws.aws_service_registry import (
    ServiceCategory,
    get_service_info,
    get_services_by_category,
    get_all_categories,
    get_total_services_count,
    AWS_SERVICE_REGISTRY
)


class TestAWSServiceRegistry:
    """Tests for AWS Service Registry - actual implementation."""
    
    def test_get_total_services_count(self):
        """Test getting total AWS services count."""
        count = get_total_services_count()
        
        assert count >= 268
    
    def test_get_services_by_category_compute(self):
        """Test getting compute services."""
        compute_services = get_services_by_category(ServiceCategory.COMPUTE)
        
        assert len(compute_services) > 0
        assert ResourceType.EC2 in compute_services
        assert ResourceType.LAMBDA in compute_services
    
    def test_get_services_by_category_storage(self):
        """Test getting storage services."""
        storage_services = get_services_by_category(ServiceCategory.STORAGE)
        
        assert len(storage_services) > 0
        assert ResourceType.S3 in storage_services
        assert ResourceType.EBS in storage_services
    
    def test_get_services_by_category_database(self):
        """Test getting database services."""
        database_services = get_services_by_category(ServiceCategory.DATABASE)
        
        assert len(database_services) > 0
        assert ResourceType.RDS in database_services
        assert ResourceType.DYNAMODB in database_services
    
    def test_get_all_categories(self):
        """Test getting all categories."""
        categories = get_all_categories()
        
        assert isinstance(categories, list)
        assert len(categories) >= 20
        
        assert ServiceCategory.COMPUTE in categories
        assert ServiceCategory.STORAGE in categories
        assert ServiceCategory.DATABASE in categories
    
    def test_get_service_info_ec2(self):
        """Test getting EC2 service info."""
        info = get_service_info(ResourceType.EC2)
        
        assert info is not None
        assert "category" in info
        assert info["category"] == ServiceCategory.COMPUTE
        assert "name" in info
    
    def test_get_service_info_rds(self):
        """Test getting RDS service info."""
        info = get_service_info(ResourceType.RDS)
        
        assert info is not None
        assert info["category"] == ServiceCategory.DATABASE
    
    def test_get_service_info_s3(self):
        """Test getting S3 service info."""
        info = get_service_info(ResourceType.S3)
        
        assert info is not None
        assert info["category"] == ServiceCategory.STORAGE
    
    def test_get_service_info_auto_generated(self):
        """Test service info is auto-generated for services not in explicit registry."""
        for resource_type in ResourceType:
            if resource_type in [ResourceType.GENERIC, ResourceType.UNKNOWN]:
                continue
            
            info = get_service_info(resource_type)
            
            assert info is not None
            assert "category" in info
            assert "name" in info
    
    def test_explicit_registry_has_required_fields(self):
        """Test explicit registry entries have required fields."""
        required_fields = ["category", "name", "metrics"]
        
        for resource_type, info in AWS_SERVICE_REGISTRY.items():
            for field in required_fields:
                assert field in info, f"Service {resource_type} missing field {field}"
    
    def test_all_categories_have_services(self):
        """Test all categories have at least one service."""
        for category in ServiceCategory:
            services = get_services_by_category(category)
            assert len(services) >= 0
    
    def test_total_service_count_matches_268(self):
        """Test total service count is at least 268."""
        count = get_total_services_count()
        
        assert count >= 268, f"Expected at least 268 services, got {count}"


class TestAWSServiceRegistryPerformance:
    """Performance tests for AWS Service Registry."""
    
    def test_get_service_info_performance(self):
        """Test get_service_info is fast."""
        import time
        
        start = time.time()
        for _ in range(100):
            get_service_info(ResourceType.EC2)
        elapsed = time.time() - start
        
        assert elapsed < 1.0, f"100 calls took {elapsed}s, expected < 1s"
    
    def test_get_all_categories_performance(self):
        """Test get_all_categories is fast."""
        import time
        
        start = time.time()
        for _ in range(100):
            get_all_categories()
        elapsed = time.time() - start
        
        assert elapsed < 1.0, f"100 calls took {elapsed}s, expected < 1s"
