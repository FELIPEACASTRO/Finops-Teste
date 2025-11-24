"""
Entidade de Domínio do Recurso AWS
Representa um recurso AWS com suas métricas e configurações.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from decimal import Decimal


class ResourceType(Enum):
    """Tipos de recursos AWS suportados."""
    EC2 = "EC2"
    RDS = "RDS"
    ELB = "ELB"
    LAMBDA = "Lambda"
    EBS = "EBS"
    S3 = "S3"
    DYNAMODB = "DynamoDB"
    ELASTICACHE = "ElastiCache"


class UsagePattern(Enum):
    """Padrões de uso de recursos."""
    STEADY = "steady"
    VARIABLE = "variable"
    BATCH = "batch"
    IDLE = "idle"
    UNKNOWN = "unknown"


class Priority(Enum):
    """Níveis de prioridade das recomendações."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLevel(Enum):
    """Níveis de risco para recomendações."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MetricDataPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": round(self.value, 2)
        }


@dataclass
class ResourceMetrics:
    """Container for resource metrics."""
    cpu_utilization: List[MetricDataPoint] = field(default_factory=list)
    memory_utilization: List[MetricDataPoint] = field(default_factory=list)
    network_in: List[MetricDataPoint] = field(default_factory=list)
    network_out: List[MetricDataPoint] = field(default_factory=list)
    disk_read_ops: List[MetricDataPoint] = field(default_factory=list)
    disk_write_ops: List[MetricDataPoint] = field(default_factory=list)
    custom_metrics: Dict[str, List[MetricDataPoint]] = field(default_factory=dict)

    def get_cpu_stats(self) -> Dict[str, float]:
        """Calculate CPU statistics."""
        if not self.cpu_utilization:
            return {"mean": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}

        values = [dp.value for dp in self.cpu_utilization]
        values.sort()
        n = len(values)

        return {
            "mean": sum(values) / n,
            "p95": values[int(0.95 * n)] if n > 0 else 0.0,
            "p99": values[int(0.99 * n)] if n > 0 else 0.0,
            "max": max(values)
        }


@dataclass
class AWSResource:
    """
    Core AWS Resource entity.

    This entity represents any AWS resource that can be analyzed for cost optimization.
    It follows the Single Responsibility Principle by focusing only on resource data.
    """
    resource_id: str
    resource_type: ResourceType
    region: str
    account_id: str
    tags: Dict[str, str] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    metrics: ResourceMetrics = field(default_factory=ResourceMetrics)
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.resource_id:
            raise ValueError("resource_id cannot be empty")
        if not self.region:
            raise ValueError("region cannot be empty")
        if not self.account_id:
            raise ValueError("account_id cannot be empty")

    def get_tag(self, key: str, default: str = "") -> str:
        """Get tag value by key."""
        return self.tags.get(key, default)

    def is_production(self) -> bool:
        """Check if resource is in production environment."""
        env = self.get_tag("Environment", "").lower()
        return env in ["prod", "production", "prd"]

    def get_criticality(self) -> str:
        """Get resource criticality level."""
        return self.get_tag("Criticality", "medium").lower()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "region": self.region,
            "account_id": self.account_id,
            "tags": self.tags,
            "configuration": self.configuration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "metrics": {
                "cpu_utilization": [dp.to_dict() for dp in self.metrics.cpu_utilization],
                "memory_utilization": [dp.to_dict() for dp in self.metrics.memory_utilization],
                "network_in": [dp.to_dict() for dp in self.metrics.network_in],
                "network_out": [dp.to_dict() for dp in self.metrics.network_out],
                "disk_read_ops": [dp.to_dict() for dp in self.metrics.disk_read_ops],
                "disk_write_ops": [dp.to_dict() for dp in self.metrics.disk_write_ops],
                "custom_metrics": {
                    k: [dp.to_dict() for dp in v]
                    for k, v in self.metrics.custom_metrics.items()
                }
            }
        }


@dataclass
class CostData:
    """Cost information for resources."""
    total_cost_usd: Decimal
    period_days: int
    cost_by_service: Dict[str, Decimal] = field(default_factory=dict)
    daily_costs: List[Dict[str, Any]] = field(default_factory=list)

    def get_top_services(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top services by cost."""
        sorted_services = sorted(
            self.cost_by_service.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {
                "service": service,
                "cost_usd": float(cost),
                "percentage": float(cost / self.total_cost_usd * 100) if self.total_cost_usd > 0 else 0.0
            }
            for service, cost in sorted_services
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_cost_usd": float(self.total_cost_usd),
            "period_days": self.period_days,
            "cost_by_service": {
                service: float(cost)
                for service, cost in self.cost_by_service.items()
            },
            "daily_costs": self.daily_costs,
            "top_services": self.get_top_services()
        }


