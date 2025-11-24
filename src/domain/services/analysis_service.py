"""
Domain service for cost optimization analysis.
Contains business logic for analyzing resources and generating recommendations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from decimal import Decimal

from ..entities import (
    AWSResource, 
    OptimizationRecommendation, 
    AnalysisReport,
    CostData,
    UsagePattern,
    Priority,
    RiskLevel
)


class IAnalysisService(ABC):
    """
    Interface for analysis services.
    
    Defines the contract for different analysis implementations
    (e.g., ML-based, rule-based, AI-based).
    """

    @abstractmethod
    async def analyze_resource(self, resource: AWSResource) -> OptimizationRecommendation:
        """Analyze a single resource and generate recommendation."""
        pass

    @abstractmethod
    async def analyze_resources(self, resources: List[AWSResource]) -> List[OptimizationRecommendation]:
        """Analyze multiple resources and generate recommendations."""
        pass

    @abstractmethod
    async def generate_report(
        self, 
        resources: List[AWSResource], 
        cost_data: CostData,
        recommendations: List[OptimizationRecommendation]
    ) -> AnalysisReport:
        """Generate a complete analysis report."""
        pass


class ResourceAnalyzer:
    """
    Domain service for resource analysis.
    
    Contains pure business logic without external dependencies.
    Follows Single Responsibility Principle.
    """

    def calculate_usage_pattern(self, resource: AWSResource) -> UsagePattern:
        """
        Determine usage pattern based on metrics.
        
        Time Complexity: O(n) where n is the number of CPU data points
        Space Complexity: O(1)
        """
        cpu_stats = resource.metrics.get_cpu_stats()
        
        if not cpu_stats or cpu_stats["mean"] == 0:
            return UsagePattern.UNKNOWN
            
        mean_cpu = cpu_stats["mean"]
        max_cpu = cpu_stats["max"]
        
        # Business rules for pattern detection
        if mean_cpu < 5:
            return UsagePattern.IDLE
        elif max_cpu - mean_cpu < 10:  # Low variance
            return UsagePattern.STEADY
        elif max_cpu - mean_cpu > 50:  # High variance
            return UsagePattern.VARIABLE
        else:
            return UsagePattern.BATCH

    def calculate_priority(
        self, 
        savings_percentage: float, 
        monthly_savings: Decimal,
        risk_level: RiskLevel
    ) -> Priority:
        """
        Calculate recommendation priority based on savings and risk.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # High savings, low risk = high priority
        if monthly_savings >= 100 and savings_percentage >= 30 and risk_level == RiskLevel.LOW:
            return Priority.HIGH
        
        # Medium savings or medium risk = medium priority
        if monthly_savings >= 50 or savings_percentage >= 20:
            return Priority.MEDIUM
            
        return Priority.LOW

    def calculate_risk_level(
        self, 
        resource: AWSResource, 
        recommended_change_percentage: float
    ) -> RiskLevel:
        """
        Calculate risk level for a recommendation.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Production resources have higher risk
        if resource.is_production():
            if recommended_change_percentage > 50:
                return RiskLevel.HIGH
            elif recommended_change_percentage > 25:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW
        
        # Non-production resources have lower risk
        if recommended_change_percentage > 75:
            return RiskLevel.HIGH
        elif recommended_change_percentage > 50:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def calculate_confidence_score(
        self, 
        resource: AWSResource, 
        data_points: int
    ) -> float:
        """
        Calculate confidence score based on data quality.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        base_confidence = min(data_points / 720, 1.0)  # 720 = 30 days * 24 hours
        
        # Adjust based on resource age and tags
        if resource.created_at and resource.tags:
            age_bonus = 0.1
            tags_bonus = 0.1 if len(resource.tags) >= 3 else 0.05
            base_confidence = min(base_confidence + age_bonus + tags_bonus, 1.0)
        
        return round(base_confidence, 2)


class ReportGenerator:
    """
    Domain service for generating analysis reports.
    
    Follows Single Responsibility Principle by focusing only on report generation.
    """

    def __init__(self):
        self.version = "4.0.0"

    def aggregate_savings(self, recommendations: List[OptimizationRecommendation]) -> Dict[str, Decimal]:
        """
        Aggregate total savings from recommendations.
        
        Time Complexity: O(n) where n is the number of recommendations
        Space Complexity: O(1)
        """
        total_monthly = sum(rec.monthly_savings_usd for rec in recommendations)
        total_annual = sum(rec.annual_savings_usd for rec in recommendations)
        
        return {
            "monthly": total_monthly,
            "annual": total_annual
        }

    def categorize_recommendations(
        self, 
        recommendations: List[OptimizationRecommendation]
    ) -> Dict[Priority, List[OptimizationRecommendation]]:
        """
        Categorize recommendations by priority.
        
        Time Complexity: O(n) where n is the number of recommendations
        Space Complexity: O(n)
        """
        categorized = {
            Priority.HIGH: [],
            Priority.MEDIUM: [],
            Priority.LOW: []
        }
        
        for rec in recommendations:
            categorized[rec.priority].append(rec)
        
        return categorized

    def generate_summary_statistics(
        self, 
        recommendations: List[OptimizationRecommendation]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for the report.
        
        Time Complexity: O(n) where n is the number of recommendations
        Space Complexity: O(1)
        """
        if not recommendations:
            return {
                "total_recommendations": 0,
                "high_priority": 0,
                "medium_priority": 0,
                "low_priority": 0,
                "average_savings_percentage": 0.0,
                "total_monthly_savings": 0.0,
                "total_annual_savings": 0.0
            }

        categorized = self.categorize_recommendations(recommendations)
        savings = self.aggregate_savings(recommendations)
        
        avg_savings_pct = sum(rec.savings_percentage for rec in recommendations) / len(recommendations)
        
        return {
            "total_recommendations": len(recommendations),
            "high_priority": len(categorized[Priority.HIGH]),
            "medium_priority": len(categorized[Priority.MEDIUM]),
            "low_priority": len(categorized[Priority.LOW]),
            "average_savings_percentage": round(avg_savings_pct, 2),
            "total_monthly_savings": float(savings["monthly"]),
            "total_annual_savings": float(savings["annual"])
        }