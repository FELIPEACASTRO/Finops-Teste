"""
Domain Entities for FinOps Platform

This module contains the core business entities following DDD principles.
Each entity represents a core business concept with identity and behavior.

Following SOLID principles:
- Single Responsibility: Each entity has one clear purpose
- Open/Closed: Extensible through composition
- Liskov Substitution: Proper inheritance hierarchy
- Interface Segregation: Focused interfaces
- Dependency Inversion: Depends on abstractions
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Protocol
from uuid import UUID, uuid4


class ResourceType(Enum):
    """Types of cloud resources for cost tracking"""
    EC2 = "ec2"
    RDS = "rds"
    S3 = "s3"
    LAMBDA = "lambda"
    ELB = "elb"
    EBS = "ebs"
    CLOUDFRONT = "cloudfront"
    ROUTE53 = "route53"
    VPC = "vpc"
    DYNAMODB = "dynamodb"


class CostCategory(Enum):
    """Categories for cost classification"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    SECURITY = "security"
    MONITORING = "monitoring"
    OTHER = "other"


class OptimizationStatus(Enum):
    """Status of optimization recommendations"""
    PENDING = "pending"
    APPLIED = "applied"
    REJECTED = "rejected"
    EXPIRED = "expired"


# Value Objects (immutable, no identity)
@dataclass(frozen=True)
class Money:
    """Value object representing monetary amounts"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def multiply(self, factor: Decimal) -> 'Money':
        return Money(self.amount * factor, self.currency)


@dataclass(frozen=True)
class TimeRange:
    """Value object for time periods"""
    start: datetime
    end: datetime
    
    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError("Start time must be before end time")
    
    @property
    def duration_days(self) -> int:
        return (self.end - self.start).days


@dataclass(frozen=True)
class ResourceMetrics:
    """Value object for resource utilization metrics"""
    cpu_utilization: float
    memory_utilization: float
    network_in: float
    network_out: float
    storage_utilization: float
    
    def __post_init__(self):
        for field_name, value in self.__dict__.items():
            if not 0 <= value <= 100:
                raise ValueError(f"{field_name} must be between 0 and 100")


# Domain Entities (have identity and lifecycle)
@dataclass
class CloudResource:
    """Core entity representing a cloud resource"""
    id: UUID = field(default_factory=uuid4)
    resource_id: str = field(default="")
    resource_type: ResourceType = field(default=ResourceType.EC2)
    name: str = field(default="")
    region: str = field(default="")
    account_id: str = field(default="")
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Business behavior
    def update_tags(self, new_tags: Dict[str, str]) -> None:
        """Update resource tags following business rules"""
        required_tags = {"Owner", "CostCenter", "Project"}
        
        # Validate required tags
        for tag in required_tags:
            if tag not in new_tags:
                raise ValueError(f"Required tag '{tag}' is missing")
        
        self.tags.update(new_tags)
        self.updated_at = datetime.utcnow()
    
    def get_cost_center(self) -> str:
        """Get cost center from tags"""
        return self.tags.get("CostCenter", "Unknown")
    
    def is_production(self) -> bool:
        """Check if resource is in production environment"""
        env = self.tags.get("Environment", "").lower()
        return env in ["prod", "production"]


@dataclass
class CostEntry:
    """Entity representing a cost entry for a resource"""
    id: UUID = field(default_factory=uuid4)
    resource_id: UUID = field(default_factory=uuid4)
    cost: Money = field(default_factory=lambda: Money(Decimal("0")))
    category: CostCategory = field(default=CostCategory.COMPUTE)
    time_range: TimeRange = field(default_factory=lambda: TimeRange(
        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
        datetime.utcnow()
    ))
    usage_metrics: Optional[ResourceMetrics] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_cost_per_hour(self) -> Money:
        """Calculate hourly cost rate"""
        hours = max(1, (self.time_range.end - self.time_range.start).total_seconds() / 3600)
        hourly_amount = self.cost.amount / Decimal(str(hours))
        return Money(hourly_amount, self.cost.currency)
    
    def is_high_cost(self, threshold: Money) -> bool:
        """Check if cost exceeds threshold"""
        return self.cost.amount > threshold.amount


@dataclass
class OptimizationRecommendation:
    """Entity for cost optimization recommendations"""
    id: UUID = field(default_factory=uuid4)
    resource_id: UUID = field(default_factory=uuid4)
    title: str = field(default="")
    description: str = field(default="")
    potential_savings: Money = field(default_factory=lambda: Money(Decimal("0")))
    confidence_score: float = field(default=0.0)
    status: OptimizationStatus = field(default=OptimizationStatus.PENDING)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
    
    def apply_recommendation(self) -> None:
        """Mark recommendation as applied"""
        if self.status != OptimizationStatus.PENDING:
            raise ValueError("Can only apply pending recommendations")
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.status = OptimizationStatus.EXPIRED
            raise ValueError("Recommendation has expired")
        
        self.status = OptimizationStatus.APPLIED
    
    def reject_recommendation(self, reason: str = "") -> None:
        """Mark recommendation as rejected"""
        if self.status != OptimizationStatus.PENDING:
            raise ValueError("Can only reject pending recommendations")
        
        self.status = OptimizationStatus.REJECTED
    
    def is_high_impact(self, threshold: Money) -> bool:
        """Check if recommendation has high financial impact"""
        return self.potential_savings.amount > threshold.amount


@dataclass
class Budget:
    """Entity for budget management"""
    id: UUID = field(default_factory=uuid4)
    name: str = field(default="")
    amount: Money = field(default_factory=lambda: Money(Decimal("0")))
    spent: Money = field(default_factory=lambda: Money(Decimal("0")))
    time_range: TimeRange = field(default_factory=lambda: TimeRange(
        datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        datetime.utcnow()
    ))
    cost_center: str = field(default="")
    alert_thresholds: List[float] = field(default_factory=lambda: [0.8, 0.9, 1.0])
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate budget utilization percentage"""
        if self.amount.amount == 0:
            return 0.0
        return float(self.spent.amount / self.amount.amount * 100)
    
    @property
    def remaining_budget(self) -> Money:
        """Calculate remaining budget"""
        remaining = self.amount.amount - self.spent.amount
        return Money(max(Decimal("0"), remaining), self.amount.currency)
    
    def add_expense(self, expense: Money) -> None:
        """Add expense to budget"""
        if expense.currency != self.spent.currency:
            raise ValueError("Expense currency must match budget currency")
        
        self.spent = self.spent.add(expense)
    
    def should_alert(self) -> List[float]:
        """Check which alert thresholds have been exceeded"""
        utilization = self.utilization_percentage / 100
        return [threshold for threshold in self.alert_thresholds if utilization >= threshold]


