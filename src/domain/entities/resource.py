"""
Domain Entity: Resource
Representa um recurso AWS no domínio da aplicação
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from decimal import Decimal


class ResourceType(Enum):
    """Tipos de recursos AWS suportados"""
    EC2 = "EC2"
    RDS = "RDS"
    ELB = "ELB"
    LAMBDA = "Lambda"
    EBS = "EBS"
    S3 = "S3"
    DYNAMODB = "DynamoDB"


class UsagePattern(Enum):
    """Padrões de uso identificados"""
    STEADY = "steady"
    VARIABLE = "variable"
    BATCH = "batch"
    IDLE = "idle"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Níveis de risco para implementação"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Priority(Enum):
    """Prioridades de implementação"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Metric:
    """Representa uma métrica de monitoramento"""
    name: str
    value: float
    timestamp: datetime
    unit: str


@dataclass
class ResourceMetrics:
    """Métricas agregadas de um recurso"""
    cpu_utilization: List[Metric]
    memory_utilization: Optional[List[Metric]] = None
    network_in: Optional[List[Metric]] = None
    network_out: Optional[List[Metric]] = None
    custom_metrics: Optional[Dict[str, List[Metric]]] = None

    def get_cpu_statistics(self) -> Dict[str, float]:
        """Calcula estatísticas de CPU"""
        if not self.cpu_utilization:
            return {}
        
        values = [m.value for m in self.cpu_utilization]
        values.sort()
        
        return {
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'p50': values[int(len(values) * 0.5)],
            'p95': values[int(len(values) * 0.95)],
            'p99': values[int(len(values) * 0.99)]
        }


@dataclass
class CostData:
    """Dados de custo de um recurso"""
    monthly_cost_usd: Decimal
    daily_cost_usd: Decimal
    cost_breakdown: Optional[Dict[str, Decimal]] = None


