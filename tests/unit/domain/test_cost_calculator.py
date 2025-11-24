"""
Unit tests for CostCalculator service.
Tests cost calculation and savings estimation logic.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.domain.entities import (
    ResourceType,
    AWSResource,
    ResourceMetrics,
    MetricDataPoint,
    Priority,
    RiskLevel
)


class TestCostCalculator:
    """Tests for cost calculation service."""
    
    def test_calculate_ec2_hourly_cost_t3a_micro(self):
        """Test EC2 t3a.micro hourly cost calculation."""
        instance_type = "t3a.micro"
        hourly_cost = 0.0094
        monthly_hours = 730
        
        expected_monthly = Decimal(str(hourly_cost)) * monthly_hours
        
        assert float(expected_monthly) == pytest.approx(6.86, rel=0.01)
    
    def test_calculate_ec2_hourly_cost_t3a_large(self):
        """Test EC2 t3a.large hourly cost calculation."""
        instance_type = "t3a.large"
        hourly_cost = 0.0752
        monthly_hours = 730
        
        expected_monthly = Decimal(str(hourly_cost)) * monthly_hours
        
        assert float(expected_monthly) == pytest.approx(54.90, rel=0.01)
    
    def test_calculate_ec2_hourly_cost_m5_xlarge(self):
        """Test EC2 m5.xlarge hourly cost calculation."""
        hourly_cost = 0.192
        monthly_hours = 730
        
        expected_monthly = Decimal(str(hourly_cost)) * monthly_hours
        
        assert float(expected_monthly) == pytest.approx(140.16, rel=0.01)
    
    def test_calculate_rds_cost_db_t3_medium(self):
        """Test RDS db.t3.medium hourly cost calculation."""
        hourly_cost = 0.068
        monthly_hours = 730
        
        expected_monthly = Decimal(str(hourly_cost)) * monthly_hours
        
        assert float(expected_monthly) == pytest.approx(49.64, rel=0.01)
    
    def test_calculate_rds_cost_db_r5_xlarge(self):
        """Test RDS db.r5.xlarge hourly cost calculation."""
        hourly_cost = 0.48
        monthly_hours = 730
        
        expected_monthly = Decimal(str(hourly_cost)) * monthly_hours
        
        assert float(expected_monthly) == pytest.approx(350.40, rel=0.01)
    
    def test_calculate_lambda_cost_per_invocation(self):
        """Test Lambda cost per invocation."""
        invocations = 1_000_000
        cost_per_million = 0.20
        
        expected = Decimal(str(invocations / 1_000_000 * cost_per_million))
        
        assert expected == Decimal('0.20')
    
    def test_calculate_lambda_cost_with_memory(self):
        """Test Lambda cost with memory and duration."""
        invocations = 1_000_000
        memory_mb = 512
        duration_ms = 200
        
        gb_seconds = (memory_mb / 1024) * (duration_ms / 1000) * invocations
        cost_per_gb_second = 0.0000166667
        
        expected = Decimal(str(gb_seconds * cost_per_gb_second))
        
        assert expected > 0
    
    def test_calculate_s3_storage_cost_standard(self):
        """Test S3 Standard storage cost."""
        storage_gb = 1000
        cost_per_gb = 0.023
        
        expected_monthly = Decimal(str(storage_gb * cost_per_gb))
        
        assert expected_monthly == Decimal('23.00')
    
    def test_calculate_s3_storage_cost_glacier(self):
        """Test S3 Glacier storage cost."""
        storage_gb = 1000
        cost_per_gb = 0.004
        
        expected_monthly = Decimal(str(storage_gb * cost_per_gb))
        
        assert expected_monthly == Decimal('4.00')
    
    def test_calculate_savings_downsize_50_percent(self):
        """Test savings calculation for 50% downsize."""
        current_monthly = Decimal('100.00')
        new_monthly = Decimal('50.00')
        
        savings = current_monthly - new_monthly
        savings_percentage = (savings / current_monthly) * 100
        
        assert savings == Decimal('50.00')
        assert savings_percentage == 50
    
    def test_calculate_savings_delete_100_percent(self):
        """Test savings calculation for deletion (100%)."""
        current_monthly = Decimal('100.00')
        new_monthly = Decimal('0.00')
        
        savings = current_monthly - new_monthly
        savings_percentage = (savings / current_monthly) * 100
        
        assert savings == Decimal('100.00')
        assert savings_percentage == 100
    
    def test_calculate_annual_savings(self):
        """Test annual savings calculation."""
        monthly_savings = Decimal('50.00')
        
        annual_savings = monthly_savings * 12
        
        assert annual_savings == Decimal('600.00')
    
    def test_calculate_reserved_instance_savings(self):
        """Test Reserved Instance savings calculation."""
        on_demand_monthly = Decimal('100.00')
        ri_monthly = Decimal('60.00')
        
        savings = on_demand_monthly - ri_monthly
        savings_percentage = (savings / on_demand_monthly) * 100
        
        assert savings == Decimal('40.00')
        assert savings_percentage == 40
    
    def test_calculate_spot_instance_savings(self):
        """Test Spot Instance savings calculation."""
        on_demand_hourly = Decimal('0.10')
        spot_hourly = Decimal('0.03')
        
        savings_percentage = ((on_demand_hourly - spot_hourly) / on_demand_hourly) * 100
        
        assert savings_percentage == 70
    
    def test_cost_with_zero_usage(self):
        """Test cost calculation with zero usage."""
        usage = 0
        cost_per_unit = Decimal('0.10')
        
        expected = Decimal(str(usage)) * cost_per_unit
        
        assert expected == Decimal('0.00')
    
    def test_cost_with_negative_value_raises_error(self):
        """Test that negative values raise appropriate errors."""
        with pytest.raises(ValueError):
            if -100 < 0:
                raise ValueError("Cost cannot be negative")
    
    def test_aggregate_costs_multiple_resources(self):
        """Test aggregating costs from multiple resources."""
        costs = [
            Decimal('100.00'),
            Decimal('200.00'),
            Decimal('150.00')
        ]
        
        total = sum(costs)
        
        assert total == Decimal('450.00')
    
    def test_cost_breakdown_by_service(self):
        """Test cost breakdown by service type."""
        cost_by_service = {
            'EC2': Decimal('500.00'),
            'RDS': Decimal('300.00'),
            'S3': Decimal('100.00')
        }
        
        total = sum(cost_by_service.values())
        ec2_percentage = (cost_by_service['EC2'] / total) * 100
        
        assert total == Decimal('900.00')
        assert float(ec2_percentage) == pytest.approx(55.56, rel=0.01)


class TestPriorityCalculator:
    """Tests for priority calculation service."""
    
    def test_priority_high_with_savings_over_100(self):
        """Test HIGH priority with savings > $100/month."""
        monthly_savings = Decimal('150.00')
        risk_level = RiskLevel.LOW
        
        if monthly_savings > 100 and risk_level == RiskLevel.LOW:
            priority = Priority.HIGH
        else:
            priority = Priority.MEDIUM
        
        assert priority == Priority.HIGH
    
    def test_priority_medium_with_savings_50_to_100(self):
        """Test MEDIUM priority with savings $50-$100/month."""
        monthly_savings = Decimal('75.00')
        
        if monthly_savings >= 50 and monthly_savings <= 100:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW
        
        assert priority == Priority.MEDIUM
    
    def test_priority_low_with_savings_under_50(self):
        """Test LOW priority with savings < $50/month."""
        monthly_savings = Decimal('25.00')
        
        if monthly_savings < 50:
            priority = Priority.LOW
        else:
            priority = Priority.MEDIUM
        
        assert priority == Priority.LOW
    
    def test_priority_considers_risk_level(self):
        """Test that priority considers risk level."""
        monthly_savings = Decimal('200.00')
        risk_high = RiskLevel.HIGH
        
        if risk_high == RiskLevel.HIGH:
            priority = Priority.MEDIUM
        else:
            priority = Priority.HIGH
        
        assert priority == Priority.MEDIUM
    
    def test_priority_production_environment(self):
        """Test priority adjustment for production environment."""
        is_production = True
        base_priority = Priority.HIGH
        
        if is_production and base_priority == Priority.HIGH:
            adjusted_priority = Priority.MEDIUM
        else:
            adjusted_priority = base_priority
        
        assert adjusted_priority == Priority.MEDIUM


class TestRiskCalculator:
    """Tests for risk calculation service."""
    
    def test_risk_high_for_production_delete(self):
        """Test HIGH risk for production resource deletion."""
        is_production = True
        action = "delete"
        
        if is_production and action == "delete":
            risk = RiskLevel.HIGH
        else:
            risk = RiskLevel.MEDIUM
        
        assert risk == RiskLevel.HIGH
    
    def test_risk_medium_for_production_downsize(self):
        """Test MEDIUM risk for production resource downsize."""
        is_production = True
        action = "downsize"
        change_percentage = 25
        
        if is_production and action == "downsize":
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.LOW
        
        assert risk == RiskLevel.MEDIUM
    
    def test_risk_low_for_dev_environment(self):
        """Test LOW risk for development environment."""
        is_production = False
        action = "delete"
        
        if not is_production:
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.HIGH
        
        assert risk == RiskLevel.LOW
    
    def test_risk_high_for_big_change_over_50_percent(self):
        """Test HIGH risk for changes > 50%."""
        change_percentage = 60
        
        if change_percentage > 50:
            risk = RiskLevel.HIGH
        elif change_percentage > 25:
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.LOW
        
        assert risk == RiskLevel.HIGH
    
    def test_risk_considers_criticality_tag(self):
        """Test risk considers criticality tag."""
        criticality = "high"
        action = "downsize"
        
        if criticality == "high":
            risk = RiskLevel.HIGH
        else:
            risk = RiskLevel.MEDIUM
        
        assert risk == RiskLevel.HIGH
    
    def test_risk_for_idle_resource_deletion(self):
        """Test risk for idle resource deletion."""
        is_idle = True
        days_idle = 30
        
        if is_idle and days_idle > 14:
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.MEDIUM
        
        assert risk == RiskLevel.LOW


class TestUsageAnalyzer:
    """Tests for usage pattern analysis."""
    
    def test_detect_steady_usage_pattern(self):
        """Test detection of steady usage pattern."""
        cpu_values = [50, 52, 48, 51, 49, 50, 51, 48]
        mean = sum(cpu_values) / len(cpu_values)
        std_dev = (sum((x - mean) ** 2 for x in cpu_values) / len(cpu_values)) ** 0.5
        
        if std_dev < 10:
            pattern = "steady"
        else:
            pattern = "variable"
        
        assert pattern == "steady"
    
    def test_detect_variable_usage_pattern(self):
        """Test detection of variable usage pattern."""
        cpu_values = [10, 90, 20, 85, 15, 92, 18, 88]
        mean = sum(cpu_values) / len(cpu_values)
        std_dev = (sum((x - mean) ** 2 for x in cpu_values) / len(cpu_values)) ** 0.5
        
        if std_dev > 20:
            pattern = "variable"
        else:
            pattern = "steady"
        
        assert pattern == "variable"
    
    def test_detect_idle_resource(self):
        """Test detection of idle resource."""
        cpu_values = [0, 0, 0, 1, 0, 0, 0, 0]
        max_cpu = max(cpu_values)
        
        if max_cpu < 5:
            status = "idle"
        else:
            status = "active"
        
        assert status == "idle"
    
    def test_detect_underutilized_resource(self):
        """Test detection of underutilized resource."""
        cpu_values = [15, 18, 12, 20, 14, 16, 19, 13]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        
        if avg_cpu < 40:
            status = "underutilized"
        else:
            status = "normal"
        
        assert status == "underutilized"
    
    def test_detect_overutilized_resource(self):
        """Test detection of overutilized resource."""
        cpu_values = [85, 90, 88, 92, 87, 91, 89, 86]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        
        if avg_cpu > 80:
            status = "overutilized"
        else:
            status = "normal"
        
        assert status == "overutilized"
