"""
Design Patterns Implementation
Following KNOWLEDGE_BASE.md specifications for essential design patterns

Implements:
- Strategy Pattern for cost calculation algorithms
- Factory Pattern for resource creation
- Observer Pattern for notifications
- Decorator Pattern for adding behaviors
- Builder Pattern for complex object construction
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union
from uuid import UUID, uuid4

from .entities import Money, CloudResource, ResourceType


# Strategy Pattern for Cost Calculation
class CostCalculationStrategy(ABC):
    """Abstract strategy for cost calculation"""
    
    @abstractmethod
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        """Calculate cost based on resource and usage"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get strategy name for logging/debugging"""
        pass


class EC2CostStrategy(CostCalculationStrategy):
    """Cost calculation strategy for EC2 instances"""
    
    def __init__(self, pricing_data: Dict[str, Decimal]):
        self.pricing_data = pricing_data
    
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        instance_type = resource.tags.get("InstanceType", "t3.micro")
        hourly_rate = self.pricing_data.get(instance_type, Decimal("0.0116"))  # t3.micro default
        
        # Apply usage-based adjustments
        cpu_utilization = usage_metrics.get("cpu_utilization", 100.0) / 100.0
        
        # Reduce cost for low utilization (optimization opportunity)
        utilization_factor = max(0.1, cpu_utilization)  # Minimum 10% charge
        
        total_cost = hourly_rate * Decimal(str(usage_hours)) * Decimal(str(utilization_factor))
        return Money(total_cost)
    
    def get_strategy_name(self) -> str:
        return "EC2CostStrategy"


class RDSCostStrategy(CostCalculationStrategy):
    """Cost calculation strategy for RDS instances"""
    
    def __init__(self, pricing_data: Dict[str, Decimal]):
        self.pricing_data = pricing_data
    
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        instance_class = resource.tags.get("DBInstanceClass", "db.t3.micro")
        hourly_rate = self.pricing_data.get(instance_class, Decimal("0.017"))
        
        # RDS has additional storage costs
        storage_gb = usage_metrics.get("allocated_storage", 20.0)
        storage_rate = Decimal("0.10")  # per GB per month
        storage_cost = storage_rate * Decimal(str(storage_gb)) * Decimal(str(usage_hours / 730))  # 730 hours/month
        
        instance_cost = hourly_rate * Decimal(str(usage_hours))
        total_cost = instance_cost + storage_cost
        
        return Money(total_cost)
    
    def get_strategy_name(self) -> str:
        return "RDSCostStrategy"


class S3CostStrategy(CostCalculationStrategy):
    """Cost calculation strategy for S3 storage"""
    
    def __init__(self, pricing_data: Dict[str, Decimal]):
        self.pricing_data = pricing_data
    
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        storage_gb = usage_metrics.get("storage_gb", 0.0)
        requests = usage_metrics.get("requests", 0)
        
        # Storage cost
        storage_rate = self.pricing_data.get("standard_storage", Decimal("0.023"))  # per GB
        storage_cost = storage_rate * Decimal(str(storage_gb))
        
        # Request cost
        request_rate = self.pricing_data.get("requests", Decimal("0.0004"))  # per 1000 requests
        request_cost = request_rate * Decimal(str(requests / 1000))
        
        total_cost = storage_cost + request_cost
        return Money(total_cost)
    
    def get_strategy_name(self) -> str:
        return "S3CostStrategy"


class CostCalculationContext:
    """Context for cost calculation strategies"""
    
    def __init__(self):
        self._strategies: Dict[ResourceType, CostCalculationStrategy] = {}
    
    def set_strategy(self, resource_type: ResourceType, strategy: CostCalculationStrategy):
        """Set strategy for specific resource type"""
        self._strategies[resource_type] = strategy
    
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        """Calculate cost using appropriate strategy"""
        strategy = self._strategies.get(resource.resource_type)
        if not strategy:
            # Default strategy
            return Money(Decimal("1.0") * Decimal(str(usage_hours)))
        
        return strategy.calculate_cost(resource, usage_hours, usage_metrics)


# Factory Pattern for Resource Creation
class ResourceFactory(ABC):
    """Abstract factory for creating resources"""
    
    @abstractmethod
    def create_resource(self, resource_data: Dict[str, Any]) -> CloudResource:
        """Create resource from data"""
        pass