class Resource(ABC):
    """Entidade base para todos os recursos AWS"""
    
    def __init__(
        self,
        resource_id: str,
        resource_type: ResourceType,
        region: str,
        tags: Optional[Dict[str, str]] = None,
        metrics: Optional[ResourceMetrics] = None,
        cost_data: Optional[CostData] = None
    ):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.region = region
        self.tags = tags or {}
        self.metrics = metrics
        self.cost_data = cost_data
        self.created_at = datetime.now()
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Retorna a configuração atual do recurso"""
        pass
    
    @abstractmethod
    def calculate_utilization(self) -> float:
        """Calcula a utilização média do recurso"""
        pass
    
    def get_environment(self) -> str:
        """Extrai o ambiente das tags"""
        return self.tags.get('Environment', 'unknown').lower()
    
    def get_criticality(self) -> str:
        """Extrai a criticidade das tags"""
        return self.tags.get('Criticality', 'medium').lower()
    
    def is_production(self) -> bool:
        """Verifica se é ambiente de produção"""
        return self.get_environment() in ['prod', 'production']


@dataclass
class EC2Resource(Resource):
    """Recurso EC2 específico"""
    
    def __init__(
        self,
        resource_id: str,
        region: str,
        instance_type: str,
        state: str,
        availability_zone: str,
        launch_time: datetime,
        tags: Optional[Dict[str, str]] = None,
        metrics: Optional[ResourceMetrics] = None,
        cost_data: Optional[CostData] = None
    ):
        super().__init__(resource_id, ResourceType.EC2, region, tags, metrics, cost_data)
        self.instance_type = instance_type
        self.state = state
        self.availability_zone = availability_zone
        self.launch_time = launch_time
    
    def get_configuration(self) -> Dict[str, Any]:
        return {
            'instance_type': self.instance_type,
            'state': self.state,
            'availability_zone': self.availability_zone,
            'launch_time': self.launch_time.isoformat()
        }
    
    def calculate_utilization(self) -> float:
        if not self.metrics or not self.metrics.cpu_utilization:
            return 0.0
        
        stats = self.metrics.get_cpu_statistics()
        return stats.get('mean', 0.0)
    
    def get_vcpu_count(self) -> int:
        """Retorna número de vCPUs baseado no tipo de instância"""
        # Mapeamento simplificado - em produção usar API ou tabela completa
        vcpu_map = {
            't3.nano': 2, 't3.micro': 2, 't3.small': 2, 't3.medium': 2,
            't3.large': 2, 't3.xlarge': 4, 't3.2xlarge': 8,
            't3a.nano': 2, 't3a.micro': 2, 't3a.small': 2, 't3a.medium': 2,
            't3a.large': 2, 't3a.xlarge': 4, 't3a.2xlarge': 8,
            'm5.large': 2, 'm5.xlarge': 4, 'm5.2xlarge': 8, 'm5.4xlarge': 16,
            'c5.large': 2, 'c5.xlarge': 4, 'c5.2xlarge': 8, 'c5.4xlarge': 16
        }
        return vcpu_map.get(self.instance_type, 2)
    
    def get_memory_gb(self) -> float:
        """Retorna quantidade de memória em GB baseado no tipo de instância"""
        # Mapeamento simplificado
        memory_map = {
            't3.nano': 0.5, 't3.micro': 1, 't3.small': 2, 't3.medium': 4,
            't3.large': 8, 't3.xlarge': 16, 't3.2xlarge': 32,
            't3a.nano': 0.5, 't3a.micro': 1, 't3a.small': 2, 't3a.medium': 4,
            't3a.large': 8, 't3a.xlarge': 16, 't3a.2xlarge': 32,
            'm5.large': 8, 'm5.xlarge': 16, 'm5.2xlarge': 32, 'm5.4xlarge': 64,
            'c5.large': 4, 'c5.xlarge': 8, 'c5.2xlarge': 16, 'c5.4xlarge': 32
        }
        return memory_map.get(self.instance_type, 4.0)


@dataclass
class RDSResource(Resource):
    """Recurso RDS específico"""
    
    def __init__(
        self,
        resource_id: str,
        region: str,
        instance_class: str,
        engine: str,
        engine_version: str,
        storage_type: str,
        allocated_storage_gb: int,
        multi_az: bool,
        availability_zone: str,
        tags: Optional[Dict[str, str]] = None,
        metrics: Optional[ResourceMetrics] = None,
        cost_data: Optional[CostData] = None
    ):
        super().__init__(resource_id, ResourceType.RDS, region, tags, metrics, cost_data)
        self.instance_class = instance_class
        self.engine = engine
        self.engine_version = engine_version
        self.storage_type = storage_type
        self.allocated_storage_gb = allocated_storage_gb
        self.multi_az = multi_az
        self.availability_zone = availability_zone
    
    def get_configuration(self) -> Dict[str, Any]:
        return {
            'instance_class': self.instance_class,
            'engine': self.engine,
            'engine_version': self.engine_version,
            'storage_type': self.storage_type,
            'allocated_storage_gb': self.allocated_storage_gb,
            'multi_az': self.multi_az,
            'availability_zone': self.availability_zone
        }
    
    def calculate_utilization(self) -> float:
        if not self.metrics or not self.metrics.cpu_utilization:
            return 0.0
        
        stats = self.metrics.get_cpu_statistics()
        return stats.get('mean', 0.0)


@dataclass
class LambdaResource(Resource):
    """Recurso Lambda específico"""
    
    def __init__(
        self,
        resource_id: str,
        region: str,
        runtime: str,
        memory_mb: int,
        timeout_seconds: int,
        tags: Optional[Dict[str, str]] = None,
        metrics: Optional[ResourceMetrics] = None,
        cost_data: Optional[CostData] = None
    ):
        super().__init__(resource_id, ResourceType.LAMBDA, region, tags, metrics, cost_data)
        self.runtime = runtime
        self.memory_mb = memory_mb
        self.timeout_seconds = timeout_seconds
    
    def get_configuration(self) -> Dict[str, Any]:
        return {
            'runtime': self.runtime,
            'memory_mb': self.memory_mb,
            'timeout_seconds': self.timeout_seconds
        }
    
    def calculate_utilization(self) -> float:
        # Para Lambda, utilizamos invocações como proxy de utilização
        if not self.metrics or not self.metrics.custom_metrics:
            return 0.0
        
        invocations = self.metrics.custom_metrics.get('invocations', [])
        if not invocations:
            return 0.0
        
        # Normalizar baseado em um threshold (ex: 1000 invocações/dia = 100%)
        total_invocations = sum(m.value for m in invocations)
        daily_invocations = total_invocations / 30  # Assumindo 30 dias de dados
        
        return min(daily_invocations / 1000 * 100, 100)  # Max 100%