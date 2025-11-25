"""
Cost Management Bounded Context
Implements DDD patterns following KNOWLEDGE_BASE.md specifications

This bounded context handles:
- Cost tracking and analysis
- Budget management and alerts
- Cost allocation and chargeback
- Forecasting and trend analysis
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Protocol
from uuid import UUID, uuid4

from .entities import Money, TimeRange


class CostAllocationStrategy(Enum):
    """Strategies for cost allocation"""
    EQUAL_SPLIT = "equal_split"
    USAGE_BASED = "usage_based"
    TAG_BASED = "tag_based"
    CUSTOM = "custom"


class ForecastModel(Enum):
    """Forecasting models for cost prediction"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    SEASONAL = "seasonal"
    ML_BASED = "ml_based"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CostForecast:
    """Value object for cost forecasting"""
    predicted_amount: Money
    confidence_interval: float
    model_used: ForecastModel
    forecast_date: datetime
    factors: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if not 0 <= self.confidence_interval <= 1:
            raise ValueError("Confidence interval must be between 0 and 1")


@dataclass(frozen=True)
class CostAllocation:
    """Value object for cost allocation"""
    cost_center: str
    allocated_amount: Money
    allocation_percentage: float
    strategy: CostAllocationStrategy
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if not 0 <= self.allocation_percentage <= 100:
            raise ValueError("Allocation percentage must be between 0 and 100")


@dataclass
class CostAlert:
    """Entity for cost alerts and notifications"""
    id: UUID = field(default_factory=uuid4)
    budget_id: UUID = field(default_factory=uuid4)
    severity: AlertSeverity = AlertSeverity.MEDIUM
    threshold_percentage: float = 80.0
    current_utilization: float = 0.0
    message: str = ""
    is_acknowledged: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None
    
    def acknowledge(self, user_id: UUID) -> None:
        """Acknowledge the alert"""
        if self.is_acknowledged:
            raise ValueError("Alert is already acknowledged")
        
        self.is_acknowledged = True
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id
    
    def is_critical(self) -> bool:
        """Check if alert is critical"""
        return self.severity == AlertSeverity.CRITICAL or self.current_utilization >= 100.0


