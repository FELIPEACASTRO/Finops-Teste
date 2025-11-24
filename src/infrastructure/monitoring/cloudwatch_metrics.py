"""CloudWatch metrics wrapper for monitoring."""

from typing import Optional, Dict, Any
import logging
from datetime import datetime


class CloudWatchMetrics:
    """
    Simple wrapper for CloudWatch metrics.
    
    In production, this would actually push to CloudWatch.
    For now, it logs metrics (ready to integrate with boto3).
    """

    def __init__(self, namespace: str = "FinOpsAnalyzer", logger: Optional[logging.Logger] = None):
        """
        Initialize metrics collector.
        
        Args:
            namespace: CloudWatch namespace
            logger: Logger instance
        """
        self.namespace = namespace
        self.logger = logger or logging.getLogger(__name__)
        self.metrics: Dict[str, Any] = {}

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a metric.
        
        In production, this would push to CloudWatch.
        For now, just logs it.
        """
        metric = {
            "name": metric_name,
            "value": value,
            "unit": unit,
            "dimensions": dimensions or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.metrics[metric_name] = metric
        
        self.logger.info(
            f"METRIC: {self.namespace}/{metric_name} = {value} {unit}"
        )

    def put_analysis_duration(self, duration_seconds: float, region: str) -> None:
        """Record analysis duration."""
        self.put_metric(
            "AnalysisDuration",
            duration_seconds,
            unit="Seconds",
            dimensions={"Region": region}
        )

    def put_resources_analyzed(self, count: int, region: str) -> None:
        """Record number of resources analyzed."""
        self.put_metric(
            "ResourcesAnalyzed",
            count,
            unit="Count",
            dimensions={"Region": region}
        )

    def put_recommendations_generated(self, count: int) -> None:
        """Record number of recommendations generated."""
        self.put_metric(
            "RecommendationsGenerated",
            count,
            unit="Count"
        )

    def put_bedrock_api_calls(self, count: int) -> None:
        """Record Bedrock API calls."""
        self.put_metric(
            "BedrockAPICall",
            count,
            unit="Count"
        )

    def put_error(self, error_type: str, region: Optional[str] = None) -> None:
        """Record errors."""
        dimensions = {"ErrorType": error_type}
        if region:
            dimensions["Region"] = region
        
        self.put_metric(
            "Errors",
            1,
            unit="Count",
            dimensions=dimensions
        )

    def put_total_savings(self, monthly_usd: float, annual_usd: float) -> None:
        """Record identified savings."""
        self.put_metric("MonthlySavings", monthly_usd, unit="None")
        self.put_metric("AnnualSavings", annual_usd, unit="None")

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics.copy()
