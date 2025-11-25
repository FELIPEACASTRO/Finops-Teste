"""
Domain Entity: Recommendation
Representa uma recomendação de otimização de custos
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any

from .resource import ResourceType, RiskLevel, Priority, UsagePattern


class RecommendationAction(Enum):
    """Ações de recomendação possíveis"""
    DOWNSIZE = "downsize"
    UPSIZE = "upsize"
    DELETE = "delete"
    OPTIMIZE = "optimize"
    NO_CHANGE = "no_change"
    SCHEDULE = "schedule"
    MIGRATE = "migrate"


@dataclass
class SavingsEstimate:
    """Estimativa de economia"""
    monthly_usd: Decimal
    annual_usd: Decimal
    percentage: float
    
    def __post_init__(self):
        """Validações pós-inicialização"""
        if self.monthly_usd < 0:
            raise ValueError("Monthly savings cannot be negative")
        if self.percentage < 0 or self.percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")


@dataclass
class ResourceAnalysis:
    """Análise detalhada de um recurso"""
    pattern: UsagePattern
    cpu_mean: float
    cpu_p95: float
    cpu_p99: Optional[float] = None
    memory_mean: Optional[float] = None
    memory_p95: Optional[float] = None
    waste_percentage: float = 0.0
    efficiency_score: float = 0.0  # 0-100
    
    def __post_init__(self):
        """Calcula score de eficiência se não fornecido"""
        if self.efficiency_score == 0.0:
            self.efficiency_score = max(0, 100 - self.waste_percentage)


@dataclass
class ImplementationStep:
    """Passo de implementação de uma recomendação"""
    order: int
    description: str
    estimated_duration_minutes: int
    requires_downtime: bool = False
    automation_possible: bool = False
    
    def __post_init__(self):
        if self.order < 1:
            raise ValueError("Order must be positive")


class Recommendation:
    """Entidade principal de recomendação"""
    
    def __init__(
        self,
        resource_type: ResourceType,
        resource_id: str,
        current_config: str,
        analysis: ResourceAnalysis,
        action: RecommendationAction,
        details: str,
        reasoning: str,
        savings: SavingsEstimate,
        risk_level: RiskLevel,
        priority: Priority,
        implementation_steps: List[ImplementationStep],
        alternatives: Optional[List['Recommendation']] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.current_config = current_config
        self.analysis = analysis
        self.action = action
        self.details = details
        self.reasoning = reasoning
        self.savings = savings
        self.risk_level = risk_level
        self.priority = priority
        self.implementation_steps = sorted(implementation_steps, key=lambda x: x.order)
        self.alternatives = alternatives or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Gera ID único para a recomendação"""
        timestamp = self.created_at.strftime("%Y%m%d_%H%M%S")
        return f"{self.resource_type.value}_{self.resource_id}_{timestamp}"
    
    def get_total_implementation_time(self) -> int:
        """Calcula tempo total de implementação em minutos"""
        return sum(step.estimated_duration_minutes for step in self.implementation_steps)
    
    def requires_downtime(self) -> bool:
        """Verifica se a implementação requer downtime"""
        return any(step.requires_downtime for step in self.implementation_steps)
    
    def is_automatable(self) -> bool:
        """Verifica se a recomendação pode ser automatizada"""
        return all(step.automation_possible for step in self.implementation_steps)
    
    def get_roi_months(self, implementation_cost_usd: Decimal = Decimal('0')) -> float:
        """Calcula ROI em meses"""
        if self.savings.monthly_usd <= 0:
            return float('inf')
        
        return float(implementation_cost_usd / self.savings.monthly_usd)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização"""
        return {
            'id': self.id,
            'resource_type': self.resource_type.value,
            'resource_id': self.resource_id,
            'current_config': self.current_config,
            'analysis': {
                'pattern': self.analysis.pattern.value,
                'cpu_mean': self.analysis.cpu_mean,
                'cpu_p95': self.analysis.cpu_p95,
                'cpu_p99': self.analysis.cpu_p99,
                'memory_mean': self.analysis.memory_mean,
                'memory_p95': self.analysis.memory_p95,
                'waste_percentage': self.analysis.waste_percentage,
                'efficiency_score': self.analysis.efficiency_score
            },
            'recommendation': {
                'action': self.action.value,
                'details': self.details,
                'reasoning': self.reasoning
            },
            'savings': {
                'monthly_usd': float(self.savings.monthly_usd),
                'annual_usd': float(self.savings.annual_usd),
                'percentage': self.savings.percentage
            },
            'risk_level': self.risk_level.value,
            'priority': self.priority.value,
            'implementation_steps': [
                {
                    'order': step.order,
                    'description': step.description,
                    'estimated_duration_minutes': step.estimated_duration_minutes,
                    'requires_downtime': step.requires_downtime,
                    'automation_possible': step.automation_possible
                }
                for step in self.implementation_steps
            ],
            'metadata': {
                'total_implementation_time_minutes': self.get_total_implementation_time(),
                'requires_downtime': self.requires_downtime(),
                'is_automatable': self.is_automatable(),
                'created_at': self.created_at.isoformat()
            }
        }


@dataclass
class RecommendationSummary:
    """Resumo agregado de recomendações"""
    total_resources_analyzed: int
    total_monthly_savings_usd: Decimal
    total_annual_savings_usd: Decimal
    high_priority_actions: int
    medium_priority_actions: int
    low_priority_actions: int
    by_action: Dict[str, int]
    by_resource_type: Dict[str, int]
    average_efficiency_score: float
    total_waste_percentage: float
    
    def get_priority_distribution(self) -> Dict[str, float]:
        """Retorna distribuição percentual por prioridade"""
        total = self.high_priority_actions + self.medium_priority_actions + self.low_priority_actions
        if total == 0:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        return {
            'high': round(self.high_priority_actions / total * 100, 1),
            'medium': round(self.medium_priority_actions / total * 100, 1),
            'low': round(self.low_priority_actions / total * 100, 1)
        }
    
    def get_savings_by_priority(self, recommendations: List[Recommendation]) -> Dict[str, Decimal]:
        """Calcula economia por prioridade"""
        savings = {'high': Decimal('0'), 'medium': Decimal('0'), 'low': Decimal('0')}
        
        for rec in recommendations:
            savings[rec.priority.value] += rec.savings.monthly_usd
        
        return savings