class EC2ResourceFactory(ResourceFactory):
    """Factory for creating EC2 resources"""
    
    def create_resource(self, resource_data: Dict[str, Any]) -> CloudResource:
        return CloudResource(
            resource_id=resource_data["InstanceId"],
            resource_type=ResourceType.EC2,
            name=resource_data.get("Name", f"EC2-{resource_data['InstanceId']}"),
            region=resource_data.get("Region", "us-east-1"),
            account_id=resource_data.get("AccountId", ""),
            tags={
                "InstanceType": resource_data.get("InstanceType", "t3.micro"),
                "State": resource_data.get("State", "running"),
                "LaunchTime": resource_data.get("LaunchTime", ""),
                **resource_data.get("Tags", {})
            }
        )


class RDSResourceFactory(ResourceFactory):
    """Factory for creating RDS resources"""
    
    def create_resource(self, resource_data: Dict[str, Any]) -> CloudResource:
        return CloudResource(
            resource_id=resource_data["DBInstanceIdentifier"],
            resource_type=ResourceType.RDS,
            name=resource_data.get("DBName", resource_data["DBInstanceIdentifier"]),
            region=resource_data.get("Region", "us-east-1"),
            account_id=resource_data.get("AccountId", ""),
            tags={
                "DBInstanceClass": resource_data.get("DBInstanceClass", "db.t3.micro"),
                "Engine": resource_data.get("Engine", "postgres"),
                "AllocatedStorage": str(resource_data.get("AllocatedStorage", 20)),
                "DBInstanceStatus": resource_data.get("DBInstanceStatus", "available"),
                **resource_data.get("Tags", {})
            }
        )


class ResourceFactoryRegistry:
    """Registry for resource factories"""
    
    def __init__(self):
        self._factories: Dict[str, ResourceFactory] = {}
    
    def register_factory(self, resource_type: str, factory: ResourceFactory):
        """Register factory for resource type"""
        self._factories[resource_type] = factory
    
    def create_resource(self, resource_type: str, resource_data: Dict[str, Any]) -> CloudResource:
        """Create resource using registered factory"""
        factory = self._factories.get(resource_type)
        if not factory:
            raise ValueError(f"No factory registered for resource type: {resource_type}")
        
        return factory.create_resource(resource_data)


# Observer Pattern for Notifications
class Observer(ABC):
    """Abstract observer for notifications"""
    
    @abstractmethod
    async def update(self, event: 'DomainEvent') -> None:
        """Handle domain event"""
        pass


@dataclass
class DomainEvent:
    """Base domain event"""
    event_id: UUID = field(default_factory=uuid4)
    event_type: str = ""
    aggregate_id: UUID = field(default_factory=uuid4)
    data: Dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


class CostThresholdExceededEvent(DomainEvent):
    """Event fired when cost threshold is exceeded"""
    
    def __init__(self, budget_id: UUID, current_cost: Money, threshold: Money):
        super().__init__(
            event_type="CostThresholdExceeded",
            aggregate_id=budget_id,
            data={
                "current_cost": {
                    "amount": str(current_cost.amount),
                    "currency": current_cost.currency
                },
                "threshold": {
                    "amount": str(threshold.amount),
                    "currency": threshold.currency
                },
                "utilization_percentage": float(current_cost.amount / threshold.amount * 100)
            }
        )


class EmailNotificationObserver(Observer):
    """Observer for email notifications"""
    
    def __init__(self, email_service: 'EmailService'):
        self.email_service = email_service
    
    async def update(self, event: DomainEvent) -> None:
        """Send email notification for domain events"""
        if isinstance(event, CostThresholdExceededEvent):
            await self._send_cost_alert_email(event)
    
    async def _send_cost_alert_email(self, event: CostThresholdExceededEvent) -> None:
        """Send cost alert email"""
        subject = "🚨 Cost Threshold Exceeded Alert"
        body = f"""
        Budget Alert: Cost threshold has been exceeded
        
        Current Cost: {event.data['current_cost']['amount']} {event.data['current_cost']['currency']}
        Threshold: {event.data['threshold']['amount']} {event.data['threshold']['currency']}
        Utilization: {event.data['utilization_percentage']:.1f}%
        
        Time: {event.occurred_at.isoformat()}
        """
        
        await self.email_service.send_alert_email(subject, body)