@dataclass
class OptimizationRecommendation:
    """
    Optimization recommendation entity.

    Represents a specific recommendation for cost optimization.
    """
    resource_id: str
    resource_type: ResourceType
    current_config: str
    recommended_action: str
    recommendation_details: str
    reasoning: str
    monthly_savings_usd: Decimal
    annual_savings_usd: Decimal
    savings_percentage: float
    risk_level: RiskLevel
    priority: Priority
    implementation_steps: List[str] = field(default_factory=list)
    usage_pattern: UsagePattern = UsagePattern.UNKNOWN
    confidence_score: float = 0.0

    def __post_init__(self):
        """Post-initialization validation."""
        if self.monthly_savings_usd < 0:
            raise ValueError("monthly_savings_usd cannot be negative")
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("confidence_score must be between 0 and 1")
        if not 0 <= self.savings_percentage <= 100:
            raise ValueError("savings_percentage must be between 0 and 100")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "current_config": self.current_config,
            "recommended_action": self.recommended_action,
            "recommendation_details": self.recommendation_details,
            "reasoning": self.reasoning,
            "monthly_savings_usd": float(self.monthly_savings_usd),
            "annual_savings_usd": float(self.annual_savings_usd),
            "savings_percentage": self.savings_percentage,
            "risk_level": self.risk_level.value,
            "priority": self.priority.value,
            "implementation_steps": self.implementation_steps,
            "usage_pattern": self.usage_pattern.value,
            "confidence_score": self.confidence_score
        }


@dataclass
class AnalysisReport:
    """
    Complete analysis report entity.

    Aggregates all analysis results and recommendations.
    """
    generated_at: datetime
    version: str
    model_used: str
    analysis_period_days: int
    total_resources_analyzed: int
    total_monthly_savings_usd: Decimal
    total_annual_savings_usd: Decimal
    recommendations: List[OptimizationRecommendation] = field(default_factory=list)
    cost_data: Optional[CostData] = None

    def get_recommendations_by_priority(self, priority: Priority) -> List[OptimizationRecommendation]:
        """Get recommendations filtered by priority."""
        return [r for r in self.recommendations if r.priority == priority]

    def get_high_priority_count(self) -> int:
        """Get count of high priority recommendations."""
        return len(self.get_recommendations_by_priority(Priority.HIGH))

    def get_medium_priority_count(self) -> int:
        """Get count of medium priority recommendations."""
        return len(self.get_recommendations_by_priority(Priority.MEDIUM))

    def get_low_priority_count(self) -> int:
        """Get count of low priority recommendations."""
        return len(self.get_recommendations_by_priority(Priority.LOW))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "version": self.version,
            "model_used": self.model_used,
            "analysis_period_days": self.analysis_period_days,
            "total_resources_analyzed": self.total_resources_analyzed,
            "total_monthly_savings_usd": float(self.total_monthly_savings_usd),
            "total_annual_savings_usd": float(self.total_annual_savings_usd),
            "high_priority_actions": self.get_high_priority_count(),
            "medium_priority_actions": self.get_medium_priority_count(),
            "low_priority_actions": self.get_low_priority_count(),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "cost_data": self.cost_data.to_dict() if self.cost_data else None
        }