@dataclass
class CostCenter:
    """Entity representing a cost center for allocation"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    code: str = ""
    description: str = ""
    owner_id: UUID = field(default_factory=uuid4)
    parent_id: Optional[UUID] = None
    budget_limit: Optional[Money] = None
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_over_budget(self, current_spending: Money) -> bool:
        """Check if cost center is over budget"""
        if not self.budget_limit:
            return False
        return current_spending.amount > self.budget_limit.amount
    
    def get_budget_utilization(self, current_spending: Money) -> float:
        """Calculate budget utilization percentage"""
        if not self.budget_limit or self.budget_limit.amount == 0:
            return 0.0
        return float(current_spending.amount / self.budget_limit.amount * 100)


@dataclass
class CostTrend:
    """Entity for cost trend analysis"""
    id: UUID = field(default_factory=uuid4)
    resource_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    time_range: TimeRange = field(default_factory=lambda: TimeRange(
        datetime.utcnow() - timedelta(days=30),
        datetime.utcnow()
    ))
    trend_percentage: float = 0.0
    trend_direction: str = "stable"  # increasing, decreasing, stable
    average_cost: Money = field(default_factory=lambda: Money(Decimal("0")))
    peak_cost: Money = field(default_factory=lambda: Money(Decimal("0")))
    lowest_cost: Money = field(default_factory=lambda: Money(Decimal("0")))
    volatility_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        # Determine trend direction based on percentage
        if self.trend_percentage > 5:
            self.trend_direction = "increasing"
        elif self.trend_percentage < -5:
            self.trend_direction = "decreasing"
        else:
            self.trend_direction = "stable"
    
    def is_volatile(self) -> bool:
        """Check if cost trend is volatile"""
        return self.volatility_score > 0.3


# Domain Services
class CostForecastingService:
    """Domain service for cost forecasting"""
    
    def __init__(self, historical_data_repository: 'HistoricalCostRepository'):
        self._historical_data = historical_data_repository
    
    def forecast_cost(
        self,
        resource_id: Optional[UUID] = None,
        cost_center_id: Optional[UUID] = None,
        forecast_period_days: int = 30,
        model: ForecastModel = ForecastModel.LINEAR
    ) -> CostForecast:
        """Generate cost forecast using specified model"""
        
        # Get historical data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=forecast_period_days * 2)  # Use 2x period for training
        
        historical_costs = self._historical_data.get_costs_for_period(
            start_date, end_date, resource_id, cost_center_id
        )
        
        if not historical_costs:
            return CostForecast(
                predicted_amount=Money(Decimal("0")),
                confidence_interval=0.0,
                model_used=model,
                forecast_date=datetime.utcnow()
            )
        
        # Apply forecasting model
        if model == ForecastModel.LINEAR:
            return self._linear_forecast(historical_costs, forecast_period_days)
        elif model == ForecastModel.EXPONENTIAL:
            return self._exponential_forecast(historical_costs, forecast_period_days)
        elif model == ForecastModel.SEASONAL:
            return self._seasonal_forecast(historical_costs, forecast_period_days)
        else:
            # ML-based forecasting would integrate with external ML service
            return self._ml_forecast(historical_costs, forecast_period_days)
    
    def _linear_forecast(self, historical_costs: List[Money], days: int) -> CostForecast:
        """Simple linear regression forecast"""
        if len(historical_costs) < 2:
            avg_cost = historical_costs[0] if historical_costs else Money(Decimal("0"))
            return CostForecast(
                predicted_amount=Money(avg_cost.amount * days),
                confidence_interval=0.5,
                model_used=ForecastModel.LINEAR,
                forecast_date=datetime.utcnow()
            )
        
        # Calculate trend
        daily_amounts = [cost.amount for cost in historical_costs]
        n = len(daily_amounts)
        
        # Simple linear regression
        x_sum = sum(range(n))
        y_sum = sum(daily_amounts)
        xy_sum = sum(i * amount for i, amount in enumerate(daily_amounts))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        intercept = (y_sum - slope * x_sum) / n
        
        # Predict for future period
        future_amount = intercept + slope * (n + days / 2)
        predicted_total = Money(Decimal(str(max(0, future_amount * days))))
        
        # Calculate confidence based on variance
        variance = sum((amount - (intercept + slope * i))**2 for i, amount in enumerate(daily_amounts)) / n
        confidence = max(0.1, min(0.9, 1 / (1 + float(variance) / 1000)))
        
        return CostForecast(
            predicted_amount=predicted_total,
            confidence_interval=confidence,
            model_used=ForecastModel.LINEAR,
            forecast_date=datetime.utcnow(),
            factors={"slope": float(slope), "intercept": float(intercept)}
        )
    
    def _exponential_forecast(self, historical_costs: List[Money], days: int) -> CostForecast:
        """Exponential smoothing forecast"""
        if not historical_costs:
            return CostForecast(
                predicted_amount=Money(Decimal("0")),
                confidence_interval=0.0,
                model_used=ForecastModel.EXPONENTIAL,
                forecast_date=datetime.utcnow()
            )
        
        # Simple exponential smoothing
        alpha = 0.3  # Smoothing parameter
        smoothed_values = []
        
        smoothed_values.append(historical_costs[0].amount)
        for i in range(1, len(historical_costs)):
            smoothed = alpha * historical_costs[i].amount + (1 - alpha) * smoothed_values[i-1]
            smoothed_values.append(smoothed)
        
        # Predict future value
        predicted_daily = smoothed_values[-1]
        predicted_total = Money(Decimal(str(predicted_daily * days)))
        
        return CostForecast(
            predicted_amount=predicted_total,
            confidence_interval=0.7,
            model_used=ForecastModel.EXPONENTIAL,
            forecast_date=datetime.utcnow(),
            factors={"alpha": alpha, "last_smoothed": float(predicted_daily)}
        )
    
    def _seasonal_forecast(self, historical_costs: List[Money], days: int) -> CostForecast:
        """Seasonal decomposition forecast"""
        # Simplified seasonal forecast - would use proper time series analysis in production
        if len(historical_costs) < 7:  # Need at least a week of data
            return self._linear_forecast(historical_costs, days)
        
        # Calculate weekly pattern
        weekly_pattern = []
        for day in range(7):
            day_costs = [historical_costs[i].amount for i in range(day, len(historical_costs), 7)]
            avg_day_cost = sum(day_costs) / len(day_costs) if day_costs else Decimal("0")
            weekly_pattern.append(avg_day_cost)
        
        # Apply pattern to forecast
        total_predicted = Decimal("0")
        for day in range(days):
            day_of_week = day % 7
            total_predicted += weekly_pattern[day_of_week]
        
        return CostForecast(
            predicted_amount=Money(total_predicted),
            confidence_interval=0.6,
            model_used=ForecastModel.SEASONAL,
            forecast_date=datetime.utcnow(),
            factors={"weekly_pattern": [float(x) for x in weekly_pattern]}
        )
    
    def _ml_forecast(self, historical_costs: List[Money], days: int) -> CostForecast:
        """ML-based forecast (placeholder for external ML service)"""
        # This would integrate with AWS Bedrock or other ML service
        # For now, return a sophisticated linear forecast
        return self._linear_forecast(historical_costs, days)


class CostAllocationService:
    """Domain service for cost allocation"""
    
    def allocate_costs(
        self,
        total_cost: Money,
        cost_centers: List[CostCenter],
        strategy: CostAllocationStrategy,
        allocation_rules: Dict[str, float] = None
    ) -> List[CostAllocation]:
        """Allocate costs across cost centers using specified strategy"""
        
        if not cost_centers:
            return []
        
        allocations = []
        
        if strategy == CostAllocationStrategy.EQUAL_SPLIT:
            allocation_per_center = total_cost.amount / len(cost_centers)
            percentage_per_center = 100.0 / len(cost_centers)
            
            for center in cost_centers:
                allocations.append(CostAllocation(
                    cost_center=center.code,
                    allocated_amount=Money(allocation_per_center, total_cost.currency),
                    allocation_percentage=percentage_per_center,
                    strategy=strategy
                ))
        
        elif strategy == CostAllocationStrategy.TAG_BASED and allocation_rules:
            total_weight = sum(allocation_rules.values())
            
            for center in cost_centers:
                weight = allocation_rules.get(center.code, 0)
                percentage = (weight / total_weight * 100) if total_weight > 0 else 0
                allocated_amount = total_cost.amount * Decimal(str(weight / total_weight)) if total_weight > 0 else Decimal("0")
                
                allocations.append(CostAllocation(
                    cost_center=center.code,
                    allocated_amount=Money(allocated_amount, total_cost.currency),
                    allocation_percentage=percentage,
                    strategy=strategy,
                    metadata={"weight": str(weight)}
                ))
        
        elif strategy == CostAllocationStrategy.USAGE_BASED:
            # This would integrate with actual usage metrics
            # For now, implement a simple budget-based allocation
            total_budget = sum(
                center.budget_limit.amount for center in cost_centers 
                if center.budget_limit
            )
            
            if total_budget > 0:
                for center in cost_centers:
                    if center.budget_limit:
                        percentage = float(center.budget_limit.amount / total_budget * 100)
                        allocated_amount = total_cost.amount * (center.budget_limit.amount / total_budget)
                        
                        allocations.append(CostAllocation(
                            cost_center=center.code,
                            allocated_amount=Money(allocated_amount, total_cost.currency),
                            allocation_percentage=percentage,
                            strategy=strategy,
                            metadata={"budget_based": "true"}
                        ))
            else:
                # Fallback to equal split
                return self.allocate_costs(total_cost, cost_centers, CostAllocationStrategy.EQUAL_SPLIT)
        
        return allocations


# Repository Interfaces
class HistoricalCostRepository(Protocol):
    """Repository for historical cost data"""
    
    async def get_costs_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        resource_id: Optional[UUID] = None,
        cost_center_id: Optional[UUID] = None
    ) -> List[Money]:
        """Get historical costs for specified period"""
        ...


class CostCenterRepository(Protocol):
    """Repository for cost centers"""
    
    async def save(self, cost_center: CostCenter) -> None:
        """Save cost center"""
        ...
    
    async def find_by_id(self, cost_center_id: UUID) -> Optional[CostCenter]:
        """Find cost center by ID"""
        ...
    
    async def find_all_active(self) -> List[CostCenter]:
        """Find all active cost centers"""
        ...


class CostAlertRepository(Protocol):
    """Repository for cost alerts"""
    
    async def save(self, alert: CostAlert) -> None:
        """Save cost alert"""
        ...
    
    async def find_unacknowledged(self) -> List[CostAlert]:
        """Find all unacknowledged alerts"""
        ...
    
    async def find_by_budget(self, budget_id: UUID) -> List[CostAlert]:
        """Find alerts for specific budget"""
        ...