class SlackNotificationObserver(Observer):
    """Observer for Slack notifications"""
    
    def __init__(self, slack_service: 'SlackService'):
        self.slack_service = slack_service
    
    async def update(self, event: DomainEvent) -> None:
        """Send Slack notification for domain events"""
        if isinstance(event, CostThresholdExceededEvent):
            await self._send_cost_alert_slack(event)
    
    async def _send_cost_alert_slack(self, event: CostThresholdExceededEvent) -> None:
        """Send cost alert to Slack"""
        message = f"""
        🚨 *Cost Threshold Exceeded*
        
        Current Cost: *{event.data['current_cost']['amount']} {event.data['current_cost']['currency']}*
        Threshold: {event.data['threshold']['amount']} {event.data['threshold']['currency']}
        Utilization: *{event.data['utilization_percentage']:.1f}%*
        """
        
        await self.slack_service.send_message("#finops-alerts", message)


class EventPublisher:
    """Publisher for domain events"""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def subscribe(self, observer: Observer) -> None:
        """Subscribe observer to events"""
        self._observers.append(observer)
    
    def unsubscribe(self, observer: Observer) -> None:
        """Unsubscribe observer from events"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish event to all observers"""
        for observer in self._observers:
            try:
                await observer.update(event)
            except Exception as e:
                # Log error but don't stop other observers
                print(f"Error in observer {type(observer).__name__}: {e}")


# Decorator Pattern for Adding Behaviors
class CostCalculationDecorator(CostCalculationStrategy):
    """Base decorator for cost calculation strategies"""
    
    def __init__(self, strategy: CostCalculationStrategy):
        self._strategy = strategy
    
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        return self._strategy.calculate_cost(resource, usage_hours, usage_metrics)
    
    def get_strategy_name(self) -> str:
        return self._strategy.get_strategy_name()


class DiscountDecorator(CostCalculationDecorator):
    """Decorator for applying discounts"""
    
    def __init__(self, strategy: CostCalculationStrategy, discount_percentage: float):
        super().__init__(strategy)
        self.discount_percentage = discount_percentage
    
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        base_cost = super().calculate_cost(resource, usage_hours, usage_metrics)
        discount_amount = base_cost.amount * Decimal(str(self.discount_percentage / 100))
        discounted_cost = base_cost.amount - discount_amount
        
        return Money(max(Decimal("0"), discounted_cost), base_cost.currency)
    
    def get_strategy_name(self) -> str:
        return f"{super().get_strategy_name()}+Discount({self.discount_percentage}%)"


class ReservedInstanceDecorator(CostCalculationDecorator):
    """Decorator for reserved instance pricing"""
    
    def __init__(self, strategy: CostCalculationStrategy, reserved_discount: float = 0.3):
        super().__init__(strategy)
        self.reserved_discount = reserved_discount
    
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        base_cost = super().calculate_cost(resource, usage_hours, usage_metrics)
        
        # Check if resource is eligible for reserved instance pricing
        if self._is_eligible_for_reserved_pricing(resource, usage_hours):
            discount_amount = base_cost.amount * Decimal(str(self.reserved_discount))
            reserved_cost = base_cost.amount - discount_amount
            return Money(reserved_cost, base_cost.currency)
        
        return base_cost
    
    def _is_eligible_for_reserved_pricing(self, resource: CloudResource, usage_hours: float) -> bool:
        """Check if resource is eligible for reserved instance pricing"""
        # Resource should run for significant hours to benefit from RI
        return usage_hours >= 24 * 30 * 0.7  # 70% of a month
    
    def get_strategy_name(self) -> str:
        return f"{super().get_strategy_name()}+ReservedInstance"


