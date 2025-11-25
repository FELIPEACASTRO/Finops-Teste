"""
Testes unitários para entidades de Resource
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.domain.entities.resource import (
    ResourceType,
    UsagePattern,
    Metric,
    ResourceMetrics,
    CostData,
    EC2Resource,
    RDSResource,
    LambdaResource
)


class TestResourceMetrics:
    """Testes para ResourceMetrics"""
    
    def test_get_cpu_statistics_empty(self):
        """Testa estatísticas com lista vazia"""
        metrics = ResourceMetrics(cpu_utilization=[])
        stats = metrics.get_cpu_statistics()
        assert stats == {}
    
    def test_get_cpu_statistics_single_value(self):
        """Testa estatísticas com um único valor"""
        now = datetime.now()
        metric = Metric("cpu", 50.0, now, "%")
        metrics = ResourceMetrics(cpu_utilization=[metric])
        
        stats = metrics.get_cpu_statistics()
        
        assert stats['mean'] == 50.0
        assert stats['min'] == 50.0
        assert stats['max'] == 50.0
        assert stats['p50'] == 50.0
        assert stats['p95'] == 50.0
        assert stats['p99'] == 50.0
    
    def test_get_cpu_statistics_multiple_values(self):
        """Testa estatísticas com múltiplos valores"""
        now = datetime.now()
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        metrics_list = [
            Metric("cpu", value, now + timedelta(hours=i), "%")
            for i, value in enumerate(values)
        ]
        
        metrics = ResourceMetrics(cpu_utilization=metrics_list)
        stats = metrics.get_cpu_statistics()
        
        assert stats['mean'] == 55.0  # (10+20+...+100)/10
        assert stats['min'] == 10.0
        assert stats['max'] == 100.0
        assert stats['p95'] == 100.0  # 95% de 10 valores = índice 9
        assert stats['p99'] == 100.0  # 99% de 10 valores = índice 9


class TestEC2Resource:
    """Testes para EC2Resource"""
    
    def test_ec2_resource_creation(self):
        """Testa criação de recurso EC2"""
        launch_time = datetime.now() - timedelta(days=30)
        tags = {'Environment': 'production', 'Team': 'backend'}
        
        resource = EC2Resource(
            resource_id='i-1234567890abcdef0',
            region='us-east-1',
            instance_type='t3.large',
            state='running',
            availability_zone='us-east-1a',
            launch_time=launch_time,
            tags=tags
        )
        
        assert resource.resource_id == 'i-1234567890abcdef0'
        assert resource.resource_type == ResourceType.EC2
        assert resource.instance_type == 't3.large'
        assert resource.state == 'running'
        assert resource.get_environment() == 'production'
        assert resource.is_production() is True
    
    def test_ec2_get_configuration(self):
        """Testa obtenção de configuração EC2"""
        launch_time = datetime.now()
        resource = EC2Resource(
            resource_id='i-test',
            region='us-east-1',
            instance_type='t3.medium',
            state='running',
            availability_zone='us-east-1b',
            launch_time=launch_time
        )
        
        config = resource.get_configuration()
        
        assert config['instance_type'] == 't3.medium'
        assert config['state'] == 'running'
        assert config['availability_zone'] == 'us-east-1b'
        assert config['launch_time'] == launch_time.isoformat()
    
    def test_ec2_calculate_utilization_no_metrics(self):
        """Testa cálculo de utilização sem métricas"""
        resource = EC2Resource(
            resource_id='i-test',
            region='us-east-1',
            instance_type='t3.medium',
            state='running',
            availability_zone='us-east-1a',
            launch_time=datetime.now()
        )
        
        utilization = resource.calculate_utilization()
        assert utilization == 0.0
    
    def test_ec2_calculate_utilization_with_metrics(self):
        """Testa cálculo de utilização com métricas"""
        now = datetime.now()
        cpu_metrics = [
            Metric("cpu", 25.0, now, "%"),
            Metric("cpu", 35.0, now + timedelta(hours=1), "%"),
            Metric("cpu", 45.0, now + timedelta(hours=2), "%")
        ]
        
        metrics = ResourceMetrics(cpu_utilization=cpu_metrics)
        
        resource = EC2Resource(
            resource_id='i-test',
            region='us-east-1',
            instance_type='t3.medium',
            state='running',
            availability_zone='us-east-1a',
            launch_time=datetime.now(),
            metrics=metrics
        )
        
        utilization = resource.calculate_utilization()
        assert utilization == 35.0  # Média de 25, 35, 45
    
    def test_ec2_get_vcpu_count(self):
        """Testa obtenção de contagem de vCPUs"""
        resource = EC2Resource(
            resource_id='i-test',
            region='us-east-1',
            instance_type='t3.large',
            state='running',
            availability_zone='us-east-1a',
            launch_time=datetime.now()
        )
        
        assert resource.get_vcpu_count() == 2
    
    def test_ec2_get_memory_gb(self):
        """Testa obtenção de memória em GB"""
        resource = EC2Resource(
            resource_id='i-test',
            region='us-east-1',
            instance_type='t3.large',
            state='running',
            availability_zone='us-east-1a',
            launch_time=datetime.now()
        )
        
        assert resource.get_memory_gb() == 8.0


class TestRDSResource:
    """Testes para RDSResource"""
    
    def test_rds_resource_creation(self):
        """Testa criação de recurso RDS"""
        tags = {'Environment': 'staging', 'Application': 'api'}
        
        resource = RDSResource(
            resource_id='mydb-instance',
            region='us-west-2',
            instance_class='db.t3.medium',
            engine='mysql',
            engine_version='8.0.35',
            storage_type='gp2',
            allocated_storage_gb=100,
            multi_az=True,
            availability_zone='us-west-2a',
            tags=tags
        )
        
        assert resource.resource_id == 'mydb-instance'
        assert resource.resource_type == ResourceType.RDS
        assert resource.instance_class == 'db.t3.medium'
        assert resource.engine == 'mysql'
        assert resource.multi_az is True
        assert resource.get_environment() == 'staging'
        assert resource.is_production() is False
    
    def test_rds_get_configuration(self):
        """Testa obtenção de configuração RDS"""
        resource = RDSResource(
            resource_id='test-db',
            region='us-east-1',
            instance_class='db.t3.small',
            engine='postgres',
            engine_version='14.9',
            storage_type='gp3',
            allocated_storage_gb=50,
            multi_az=False,
            availability_zone='us-east-1c'
        )
        
        config = resource.get_configuration()
        
        assert config['instance_class'] == 'db.t3.small'
        assert config['engine'] == 'postgres'
        assert config['engine_version'] == '14.9'
        assert config['storage_type'] == 'gp3'
        assert config['allocated_storage_gb'] == 50
        assert config['multi_az'] is False


class TestLambdaResource:
    """Testes para LambdaResource"""
    
    def test_lambda_resource_creation(self):
        """Testa criação de recurso Lambda"""
        tags = {'Environment': 'production', 'Team': 'data'}
        
        resource = LambdaResource(
            resource_id='my-function',
            region='eu-west-1',
            runtime='python3.11',
            memory_mb=512,
            timeout_seconds=30,
            tags=tags
        )
        
        assert resource.resource_id == 'my-function'
        assert resource.resource_type == ResourceType.LAMBDA
        assert resource.runtime == 'python3.11'
        assert resource.memory_mb == 512
        assert resource.timeout_seconds == 30
    
    def test_lambda_calculate_utilization_no_metrics(self):
        """Testa cálculo de utilização Lambda sem métricas"""
        resource = LambdaResource(
            resource_id='test-function',
            region='us-east-1',
            runtime='python3.11',
            memory_mb=256,
            timeout_seconds=15
        )
        
        utilization = resource.calculate_utilization()
        assert utilization == 0.0
    
    def test_lambda_calculate_utilization_with_invocations(self):
        """Testa cálculo de utilização Lambda com invocações"""
        now = datetime.now()
        invocation_metrics = [
            Metric("invocations", 500, now, "count"),
            Metric("invocations", 750, now + timedelta(days=1), "count"),
            Metric("invocations", 1000, now + timedelta(days=2), "count")
        ]
        
        metrics = ResourceMetrics(
            cpu_utilization=[],
            custom_metrics={'invocations': invocation_metrics}
        )
        
        resource = LambdaResource(
            resource_id='test-function',
            region='us-east-1',
            runtime='python3.11',
            memory_mb=256,
            timeout_seconds=15,
            metrics=metrics
        )
        
        utilization = resource.calculate_utilization()
        # Total: 2250 invocações em 30 dias = 75/dia
        # 75/1000 * 100 = 7.5%
        assert utilization == 7.5


class TestCostData:
    """Testes para CostData"""
    
    def test_cost_data_creation(self):
        """Testa criação de dados de custo"""
        cost_data = CostData(
            monthly_cost_usd=Decimal('150.75'),
            daily_cost_usd=Decimal('5.02'),
            cost_breakdown={'compute': Decimal('120.00'), 'storage': Decimal('30.75')}
        )
        
        assert cost_data.monthly_cost_usd == Decimal('150.75')
        assert cost_data.daily_cost_usd == Decimal('5.02')
        assert cost_data.cost_breakdown['compute'] == Decimal('120.00')


if __name__ == '__main__':
    pytest.main([__file__])