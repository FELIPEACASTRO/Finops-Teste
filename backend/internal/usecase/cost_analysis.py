"""
Cost Analysis Use Cases

This module implements the application layer use cases for cost analysis,
following Clean Architecture principles. Use cases orchestrate the flow
of data to and from entities, and direct those entities to use their
business rules to achieve the goals of the use case.

Following SOLID principles and Clean Architecture:
- Independent of frameworks, UI, database
- Testable in isolation
- Independent of external agencies
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Protocol
from uuid import UUID

from ..domain.entities import (
    Budget,
    CloudResource,
    CostAnalysisService,
    CostEntry,
    Money,
    OptimizationRecommendation,
    ResourceType,
    TimeRange,
    BudgetRepository,
    CostRepository,
    OptimizationRepository,
    ResourceRepository,
)


# Input/Output DTOs for use cases
@dataclass
class CostAnalysisRequest:
    """Request DTO for cost analysis"""
    resource_ids: Optional[List[UUID]] = None
    cost_center: Optional[str] = None
    time_range: Optional[TimeRange] = None
    resource_type: Optional[ResourceType] = None


@dataclass
class CostAnalysisResponse:
    """Response DTO for cost analysis"""
    total_cost: Money
    cost_by_resource: Dict[UUID, Money]
    cost_by_category: Dict[str, Money]
    cost_trend_percentage: float
    period_comparison: Dict[str, Money]
    top_cost_resources: List[Dict[str, any]]


@dataclass
class OptimizationRequest:
    """Request DTO for optimization analysis"""
    resource_ids: Optional[List[UUID]] = None
    cost_center: Optional[str] = None
    min_savings_threshold: Money = Money(Decimal("10.00"))
    confidence_threshold: float = 0.7


@dataclass
class OptimizationResponse:
    """Response DTO for optimization recommendations"""
    recommendations: List[OptimizationRecommendation]
    total_potential_savings: Money
    high_impact_count: int
    average_confidence: float


@dataclass
class BudgetAnalysisRequest:
    """Request DTO for budget analysis"""
    cost_center: Optional[str] = None
    time_range: Optional[TimeRange] = None


@dataclass
class BudgetAnalysisResponse:
    """Response DTO for budget analysis"""
    budgets: List[Budget]
    total_allocated: Money
    total_spent: Money
    utilization_percentage: float
    alerts: List[Dict[str, any]]


# External Service Interfaces (following Dependency Inversion)
class CloudMetricsService(Protocol):
    """Interface for cloud metrics collection"""
    
    async def get_resource_metrics(self, resource_id: str, time_range: TimeRange) -> Dict[str, float]:
        """Get utilization metrics for a resource"""
        ...
    
    async def get_cost_data(self, resource_id: str, time_range: TimeRange) -> List[Dict[str, any]]:
        """Get cost data for a resource"""
        ...


class NotificationService(Protocol):
    """Interface for sending notifications"""
    
    async def send_budget_alert(self, budget: Budget, threshold: float) -> None:
        """Send budget alert notification"""
        ...
    
    async def send_optimization_report(self, recommendations: List[OptimizationRecommendation]) -> None:
        """Send optimization recommendations"""
        ...


class MLPredictionService(Protocol):
    """Interface for ML-based predictions"""
    
    async def predict_cost_trend(self, historical_data: List[CostEntry]) -> Dict[str, float]:
        """Predict future cost trends"""
        ...
    
    async def generate_optimization_recommendations(self, resource: CloudResource, metrics: Dict[str, float]) -> List[OptimizationRecommendation]:
        """Generate ML-based optimization recommendations"""
        ...


# Use Case Implementations
class CostAnalysisUseCase:
    """Use case for comprehensive cost analysis"""
    
    def __init__(
        self,
        cost_repository: CostRepository,
        resource_repository: ResourceRepository,
        metrics_service: CloudMetricsService,
    ):
        self._cost_repository = cost_repository
        self._resource_repository = resource_repository
        self._metrics_service = metrics_service
    
    async def execute(self, request: CostAnalysisRequest) -> CostAnalysisResponse:
        """Execute cost analysis use case"""
        
        # Set default time range if not provided
        if not request.time_range:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            request.time_range = TimeRange(start_date, end_date)
        
        # Get cost entries based on request criteria
        cost_entries = await self._get_cost_entries(request)
        
        # Calculate total cost
        total_cost = CostAnalysisService.calculate_total_cost(cost_entries)
        
        # Calculate cost by resource
        cost_by_resource = self._calculate_cost_by_resource(cost_entries)
        
        # Calculate cost by category
        cost_by_category = self._calculate_cost_by_category(cost_entries)
        
        # Calculate cost trend
        cost_trend = CostAnalysisService.calculate_cost_trend(cost_entries)
        
        # Calculate period comparison
        period_comparison = await self._calculate_period_comparison(request)
        
        # Get top cost resources
        top_cost_resources = await self._get_top_cost_resources(cost_by_resource)
        
        return CostAnalysisResponse(
            total_cost=total_cost,
            cost_by_resource=cost_by_resource,
            cost_by_category=cost_by_category,
            cost_trend_percentage=cost_trend,
            period_comparison=period_comparison,
            top_cost_resources=top_cost_resources,
        )
    
    async def _get_cost_entries(self, request: CostAnalysisRequest) -> List[CostEntry]:
        """Get cost entries based on request criteria"""
        if request.cost_center:
            return await self._cost_repository.find_by_cost_center(
                request.cost_center, request.time_range
            )
        elif request.resource_ids:
            all_entries = []
            for resource_id in request.resource_ids:
                entries = await self._cost_repository.find_by_resource(resource_id)
                # Filter by time range
                filtered_entries = [
                    entry for entry in entries
                    if self._is_in_time_range(entry, request.time_range)
                ]
                all_entries.extend(filtered_entries)
            return all_entries
        else:
            return await self._cost_repository.find_by_time_range(request.time_range)
    
    def _is_in_time_range(self, cost_entry: CostEntry, time_range: TimeRange) -> bool:
        """Check if cost entry is within time range"""
        return (cost_entry.time_range.start >= time_range.start and 
                cost_entry.time_range.end <= time_range.end)
    
    def _calculate_cost_by_resource(self, cost_entries: List[CostEntry]) -> Dict[UUID, Money]:
        """Calculate total cost by resource"""
        cost_by_resource = {}
        for entry in cost_entries:
            if entry.resource_id not in cost_by_resource:
                cost_by_resource[entry.resource_id] = entry.cost
            else:
                cost_by_resource[entry.resource_id] = cost_by_resource[entry.resource_id].add(entry.cost)
        return cost_by_resource
    
    def _calculate_cost_by_category(self, cost_entries: List[CostEntry]) -> Dict[str, Money]:
        """Calculate total cost by category"""
        cost_by_category = {}
        for entry in cost_entries:
            category = entry.category.value
            if category not in cost_by_category:
                cost_by_category[category] = entry.cost
            else:
                cost_by_category[category] = cost_by_category[category].add(entry.cost)
        return cost_by_category
    
    async def _calculate_period_comparison(self, request: CostAnalysisRequest) -> Dict[str, Money]:
        """Calculate cost comparison with previous period"""
        current_period = request.time_range
        duration = current_period.end - current_period.start
        
        # Previous period with same duration
        previous_start = current_period.start - duration
        previous_end = current_period.start
        previous_period = TimeRange(previous_start, previous_end)
        
        # Get previous period data
        previous_request = CostAnalysisRequest(
            resource_ids=request.resource_ids,
            cost_center=request.cost_center,
            time_range=previous_period,
            resource_type=request.resource_type,
        )
        
        previous_entries = await self._get_cost_entries(previous_request)
        previous_total = CostAnalysisService.calculate_total_cost(previous_entries)
        
        return {
            "previous_period": previous_total,
            "current_period": CostAnalysisService.calculate_total_cost(
                await self._get_cost_entries(request)
            ),
        }
    
    async def _get_top_cost_resources(self, cost_by_resource: Dict[UUID, Money]) -> List[Dict[str, any]]:
        """Get top 10 highest cost resources with details"""
        # Sort by cost amount
        sorted_resources = sorted(
            cost_by_resource.items(),
            key=lambda x: x[1].amount,
            reverse=True
        )[:10]
        
        top_resources = []
        for resource_id, cost in sorted_resources:
            resource = await self._resource_repository.find_by_id(resource_id)
            if resource:
                top_resources.append({
                    "resource_id": resource_id,
                    "resource_name": resource.name,
                    "resource_type": resource.resource_type.value,
                    "cost": cost,
                    "cost_center": resource.get_cost_center(),
                })
        
        return top_resources


class OptimizationUseCase:
    """Use case for generating and managing optimization recommendations"""
    
    def __init__(
        self,
        optimization_repository: OptimizationRepository,
        resource_repository: ResourceRepository,
        cost_repository: CostRepository,
        metrics_service: CloudMetricsService,
        ml_service: MLPredictionService,
        notification_service: NotificationService,
    ):
        self._optimization_repository = optimization_repository
        self._resource_repository = resource_repository
        self._cost_repository = cost_repository
        self._metrics_service = metrics_service
        self._ml_service = ml_service
        self._notification_service = notification_service
    
    async def generate_recommendations(self, request: OptimizationRequest) -> OptimizationResponse:
        """Generate optimization recommendations"""
        
        # Get resources to analyze
        resources = await self._get_resources_for_optimization(request)
        
        all_recommendations = []
        
        for resource in resources:
            # Get resource metrics
            time_range = TimeRange(
                datetime.utcnow() - timedelta(days=7),
                datetime.utcnow()
            )
            metrics = await self._metrics_service.get_resource_metrics(
                resource.resource_id, time_range
            )
            
            # Generate ML-based recommendations
            ml_recommendations = await self._ml_service.generate_optimization_recommendations(
                resource, metrics
            )
            
            # Filter by confidence threshold
            filtered_recommendations = [
                rec for rec in ml_recommendations
                if rec.confidence_score >= request.confidence_threshold
                and rec.potential_savings.amount >= request.min_savings_threshold.amount
            ]
            
            all_recommendations.extend(filtered_recommendations)
        
        # Save recommendations
        for recommendation in all_recommendations:
            await self._optimization_repository.save(recommendation)
        
        # Calculate response metrics
        total_savings = Money(
            sum(rec.potential_savings.amount for rec in all_recommendations),
            "USD"
        )
        
        high_impact_threshold = Money(Decimal("100.00"))
        high_impact_count = sum(
            1 for rec in all_recommendations
            if rec.is_high_impact(high_impact_threshold)
        )
        
        average_confidence = (
            sum(rec.confidence_score for rec in all_recommendations) / len(all_recommendations)
            if all_recommendations else 0.0
        )
        
        # Send notification if there are high-impact recommendations
        if high_impact_count > 0:
            await self._notification_service.send_optimization_report(all_recommendations)
        
        return OptimizationResponse(
            recommendations=all_recommendations,
            total_potential_savings=total_savings,
            high_impact_count=high_impact_count,
            average_confidence=average_confidence,
        )
    
    async def apply_recommendation(self, recommendation_id: UUID) -> None:
        """Apply an optimization recommendation"""
        # This would typically integrate with cloud provider APIs
        # to actually implement the optimization
        pass
    
    async def _get_resources_for_optimization(self, request: OptimizationRequest) -> List[CloudResource]:
        """Get resources that need optimization analysis"""
        if request.resource_ids:
            resources = []
            for resource_id in request.resource_ids:
                resource = await self._resource_repository.find_by_id(resource_id)
                if resource:
                    resources.append(resource)
            return resources
        elif request.cost_center:
            return await self._resource_repository.find_by_cost_center(request.cost_center)
        else:
            # Get all resources (this might need pagination in real implementation)
            all_resources = []
            for resource_type in ResourceType:
                resources = await self._resource_repository.find_by_type(resource_type)
                all_resources.extend(resources)
            return all_resources


class BudgetManagementUseCase:
    """Use case for budget management and monitoring"""
    
    def __init__(
        self,
        budget_repository: BudgetRepository,
        cost_repository: CostRepository,
        notification_service: NotificationService,
    ):
        self._budget_repository = budget_repository
        self._cost_repository = cost_repository
        self._notification_service = notification_service
    
    async def analyze_budgets(self, request: BudgetAnalysisRequest) -> BudgetAnalysisResponse:
        """Analyze budget utilization and generate alerts"""
        
        # Get budgets
        if request.cost_center:
            budgets = await self._budget_repository.find_by_cost_center(request.cost_center)
        else:
            budgets = await self._budget_repository.find_active()
        
        # Update budget spending
        for budget in budgets:
            await self._update_budget_spending(budget, request.time_range)
        
        # Calculate totals
        total_allocated = Money(
            sum(budget.amount.amount for budget in budgets),
            "USD" if budgets else "USD"
        )
        
        total_spent = Money(
            sum(budget.spent.amount for budget in budgets),
            "USD" if budgets else "USD"
        )
        
        utilization_percentage = (
            float(total_spent.amount / total_allocated.amount * 100)
            if total_allocated.amount > 0 else 0.0
        )
        
        # Generate alerts
        alerts = []
        for budget in budgets:
            exceeded_thresholds = budget.should_alert()
            for threshold in exceeded_thresholds:
                alert = {
                    "budget_id": budget.id,
                    "budget_name": budget.name,
                    "cost_center": budget.cost_center,
                    "threshold": threshold,
                    "utilization": budget.utilization_percentage,
                    "severity": self._get_alert_severity(threshold),
                }
                alerts.append(alert)
                
                # Send notification
                await self._notification_service.send_budget_alert(budget, threshold)
        
        return BudgetAnalysisResponse(
            budgets=budgets,
            total_allocated=total_allocated,
            total_spent=total_spent,
            utilization_percentage=utilization_percentage,
            alerts=alerts,
        )
    
    async def _update_budget_spending(self, budget: Budget, time_range: Optional[TimeRange]) -> None:
        """Update budget with actual spending"""
        if not time_range:
            time_range = budget.time_range
        
        # Get cost entries for the budget's cost center
        cost_entries = await self._cost_repository.find_by_cost_center(
            budget.cost_center, time_range
        )
        
        # Calculate total spending
        total_spent = CostAnalysisService.calculate_total_cost(cost_entries)
        budget.spent = total_spent
        
        # Save updated budget
        await self._budget_repository.save(budget)
    
    def _get_alert_severity(self, threshold: float) -> str:
        """Get alert severity based on threshold"""
        if threshold >= 1.0:
            return "critical"
        elif threshold >= 0.9:
            return "high"
        elif threshold >= 0.8:
            return "medium"
        else:
            return "low"


# Factory for creating use cases with dependencies
class UseCaseFactory:
    """Factory for creating use cases with proper dependency injection"""
    
    def __init__(
        self,
        cost_repository: CostRepository,
        resource_repository: ResourceRepository,
        optimization_repository: OptimizationRepository,
        budget_repository: BudgetRepository,
        metrics_service: CloudMetricsService,
        ml_service: MLPredictionService,
        notification_service: NotificationService,
    ):
        self._cost_repository = cost_repository
        self._resource_repository = resource_repository
        self._optimization_repository = optimization_repository
        self._budget_repository = budget_repository
        self._metrics_service = metrics_service
        self._ml_service = ml_service
        self._notification_service = notification_service
    
    def create_cost_analysis_use_case(self) -> CostAnalysisUseCase:
        """Create cost analysis use case"""
        return CostAnalysisUseCase(
            self._cost_repository,
            self._resource_repository,
            self._metrics_service,
        )
    
    def create_optimization_use_case(self) -> OptimizationUseCase:
        """Create optimization use case"""
        return OptimizationUseCase(
            self._optimization_repository,
            self._resource_repository,
            self._cost_repository,
            self._metrics_service,
            self._ml_service,
            self._notification_service,
        )
    
    def create_budget_management_use_case(self) -> BudgetManagementUseCase:
        """Create budget management use case"""
        return BudgetManagementUseCase(
            self._budget_repository,
            self._cost_repository,
            self._notification_service,
        )