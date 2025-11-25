"""
Budget Management Controller

This module implements the HTTP interface adapters for budget management operations.
Handles budget creation, monitoring, alerts, and reporting.

Following Clean Architecture and SOLID principles:
- Single Responsibility: Only handles HTTP concerns for budget management
- Open/Closed: Extensible through composition
- Dependency Inversion: Depends on abstractions (use cases)
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator

from ..domain.entities import Money, TimeRange
from ..usecase.cost_analysis import (
    BudgetAnalysisRequest,
    BudgetAnalysisResponse,
    BudgetManagementUseCase,
    UseCaseFactory,
)


# Request/Response DTOs
class CreateBudgetRequestDTO(BaseModel):
    """DTO for creating a new budget"""
    name: str = Field(..., description="Budget name", min_length=1, max_length=100)
    amount: Decimal = Field(..., description="Budget amount", gt=0)
    currency: str = Field(default="USD", description="Currency code", min_length=3, max_length=3)
    cost_center: str = Field(..., description="Cost center", min_length=1, max_length=50)
    start_date: datetime = Field(..., description="Budget start date")
    end_date: datetime = Field(..., description="Budget end date")
    alert_thresholds: List[float] = Field(
        default=[0.8, 0.9, 1.0],
        description="Alert thresholds as percentages (0.0-1.0)"
    )
    
    @validator('end_date')
    def end_date_must_be_after_start(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('alert_thresholds')
    def validate_thresholds(cls, v):
        if not all(0.0 <= threshold <= 1.0 for threshold in v):
            raise ValueError('Alert thresholds must be between 0.0 and 1.0')
        return sorted(v)  # Ensure thresholds are sorted
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Q4 2024 Engineering Budget",
                "amount": "50000.00",
                "currency": "USD",
                "cost_center": "engineering",
                "start_date": "2024-10-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "alert_thresholds": [0.75, 0.9, 1.0]
            }
        }


class UpdateBudgetRequestDTO(BaseModel):
    """DTO for updating an existing budget"""
    name: Optional[str] = Field(None, description="Budget name", min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, description="Budget amount", gt=0)
    alert_thresholds: Optional[List[float]] = Field(None, description="Alert thresholds")
    
    @validator('alert_thresholds')
    def validate_thresholds(cls, v):
        if v is not None and not all(0.0 <= threshold <= 1.0 for threshold in v):
            raise ValueError('Alert thresholds must be between 0.0 and 1.0')
        return sorted(v) if v else v


class BudgetDTO(BaseModel):
    """DTO for budget information"""
    id: UUID
    name: str
    amount: Dict[str, str]  # {"amount": "50000.00", "currency": "USD"}
    spent: Dict[str, str]
    remaining: Dict[str, str]
    utilization_percentage: float
    cost_center: str
    time_range: Dict[str, datetime]  # {"start": datetime, "end": datetime}
    alert_thresholds: List[float]
    status: str  # "on_track", "warning", "over_budget"
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Q4 2024 Engineering Budget",
                "amount": {"amount": "50000.00", "currency": "USD"},
                "spent": {"amount": "37500.00", "currency": "USD"},
                "remaining": {"amount": "12500.00", "currency": "USD"},
                "utilization_percentage": 75.0,
                "cost_center": "engineering",
                "status": "warning"
            }
        }


class BudgetAlertDTO(BaseModel):
    """DTO for budget alert information"""
    budget_id: UUID
    budget_name: str
    cost_center: str
    threshold: float
    utilization: float
    severity: str  # "low", "medium", "high", "critical"
    message: str
    triggered_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "budget_id": "123e4567-e89b-12d3-a456-426614174000",
                "budget_name": "Q4 2024 Engineering Budget",
                "cost_center": "engineering",
                "threshold": 0.9,
                "utilization": 92.5,
                "severity": "high",
                "message": "Budget utilization has exceeded 90% threshold",
                "triggered_at": "2024-11-25T21:45:00Z"
            }
        }


class BudgetAnalysisResponseDTO(BaseModel):
    """DTO for budget analysis response"""
    budgets: List[BudgetDTO]
    total_allocated: Dict[str, str]
    total_spent: Dict[str, str]
    utilization_percentage: float
    alerts: List[BudgetAlertDTO]
    summary: Dict[str, int]  # Count by status
    
    class Config:
        schema_extra = {
            "example": {
                "total_allocated": {"amount": "150000.00", "currency": "USD"},
                "total_spent": {"amount": "112500.00", "currency": "USD"},
                "utilization_percentage": 75.0,
                "summary": {
                    "on_track": 2,
                    "warning": 1,
                    "over_budget": 0
                }
            }
        }


class BudgetForecastDTO(BaseModel):
    """DTO for budget forecast"""
    budget_id: UUID
    current_utilization: float
    projected_utilization: float
    projected_end_date_utilization: float
    forecast_accuracy: float
    recommendations: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "budget_id": "123e4567-e89b-12d3-a456-426614174000",
                "current_utilization": 75.0,
                "projected_utilization": 95.0,
                "projected_end_date_utilization": 110.0,
                "forecast_accuracy": 0.85,
                "recommendations": [
                    "Consider increasing budget by 10%",
                    "Review spending patterns for optimization opportunities"
                ]
            }
        }


# Controller Implementation
class BudgetController:
    """Controller for budget management operations"""
    
    def __init__(self, use_case_factory: UseCaseFactory):
        self._use_case_factory = use_case_factory
        self.router = APIRouter(prefix="/api/v1/budgets", tags=["Budget Management"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        
        @self.router.post(
            "/",
            response_model=BudgetDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Create budget",
            description="Create a new budget for cost tracking and alerts"
        )
        async def create_budget(request: CreateBudgetRequestDTO) -> BudgetDTO:
            """Create a new budget"""
            try:
                # This would typically call a use case to create the budget
                # Placeholder implementation
                budget_id = UUID("123e4567-e89b-12d3-a456-426614174000")
                
                return BudgetDTO(
                    id=budget_id,
                    name=request.name,
                    amount={"amount": str(request.amount), "currency": request.currency},
                    spent={"amount": "0.00", "currency": request.currency},
                    remaining={"amount": str(request.amount), "currency": request.currency},
                    utilization_percentage=0.0,
                    cost_center=request.cost_center,
                    time_range={"start": request.start_date, "end": request.end_date},
                    alert_thresholds=request.alert_thresholds,
                    status="on_track",
                    created_at=datetime.utcnow()
                )
                
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": str(e), "error_code": "VALIDATION_ERROR"}
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to create budget", "error_code": "CREATION_ERROR"}
                )
        
        @self.router.get(
            "/",
            response_model=List[BudgetDTO],
            summary="Get budgets",
            description="Retrieve budgets with optional filtering"
        )
        async def get_budgets(
            cost_center: Optional[str] = Query(None, description="Filter by cost center"),
            status_filter: Optional[str] = Query(None, description="Filter by status"),
            active_only: bool = Query(True, description="Show only active budgets")
        ) -> List[BudgetDTO]:
            """Get budgets with filtering options"""
            try:
                # Placeholder implementation
                return []
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to retrieve budgets", "error_code": "RETRIEVAL_ERROR"}
                )
        
        @self.router.get(
            "/{budget_id}",
            response_model=BudgetDTO,
            summary="Get budget by ID",
            description="Retrieve a specific budget by its ID"
        )
        async def get_budget(budget_id: UUID) -> BudgetDTO:
            """Get budget by ID"""
            try:
                # Placeholder implementation
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Budget not found", "error_code": "NOT_FOUND"}
                )
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to retrieve budget", "error_code": "RETRIEVAL_ERROR"}
                )
        
        @self.router.put(
            "/{budget_id}",
            response_model=BudgetDTO,
            summary="Update budget",
            description="Update an existing budget"
        )
        async def update_budget(
            budget_id: UUID,
            request: UpdateBudgetRequestDTO
        ) -> BudgetDTO:
            """Update an existing budget"""
            try:
                # This would call a use case to update the budget
                # Placeholder implementation
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Budget not found", "error_code": "NOT_FOUND"}
                )
                
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": str(e), "error_code": "VALIDATION_ERROR"}
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to update budget", "error_code": "UPDATE_ERROR"}
                )
        
        @self.router.delete(
            "/{budget_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete budget",
            description="Delete a budget"
        )
        async def delete_budget(budget_id: UUID):
            """Delete a budget"""
            try:
                # This would call a use case to delete the budget
                # Placeholder implementation
                pass
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to delete budget", "error_code": "DELETION_ERROR"}
                )
        
        @self.router.post(
            "/analyze",
            response_model=BudgetAnalysisResponseDTO,
            summary="Analyze budgets",
            description="Perform comprehensive budget analysis with alerts"
        )
        async def analyze_budgets(
            cost_center: Optional[str] = Query(None, description="Filter by cost center")
        ) -> BudgetAnalysisResponseDTO:
            """Analyze budgets and generate alerts"""
            try:
                # Create analysis request
                request = BudgetAnalysisRequest(cost_center=cost_center)
                
                # Execute use case
                use_case = self._use_case_factory.create_budget_management_use_case()
                response = await use_case.analyze_budgets(request)
                
                # Convert to DTO
                return self._convert_budget_analysis_to_dto(response)
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to analyze budgets", "error_code": "ANALYSIS_ERROR"}
                )
        
        @self.router.get(
            "/{budget_id}/forecast",
            response_model=BudgetForecastDTO,
            summary="Get budget forecast",
            description="Get budget utilization forecast and recommendations"
        )
        async def get_budget_forecast(budget_id: UUID) -> BudgetForecastDTO:
            """Get budget forecast"""
            try:
                # This would call a forecasting service
                # Placeholder implementation
                return BudgetForecastDTO(
                    budget_id=budget_id,
                    current_utilization=75.0,
                    projected_utilization=95.0,
                    projected_end_date_utilization=110.0,
                    forecast_accuracy=0.85,
                    recommendations=[
                        "Consider increasing budget by 10%",
                        "Review spending patterns for optimization opportunities"
                    ]
                )
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to generate forecast", "error_code": "FORECAST_ERROR"}
                )
        
        @self.router.get(
            "/alerts/active",
            response_model=List[BudgetAlertDTO],
            summary="Get active budget alerts",
            description="Retrieve all active budget alerts"
        )
        async def get_active_alerts() -> List[BudgetAlertDTO]:
            """Get active budget alerts"""
            try:
                # This would call a use case to get active alerts
                # Placeholder implementation
                return []
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to retrieve alerts", "error_code": "ALERTS_ERROR"}
                )
        
        @self.router.get(
            "/health",
            summary="Health check",
            description="Check if budget service is healthy"
        )
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "budget-management",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
    
    def _convert_budget_analysis_to_dto(
        self,
        domain_response: BudgetAnalysisResponse
    ) -> BudgetAnalysisResponseDTO:
        """Convert domain response to DTO"""
        
        # Convert budgets
        budgets_dto = []
        for budget in domain_response.budgets:
            status = self._determine_budget_status(budget.utilization_percentage)
            
            budgets_dto.append(BudgetDTO(
                id=budget.id,
                name=budget.name,
                amount={
                    "amount": str(budget.amount.amount),
                    "currency": budget.amount.currency
                },
                spent={
                    "amount": str(budget.spent.amount),
                    "currency": budget.spent.currency
                },
                remaining={
                    "amount": str(budget.remaining_budget.amount),
                    "currency": budget.remaining_budget.currency
                },
                utilization_percentage=budget.utilization_percentage,
                cost_center=budget.cost_center,
                time_range={
                    "start": budget.time_range.start,
                    "end": budget.time_range.end
                },
                alert_thresholds=budget.alert_thresholds,
                status=status,
                created_at=budget.created_at
            ))
        
        # Convert alerts
        alerts_dto = []
        for alert in domain_response.alerts:
            alerts_dto.append(BudgetAlertDTO(
                budget_id=alert["budget_id"],
                budget_name=alert["budget_name"],
                cost_center=alert["cost_center"],
                threshold=alert["threshold"],
                utilization=alert["utilization"],
                severity=alert["severity"],
                message=f"Budget utilization has exceeded {alert['threshold']*100}% threshold",
                triggered_at=datetime.utcnow()
            ))
        
        # Calculate summary
        summary = {"on_track": 0, "warning": 0, "over_budget": 0}
        for budget_dto in budgets_dto:
            summary[budget_dto.status] += 1
        
        return BudgetAnalysisResponseDTO(
            budgets=budgets_dto,
            total_allocated={
                "amount": str(domain_response.total_allocated.amount),
                "currency": domain_response.total_allocated.currency
            },
            total_spent={
                "amount": str(domain_response.total_spent.amount),
                "currency": domain_response.total_spent.currency
            },
            utilization_percentage=domain_response.utilization_percentage,
            alerts=alerts_dto,
            summary=summary
        )
    
    def _determine_budget_status(self, utilization_percentage: float) -> str:
        """Determine budget status based on utilization"""
        if utilization_percentage >= 100:
            return "over_budget"
        elif utilization_percentage >= 80:
            return "warning"
        else:
            return "on_track"


# Router factory
def create_budget_router(use_case_factory: UseCaseFactory) -> APIRouter:
    """Create budget management router"""
    controller = BudgetController(use_case_factory)
    return controller.router