"""
Cost Analysis Controller

This module implements the HTTP interface adapters for cost analysis operations.
Controllers are responsible for handling HTTP requests, validating input,
calling use cases, and formatting responses.

Following Clean Architecture principles:
- Controllers depend on use cases (application layer)
- Controllers handle HTTP concerns (routing, serialization, validation)
- Controllers are independent of business logic
- Controllers follow Single Responsibility Principle
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from ..domain.entities import Money, ResourceType, TimeRange
from ..usecase.cost_analysis import (
    CostAnalysisRequest,
    CostAnalysisResponse,
    CostAnalysisUseCase,
    UseCaseFactory,
)


# Request/Response Models (DTOs for HTTP layer)
class MoneyDTO(BaseModel):
    """DTO for Money value object"""
    amount: Decimal = Field(..., description="Monetary amount", ge=0)
    currency: str = Field(default="USD", description="Currency code", min_length=3, max_length=3)
    
    class Config:
        schema_extra = {
            "example": {
                "amount": "150.75",
                "currency": "USD"
            }
        }


class TimeRangeDTO(BaseModel):
    """DTO for TimeRange value object"""
    start: datetime = Field(..., description="Start date and time")
    end: datetime = Field(..., description="End date and time")
    
    @validator('end')
    def end_must_be_after_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError('End time must be after start time')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "start": "2024-11-01T00:00:00Z",
                "end": "2024-11-30T23:59:59Z"
            }
        }


class CostAnalysisRequestDTO(BaseModel):
    """DTO for cost analysis request"""
    resource_ids: Optional[List[UUID]] = Field(None, description="List of resource IDs to analyze")
    cost_center: Optional[str] = Field(None, description="Cost center to filter by", min_length=1, max_length=100)
    time_range: Optional[TimeRangeDTO] = Field(None, description="Time range for analysis")
    resource_type: Optional[ResourceType] = Field(None, description="Resource type to filter by")
    
    class Config:
        schema_extra = {
            "example": {
                "cost_center": "engineering",
                "time_range": {
                    "start": "2024-11-01T00:00:00Z",
                    "end": "2024-11-30T23:59:59Z"
                },
                "resource_type": "ec2"
            }
        }


class TopCostResourceDTO(BaseModel):
    """DTO for top cost resource information"""
    resource_id: UUID
    resource_name: str
    resource_type: str
    cost: MoneyDTO
    cost_center: str


class CostAnalysisResponseDTO(BaseModel):
    """DTO for cost analysis response"""
    total_cost: MoneyDTO
    cost_by_resource: Dict[str, MoneyDTO]  # UUID as string for JSON serialization
    cost_by_category: Dict[str, MoneyDTO]
    cost_trend_percentage: float = Field(..., description="Cost trend as percentage")
    period_comparison: Dict[str, MoneyDTO]
    top_cost_resources: List[TopCostResourceDTO]
    
    class Config:
        schema_extra = {
            "example": {
                "total_cost": {"amount": "1250.50", "currency": "USD"},
                "cost_by_category": {
                    "compute": {"amount": "800.00", "currency": "USD"},
                    "storage": {"amount": "300.50", "currency": "USD"},
                    "network": {"amount": "150.00", "currency": "USD"}
                },
                "cost_trend_percentage": 15.5,
                "period_comparison": {
                    "current_period": {"amount": "1250.50", "currency": "USD"},
                    "previous_period": {"amount": "1083.26", "currency": "USD"}
                }
            }
        }


class ErrorResponseDTO(BaseModel):
    """DTO for error responses"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")
    details: Optional[Dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Invalid time range provided",
                "error_code": "INVALID_TIME_RANGE",
                "details": {"field": "time_range.end", "reason": "End time must be after start time"},
                "timestamp": "2024-11-25T21:45:00Z"
            }
        }