class TaxDecorator(CostCalculationDecorator):
    """Decorator for applying taxes"""
    
    def __init__(self, strategy: CostCalculationStrategy, tax_rate: float):
        super().__init__(strategy)
        self.tax_rate = tax_rate
    
    def calculate_cost(
        self,
        resource: CloudResource,
        usage_hours: float,
        usage_metrics: Dict[str, float]
    ) -> Money:
        base_cost = super().calculate_cost(resource, usage_hours, usage_metrics)
        tax_amount = base_cost.amount * Decimal(str(self.tax_rate / 100))
        total_cost = base_cost.amount + tax_amount
        
        return Money(total_cost, base_cost.currency)
    
    def get_strategy_name(self) -> str:
        return f"{super().get_strategy_name()}+Tax({self.tax_rate}%)"


# Builder Pattern for Complex Object Construction
class CostAnalysisReportBuilder:
    """Builder for creating complex cost analysis reports"""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> 'CostAnalysisReportBuilder':
        """Reset builder to initial state"""
        self._report_data = {
            "id": uuid4(),
            "title": "",
            "description": "",
            "time_range": None,
            "cost_centers": [],
            "resources": [],
            "total_cost": Money(Decimal("0")),
            "forecasts": [],
            "recommendations": [],
            "charts": [],
            "filters": {},
            "metadata": {},
            "created_at": datetime.utcnow()
        }
        return self
    
    def set_title(self, title: str) -> 'CostAnalysisReportBuilder':
        """Set report title"""
        self._report_data["title"] = title
        return self
    
    def set_description(self, description: str) -> 'CostAnalysisReportBuilder':
        """Set report description"""
        self._report_data["description"] = description
        return self
    
    def set_time_range(self, start: datetime, end: datetime) -> 'CostAnalysisReportBuilder':
        """Set report time range"""
        from .entities import TimeRange
        self._report_data["time_range"] = TimeRange(start, end)
        return self
    
    def add_cost_center(self, cost_center: str) -> 'CostAnalysisReportBuilder':
        """Add cost center to report"""
        self._report_data["cost_centers"].append(cost_center)
        return self
    
    def add_resource(self, resource: CloudResource) -> 'CostAnalysisReportBuilder':
        """Add resource to report"""
        self._report_data["resources"].append(resource)
        return self
    
    def set_total_cost(self, total_cost: Money) -> 'CostAnalysisReportBuilder':
        """Set total cost"""
        self._report_data["total_cost"] = total_cost
        return self
    
    def add_forecast(self, forecast: Dict[str, Any]) -> 'CostAnalysisReportBuilder':
        """Add forecast data"""
        self._report_data["forecasts"].append(forecast)
        return self
    
    def add_recommendation(self, recommendation: Dict[str, Any]) -> 'CostAnalysisReportBuilder':
        """Add optimization recommendation"""
        self._report_data["recommendations"].append(recommendation)
        return self
    
    def add_chart(self, chart_type: str, chart_data: Dict[str, Any]) -> 'CostAnalysisReportBuilder':
        """Add chart to report"""
        self._report_data["charts"].append({
            "type": chart_type,
            "data": chart_data,
            "id": str(uuid4())
        })
        return self
    
    def set_filters(self, filters: Dict[str, Any]) -> 'CostAnalysisReportBuilder':
        """Set report filters"""
        self._report_data["filters"] = filters
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'CostAnalysisReportBuilder':
        """Add metadata to report"""
        self._report_data["metadata"][key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the final report"""
        # Validate required fields
        if not self._report_data["title"]:
            raise ValueError("Report title is required")
        
        if not self._report_data["time_range"]:
            raise ValueError("Report time range is required")
        
        # Calculate summary statistics
        self._report_data["summary"] = {
            "total_resources": len(self._report_data["resources"]),
            "total_cost_centers": len(self._report_data["cost_centers"]),
            "total_forecasts": len(self._report_data["forecasts"]),
            "total_recommendations": len(self._report_data["recommendations"]),
            "potential_savings": sum(
                rec.get("potential_savings", 0) 
                for rec in self._report_data["recommendations"]
            )
        }
        
        return self._report_data.copy()


# External Service Interfaces (for dependency injection)
class EmailService(Protocol):
    """Interface for email service"""
    
    async def send_alert_email(self, subject: str, body: str) -> None:
        """Send alert email"""
        ...


class SlackService(Protocol):
    """Interface for Slack service"""
    
    async def send_message(self, channel: str, message: str) -> None:
        """Send message to Slack channel"""
        ...