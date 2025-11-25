"""
Optimization Controller

This module implements the HTTP interface adapters for optimization operations.
Handles optimization recommendations, application of recommendations,
and optimization reporting.

Following Clean Architecture and SOLID principles:
- Single Responsibility: Only handles HTTP concerns for optimization
- Open/Closed: Extensible through composition
- Dependency Inversion: Depends on abstractions (use cases)
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from ..domain.entities import Money, OptimizationStatus
from ..usecase.cost_analysis import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationUseCase,
    UseCaseFactory,
)


# Request/Response DTOs
class OptimizationRequestDTO(BaseModel):
    """DTO for optimization analysis request"""
    resource_ids: Optional[List[UUID]] = Field(None, description="Specific resources to analyze")
    cost_center: Optional[str] = Field(None, description="Cost center to analyze", min_length=1)
    min_savings_threshold: Decimal = Field(
        default=Decimal("10.00"),
        description="Minimum savings threshold in USD",
        ge=0
    )
    confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence score for recommendations",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        schema_extra = {
            "example": {
                "cost_center": "engineering",
                "min_savings_threshold": "50.00",
                "confidence_threshold": 0.8
            }
        }


class OptimizationRecommendationDTO(BaseModel):
    """DTO for optimization recommendation"""
    id: UUID
    resource_id: UUID
    title: str
    description: str
    potential_savings: Dict[str, str]  # {"amount": "150.00", "currency": "USD"}
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    status: OptimizationStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    impact_level: str  # "low", "medium", "high", "critical"
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "resource_id": "123e4567-e89b-12d3-a456-426614174001",
                "title": "Rightsize EC2 Instance",
                "description": "Instance is over-provisioned. Consider downsizing from m5.large to m5.medium",
                "potential_savings": {"amount": "150.00", "currency": "USD"},
                "confidence_score": 0.85,
                "status": "pending",
                "impact_level": "medium"
            }
        }


class OptimizationResponseDTO(BaseModel):
    """DTO for optimization analysis response"""
    recommendations: List[OptimizationRecommendationDTO]
    total_potential_savings: Dict[str, str]
    high_impact_count: int
    average_confidence: float
    analysis_summary: Dict[str, int]  # Count by impact level
    
    class Config:
        schema_extra = {
            "example": {
                "total_potential_savings": {"amount": "1250.00", "currency": "USD"},
                "high_impact_count": 3,
                "average_confidence": 0.78,
                "analysis_summary": {
                    "critical": 1,
                    "high": 2,
                    "medium": 5,
                    "low": 3
                }
            }
        }


class ApplyRecommendationRequestDTO(BaseModel):
    """DTO for applying a recommendation"""
    recommendation_id: UUID
    apply_immediately: bool = Field(default=False, description="Apply recommendation immediately")
    scheduled_time: Optional[datetime] = Field(None, description="Schedule application for later")
    notes: Optional[str] = Field(None, description="Additional notes", max_length=500)
    
    @validator('scheduled_time')
    def scheduled_time_must_be_future(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v


class ApplyRecommendationResponseDTO(BaseModel):
    """DTO for apply recommendation response"""
    recommendation_id: UUID
    status: str
    message: str
    applied_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None


class OptimizationSummaryDTO(BaseModel):
    """DTO for optimization summary"""
    total_recommendations: int
    pending_recommendations: int
    applied_recommendations: int
    total_potential_savings: Dict[str, str]
    total_realized_savings: Dict[str, str]
    optimization_rate: float  # Percentage of recommendations applied
    last_analysis: datetime


# Controller Implementation
class OptimizationController:
    """Controller for optimization operations"""
    
    def __init__(self, use_case_factory: UseCaseFactory):
        self._use_case_factory = use_case_factory
        self.router = APIRouter(prefix="/api/v1/optimization", tags=["Optimization"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        
        @self.router.post(
            "/analyze",
            response_model=OptimizationResponseDTO,
            status_code=status.HTTP_200_OK,
            summary="Generate optimization recommendations",
            description="Analyze resources and generate cost optimization recommendations using ML"
        )
        async def generate_recommendations(
            request: OptimizationRequestDTO
        ) -> OptimizationResponseDTO:
            """Generate optimization recommendations"""
            try:
                # Convert DTO to domain request
                domain_request = OptimizationRequest(
                    resource_ids=request.resource_ids,
                    cost_center=request.cost_center,
                    min_savings_threshold=Money(request.min_savings_threshold, "USD"),
                    confidence_threshold=request.confidence_threshold
                )
                
                # Execute use case
                use_case = self._use_case_factory.create_optimization_use_case()
                response = await use_case.generate_recommendations(domain_request)
                
                # Convert to DTO
                return self._convert_optimization_response_to_dto(response)
                
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": str(e), "error_code": "VALIDATION_ERROR"}
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to generate recommendations", "error_code": "ANALYSIS_ERROR"}
                )
        
        @self.router.post(
            "/recommendations/{recommendation_id}/apply",
            response_model=ApplyRecommendationResponseDTO,
            summary="Apply optimization recommendation",
            description="Apply a specific optimization recommendation"
        )
        async def apply_recommendation(
            recommendation_id: UUID,
            request: ApplyRecommendationRequestDTO
        ) -> ApplyRecommendationResponseDTO:
            """Apply an optimization recommendation"""
            try:
                if request.recommendation_id != recommendation_id:
                    raise ValueError("Recommendation ID mismatch")
                
                # Execute use case
                use_case = self._use_case_factory.create_optimization_use_case()
                await use_case.apply_recommendation(recommendation_id)
                
                return ApplyRecommendationResponseDTO(
                    recommendation_id=recommendation_id,
                    status="applied" if request.apply_immediately else "scheduled",
                    message="Recommendation applied successfully" if request.apply_immediately 
                           else "Recommendation scheduled for application",
                    applied_at=datetime.utcnow() if request.apply_immediately else None,
                    scheduled_for=request.scheduled_time
                )
                
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": str(e), "error_code": "VALIDATION_ERROR"}
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to apply recommendation", "error_code": "APPLICATION_ERROR"}
                )
        
        @self.router.get(
            "/recommendations",
            response_model=List[OptimizationRecommendationDTO],
            summary="Get optimization recommendations",
            description="Retrieve optimization recommendations with filtering options"
        )
        async def get_recommendations(
            status_filter: Optional[OptimizationStatus] = Query(None, description="Filter by status"),
            cost_center: Optional[str] = Query(None, description="Filter by cost center"),
            min_savings: Optional[Decimal] = Query(None, description="Minimum savings threshold", ge=0),
            limit: int = Query(50, description="Maximum number of results", ge=1, le=1000)
        ) -> List[OptimizationRecommendationDTO]:
            """Get optimization recommendations with filters"""
            try:
                # This would typically call a use case to get recommendations
                # For now, return empty list as placeholder
                return []
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to retrieve recommendations", "error_code": "RETRIEVAL_ERROR"}
                )
        
        @self.router.get(
            "/summary",
            response_model=OptimizationSummaryDTO,
            summary="Get optimization summary",
            description="Get summary of optimization activities and potential savings"
        )
        async def get_optimization_summary(
            cost_center: Optional[str] = Query(None, description="Filter by cost center")
        ) -> OptimizationSummaryDTO:
            """Get optimization summary"""
            try:
                # Placeholder implementation
                return OptimizationSummaryDTO(
                    total_recommendations=0,
                    pending_recommendations=0,
                    applied_recommendations=0,
                    total_potential_savings={"amount": "0.00", "currency": "USD"},
                    total_realized_savings={"amount": "0.00", "currency": "USD"},
                    optimization_rate=0.0,
                    last_analysis=datetime.utcnow()
                )
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to get optimization summary", "error_code": "SUMMARY_ERROR"}
                )
        
        @self.router.delete(
            "/recommendations/{recommendation_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Reject optimization recommendation",
            description="Reject or dismiss an optimization recommendation"
        )
        async def reject_recommendation(
            recommendation_id: UUID,
            reason: Optional[str] = Query(None, description="Reason for rejection")
        ):
            """Reject an optimization recommendation"""
            try:
                # This would call a use case to reject the recommendation
                # Placeholder implementation
                pass
                
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": str(e), "error_code": "VALIDATION_ERROR"}
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Failed to reject recommendation", "error_code": "REJECTION_ERROR"}
                )
        
        @self.router.get(
            "/health",
            summary="Health check",
            description="Check if optimization service is healthy"
        )
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "optimization",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
    
    def _convert_optimization_response_to_dto(
        self, 
        domain_response: OptimizationResponse
    ) -> OptimizationResponseDTO:
        """Convert domain response to DTO"""
        
        # Convert recommendations
        recommendations_dto = []
        for rec in domain_response.recommendations:
            impact_level = self._calculate_impact_level(rec.potential_savings)
            
            recommendations_dto.append(OptimizationRecommendationDTO(
                id=rec.id,
                resource_id=rec.resource_id,
                title=rec.title,
                description=rec.description,
                potential_savings={
                    "amount": str(rec.potential_savings.amount),
                    "currency": rec.potential_savings.currency
                },
                confidence_score=rec.confidence_score,
                status=rec.status,
                created_at=rec.created_at,
                expires_at=rec.expires_at,
                impact_level=impact_level
            ))
        
        # Calculate analysis summary
        analysis_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for rec_dto in recommendations_dto:
            analysis_summary[rec_dto.impact_level] += 1
        
        return OptimizationResponseDTO(
            recommendations=recommendations_dto,
            total_potential_savings={
                "amount": str(domain_response.total_potential_savings.amount),
                "currency": domain_response.total_potential_savings.currency
            },
            high_impact_count=domain_response.high_impact_count,
            average_confidence=domain_response.average_confidence,
            analysis_summary=analysis_summary
        )
    
    def _calculate_impact_level(self, potential_savings: Money) -> str:
        """Calculate impact level based on potential savings"""
        amount = potential_savings.amount
        
        if amount >= 500:
            return "critical"
        elif amount >= 200:
            return "high"
        elif amount >= 50:
            return "medium"
        else:
            return "low"


# Router factory
def create_optimization_router(use_case_factory: UseCaseFactory) -> APIRouter:
    """Create optimization router"""
    controller = OptimizationController(use_case_factory)
    return controller.router