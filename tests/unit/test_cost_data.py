"""
Unit tests for CostData entity.
Tests cost aggregation and serialization.
"""

import pytest
from decimal import Decimal
from src.domain.entities import CostData


class TestCostData:
    """Tests for CostData entity."""
    
    def test_create_cost_data(self):
        """Test creating cost data."""
        cost_data = CostData(
            total_cost_usd=Decimal('1234.56'),
            period_days=30,
            cost_by_service={'EC2': Decimal('800.00'), 'RDS': Decimal('434.56')}
        )
        
        assert cost_data.total_cost_usd == Decimal('1234.56')
        assert cost_data.period_days == 30
        assert len(cost_data.cost_by_service) == 2
    
    def test_get_top_services(self):
        """Test getting top services by cost."""
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30,
            cost_by_service={
                'EC2': Decimal('500.00'),
                'RDS': Decimal('300.00'),
                'S3': Decimal('100.00'),
                'Lambda': Decimal('50.00'),
                'CloudWatch': Decimal('50.00')
            }
        )
        
        top_services = cost_data.get_top_services(limit=3)
        
        assert len(top_services) == 3
        assert top_services[0]['service'] == 'EC2'
        assert top_services[0]['cost_usd'] == 500.00
        assert top_services[0]['percentage'] == 50.0
        assert top_services[1]['service'] == 'RDS'
        assert top_services[2]['service'] == 'S3'
    
    def test_get_top_services_all(self):
        """Test getting all services when limit is higher."""
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30,
            cost_by_service={
                'EC2': Decimal('500.00'),
                'RDS': Decimal('300.00'),
                'S3': Decimal('200.00')
            }
        )
        
        top_services = cost_data.get_top_services(limit=10)
        
        assert len(top_services) == 3
    
    def test_to_dict(self):
        """Test converting cost data to dictionary."""
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30,
            cost_by_service={'EC2': Decimal('600.00'), 'RDS': Decimal('400.00')},
            daily_costs=[{'date': '2025-11-01', 'cost': 33.33}]
        )
        
        result = cost_data.to_dict()
        
        assert result['total_cost_usd'] == 1000.00
        assert result['period_days'] == 30
        assert result['cost_by_service']['EC2'] == 600.00
        assert result['cost_by_service']['RDS'] == 400.00
        assert len(result['top_services']) >= 0
        assert len(result['daily_costs']) == 1
    
    def test_zero_total_cost(self):
        """Test handling zero total cost."""
        cost_data = CostData(
            total_cost_usd=Decimal('0.00'),
            period_days=30,
            cost_by_service={}
        )
        
        top_services = cost_data.get_top_services()
        
        assert len(top_services) == 0
        
        result = cost_data.to_dict()
        assert result['total_cost_usd'] == 0.0