# Controller Implementation
class CostController:
    """Controller for cost analysis operations"""
    
    def __init__(self, use_case_factory: UseCaseFactory):
        self._use_case_factory = use_case_factory
        self.router = APIRouter(prefix="/api/v1/costs", tags=["Cost Analysis"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        
        @self.router.post(
            "/analyze",
            response_model=CostAnalysisResponseDTO,
            status_code=status.HTTP_200_OK,
            summary="Analyze costs",
            description="Perform comprehensive cost analysis with filtering and aggregation options",
            responses={
                400: {"model": ErrorResponseDTO, "description": "Bad Request"},
                404: {"model": ErrorResponseDTO, "description": "Resources not found"},
                500: {"model": ErrorResponseDTO, "description": "Internal Server Error"}
            }
        )
        async def analyze_costs(request: CostAnalysisRequestDTO) -> CostAnalysisResponseDTO:
            """Analyze costs based on provided criteria"""
            try:
                # Convert DTO to domain request
                domain_request = self._convert_to_domain_request(request)
                
                # Execute use case
                use_case = self._use_case_factory.create_cost_analysis_use_case()
                response = await use_case.execute(domain_request)
                
                # Convert domain response to DTO
                return self._convert_to_dto_response(response)
                
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponseDTO(
                        error=str(e),
                        error_code="VALIDATION_ERROR"
                    ).dict()
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponseDTO(
                        error="Internal server error occurred",
                        error_code="INTERNAL_ERROR",
                        details={"original_error": str(e)}
                    ).dict()
                )
        
        @self.router.get(
            "/summary",
            response_model=Dict[str, MoneyDTO],
            summary="Get cost summary",
            description="Get a quick cost summary for the last 30 days"
        )
        async def get_cost_summary(
            cost_center: Optional[str] = Query(None, description="Filter by cost center"),
            days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
        ) -> Dict[str, MoneyDTO]:
            """Get cost summary for specified period"""
            try:
                # Create time range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                time_range = TimeRange(start_date, end_date)
                
                # Create request
                domain_request = CostAnalysisRequest(
                    cost_center=cost_center,
                    time_range=time_range
                )
                
                # Execute use case
                use_case = self._use_case_factory.create_cost_analysis_use_case()
                response = await use_case.execute(domain_request)
                
                # Return simplified response
                return {
                    "total_cost": MoneyDTO(
                        amount=response.total_cost.amount,
                        currency=response.total_cost.currency
                    ),
                    "average_daily_cost": MoneyDTO(
                        amount=response.total_cost.amount / days,
                        currency=response.total_cost.currency
                    )
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponseDTO(
                        error="Failed to get cost summary",
                        error_code="SUMMARY_ERROR"
                    ).dict()
                )
        
        @self.router.get(
            "/trends",
            response_model=Dict[str, float],
            summary="Get cost trends",
            description="Get cost trend analysis over time"
        )
        async def get_cost_trends(
            cost_center: Optional[str] = Query(None, description="Filter by cost center"),
            period_days: int = Query(30, description="Period in days", ge=7, le=365)
        ) -> Dict[str, float]:
            """Get cost trends over specified period"""
            try:
                # Create time range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=period_days)
                time_range = TimeRange(start_date, end_date)
                
                # Create request
                domain_request = CostAnalysisRequest(
                    cost_center=cost_center,
                    time_range=time_range
                )
                
                # Execute use case
                use_case = self._use_case_factory.create_cost_analysis_use_case()
                response = await use_case.execute(domain_request)
                
                return {
                    "trend_percentage": response.cost_trend_percentage,
                    "period_days": period_days,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponseDTO(
                        error="Failed to get cost trends",
                        error_code="TRENDS_ERROR"
                    ).dict()
                )
        
        @self.router.get(
            "/health",
            summary="Health check",
            description="Check if cost analysis service is healthy"
        )
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "cost-analysis",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
    
    def _convert_to_domain_request(self, dto: CostAnalysisRequestDTO) -> CostAnalysisRequest:
        """Convert DTO to domain request"""
        time_range = None
        if dto.time_range:
            time_range = TimeRange(dto.time_range.start, dto.time_range.end)
        
        return CostAnalysisRequest(
            resource_ids=dto.resource_ids,
            cost_center=dto.cost_center,
            time_range=time_range,
            resource_type=dto.resource_type
        )
    
    def _convert_to_dto_response(self, domain_response: CostAnalysisResponse) -> CostAnalysisResponseDTO:
        """Convert domain response to DTO"""
        return CostAnalysisResponseDTO(
            total_cost=MoneyDTO(
                amount=domain_response.total_cost.amount,
                currency=domain_response.total_cost.currency
            ),
            cost_by_resource={
                str(resource_id): MoneyDTO(amount=cost.amount, currency=cost.currency)
                for resource_id, cost in domain_response.cost_by_resource.items()
            },
            cost_by_category={
                category: MoneyDTO(amount=cost.amount, currency=cost.currency)
                for category, cost in domain_response.cost_by_category.items()
            },
            cost_trend_percentage=domain_response.cost_trend_percentage,
            period_comparison={
                period: MoneyDTO(amount=cost.amount, currency=cost.currency)
                for period, cost in domain_response.period_comparison.items()
            },
            top_cost_resources=[
                TopCostResourceDTO(
                    resource_id=resource["resource_id"],
                    resource_name=resource["resource_name"],
                    resource_type=resource["resource_type"],
                    cost=MoneyDTO(
                        amount=resource["cost"].amount,
                        currency=resource["cost"].currency
                    ),
                    cost_center=resource["cost_center"]
                )
                for resource in domain_response.top_cost_resources
            ]
        )


# Dependency injection helper
def get_cost_controller(use_case_factory: UseCaseFactory = Depends()) -> CostController:
    """Dependency injection for cost controller"""
    return CostController(use_case_factory)


# Router instance for FastAPI app
def create_cost_router(use_case_factory: UseCaseFactory) -> APIRouter:
    """Create cost analysis router"""
    controller = CostController(use_case_factory)
    return controller.router