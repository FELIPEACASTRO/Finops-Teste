"""
Data Transfer Objects for analysis operations.
Provides a stable interface between layers.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities import AnalysisReport


@dataclass
class AnalysisRequestDTO:
    """DTO for analysis requests."""
    regions: List[str]
    analysis_period_days: int = 30
    include_cost_data: bool = True
    save_report: bool = True
    notification_email: Optional[str] = None


@dataclass
class AnalysisResponseDTO:
    """DTO for analysis responses."""
    success: bool
    message: str
    report: Optional[AnalysisReport] = None
    report_location: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "message": self.message,
            "execution_time_seconds": self.execution_time_seconds
        }
        
        if self.report:
            result["report"] = self.report.to_dict()
        
        if self.report_location:
            result["report_location"] = self.report_location
            
        if self.error_message:
            result["error_message"] = self.error_message
            
        return result


@dataclass
class ResourceSummaryDTO:
    """DTO for resource summary information."""
    resource_type: str
    total_count: int
    total_monthly_cost: float
    potential_savings: float
    high_priority_recommendations: int


@dataclass
class NotificationDTO:
    """DTO for notification data."""
    recipient_email: str
    subject: str
    report_summary: Dict[str, Any]
    report_location: str
    generated_at: datetime