# Domain Services (business logic that doesn't belong to a single entity)
class CostAnalysisService:
    """Domain service for cost analysis operations"""
    
    @staticmethod
    def calculate_total_cost(cost_entries: List[CostEntry]) -> Money:
        """Calculate total cost from multiple entries"""
        if not cost_entries:
            return Money(Decimal("0"))
        
        # Assume all entries have same currency (validation should be done elsewhere)
        total = Decimal("0")
        currency = cost_entries[0].cost.currency
        
        for entry in cost_entries:
            if entry.cost.currency != currency:
                raise ValueError("All cost entries must have the same currency")
            total += entry.cost.amount
        
        return Money(total, currency)
    
    @staticmethod
    def calculate_cost_trend(cost_entries: List[CostEntry]) -> float:
        """Calculate cost trend (positive = increasing, negative = decreasing)"""
        if len(cost_entries) < 2:
            return 0.0
        
        # Sort by time
        sorted_entries = sorted(cost_entries, key=lambda x: x.time_range.start)
        
        # Compare first half with second half
        mid_point = len(sorted_entries) // 2
        first_half = sorted_entries[:mid_point]
        second_half = sorted_entries[mid_point:]
        
        first_half_avg = sum(e.cost.amount for e in first_half) / len(first_half)
        second_half_avg = sum(e.cost.amount for e in second_half) / len(second_half)
        
        if first_half_avg == 0:
            return 0.0
        
        return float((second_half_avg - first_half_avg) / first_half_avg * 100)


# Repository Interfaces (following Dependency Inversion Principle)
class ResourceRepository(Protocol):
    """Repository interface for cloud resources"""
    
    async def save(self, resource: CloudResource) -> None:
        """Save a cloud resource"""
        ...
    
    async def find_by_id(self, resource_id: UUID) -> Optional[CloudResource]:
        """Find resource by ID"""
        ...
    
    async def find_by_type(self, resource_type: ResourceType) -> List[CloudResource]:
        """Find resources by type"""
        ...
    
    async def find_by_cost_center(self, cost_center: str) -> List[CloudResource]:
        """Find resources by cost center"""
        ...


class CostRepository(Protocol):
    """Repository interface for cost entries"""
    
    async def save(self, cost_entry: CostEntry) -> None:
        """Save a cost entry"""
        ...
    
    async def find_by_resource(self, resource_id: UUID) -> List[CostEntry]:
        """Find cost entries for a resource"""
        ...
    
    async def find_by_time_range(self, time_range: TimeRange) -> List[CostEntry]:
        """Find cost entries within time range"""
        ...
    
    async def find_by_cost_center(self, cost_center: str, time_range: TimeRange) -> List[CostEntry]:
        """Find cost entries by cost center and time range"""
        ...


class OptimizationRepository(Protocol):
    """Repository interface for optimization recommendations"""
    
    async def save(self, recommendation: OptimizationRecommendation) -> None:
        """Save an optimization recommendation"""
        ...
    
    async def find_pending(self) -> List[OptimizationRecommendation]:
        """Find all pending recommendations"""
        ...
    
    async def find_by_resource(self, resource_id: UUID) -> List[OptimizationRecommendation]:
        """Find recommendations for a resource"""
        ...


class BudgetRepository(Protocol):
    """Repository interface for budgets"""
    
    async def save(self, budget: Budget) -> None:
        """Save a budget"""
        ...
    
    async def find_by_cost_center(self, cost_center: str) -> List[Budget]:
        """Find budgets by cost center"""
        ...
    
    async def find_active(self) -> List[Budget]:
        """Find all active budgets"""
        ...