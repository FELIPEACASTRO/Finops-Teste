"""
Metrics Collection System

This module provides comprehensive metrics collection following observability
best practices. Implements RED (Rate, Errors, Duration) and USE (Utilization,
Saturation, Errors) methodologies for monitoring.

Features:
- Business metrics (cost, savings, budget utilization)
- Technical metrics (response times, error rates, throughput)
- Infrastructure metrics (database connections, memory usage)
- Custom metrics with labels and dimensions
- Integration with Prometheus and other monitoring systems
- Real-time metrics aggregation
"""

import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import Field
from pydantic_settings import BaseSettings

from .logger import get_logger


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricsConfig(BaseSettings):
    """Metrics configuration settings"""

    # Collection settings
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8080, env="METRICS_PORT")
    metrics_path: str = Field(default="/metrics", env="METRICS_PATH")

    # Retention settings
    metrics_retention_hours: int = Field(default=24, env="METRICS_RETENTION_HOURS")
    histogram_buckets: List[float] = Field(
        default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )

    # Export settings
    enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    prometheus_namespace: str = Field(default="finops", env="PROMETHEUS_NAMESPACE")

    # Business metrics settings
    cost_threshold_high: float = Field(default=1000.0, env="COST_THRESHOLD_HIGH")
    cost_threshold_critical: float = Field(default=5000.0, env="COST_THRESHOLD_CRITICAL")

    class Config:
        env_file = ".env"
        case_sensitive = False


@dataclass
class MetricValue:
    """Individual metric value with timestamp"""
    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class HistogramBucket:
    """Histogram bucket for latency measurements"""
    upper_bound: float
    count: int = 0


class Metric:
    """Base metric class"""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.values: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.lock = Lock()
        self.created_at = datetime.utcnow()

    def _get_label_key(self, labels: Dict[str, str]) -> str:
        """Generate key from labels"""
        if not labels:
            return "default"
        return "|".join(f"{k}:{v}" for k, v in sorted(labels.items()))

    def add_value(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Add value to metric"""
        labels = labels or {}
        label_key = self._get_label_key(labels)

        with self.lock:
            self.values[label_key].append(MetricValue(
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels
            ))

    def get_current_value(self, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current value for metric"""
        label_key = self._get_label_key(labels or {})

        with self.lock:
            if label_key in self.values and self.values[label_key]:
                return self.values[label_key][-1].value

        return None

    def get_values_in_range(
        self,
        start_time: datetime,
        end_time: datetime,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricValue]:
        """Get values within time range"""
        label_key = self._get_label_key(labels or {})

        with self.lock:
            if label_key not in self.values:
                return []

            return [
                value for value in self.values[label_key]
                if start_time <= value.timestamp <= end_time
            ]


class Counter(Metric):
    """Counter metric - monotonically increasing"""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self.metric_type = MetricType.COUNTER

    def increment(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment counter"""
        current = self.get_current_value(labels) or 0
        self.add_value(current + amount, labels)

    def get_rate(
        self,
        duration_minutes: int = 5,
        labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Get rate per minute over duration"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=duration_minutes)

        values = self.get_values_in_range(start_time, end_time, labels)

        if len(values) < 2:
            return 0.0

        first_value = values[0].value
        last_value = values[-1].value
        time_diff_minutes = (values[-1].timestamp - values[0].timestamp).total_seconds() / 60

        if time_diff_minutes == 0:
            return 0.0

        return (last_value - first_value) / time_diff_minutes


class Gauge(Metric):
    """Gauge metric - can go up or down"""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self.metric_type = MetricType.GAUGE

    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value"""
        self.add_value(value, labels)

    def increment(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge"""
        current = self.get_current_value(labels) or 0
        self.add_value(current + amount, labels)

    def decrement(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge"""
        current = self.get_current_value(labels) or 0
        self.add_value(current - amount, labels)


class Histogram(Metric):
    """Histogram metric for latency measurements"""

    def __init__(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None,
        labels: Optional[List[str]] = None
    ):
        super().__init__(name, description, labels)
        self.metric_type = MetricType.HISTOGRAM
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self.bucket_counts: Dict[str, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self.sum_values: Dict[str, float] = defaultdict(float)
        self.count_values: Dict[str, int] = defaultdict(int)

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        label_key = self._get_label_key(labels or {})

        with self.lock:
            # Update buckets
            for bucket in self.buckets:
                if value <= bucket:
                    self.bucket_counts[label_key][bucket] += 1

            # Update sum and count
            self.sum_values[label_key] += value
            self.count_values[label_key] += 1

            # Store individual value
            self.add_value(value, labels)

    def get_percentile(
        self,
        percentile: float,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """Get percentile value"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)  # Last hour

        values = self.get_values_in_range(start_time, end_time, labels)

        if not values:
            return None

        sorted_values = sorted([v.value for v in values])
        index = int(len(sorted_values) * percentile / 100)

        if index >= len(sorted_values):
            index = len(sorted_values) - 1

        return sorted_values[index]

    def get_average(self, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get average value"""
        label_key = self._get_label_key(labels or {})

        with self.lock:
            count = self.count_values.get(label_key, 0)
            if count == 0:
                return None

            return self.sum_values[label_key] / count


class MetricsRegistry:
    """Registry for all metrics"""

    def __init__(self, config: MetricsConfig):
        self.config = config
        self.metrics: Dict[str, Metric] = {}
        self.lock = Lock()
        self.logger = get_logger(__name__)

    def register_counter(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Counter:
        """Register a counter metric"""
        with self.lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Counter):
                    raise ValueError(f"Metric {name} already exists with different type")
                return metric

            counter = Counter(name, description, labels)
            self.metrics[name] = counter
            self.logger.debug(f"Registered counter metric: {name}")
            return counter

    def register_gauge(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Gauge:
        """Register a gauge metric"""
        with self.lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Gauge):
                    raise ValueError(f"Metric {name} already exists with different type")
                return metric

            gauge = Gauge(name, description, labels)
            self.metrics[name] = gauge
            self.logger.debug(f"Registered gauge metric: {name}")
            return gauge

    def register_histogram(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None,
        labels: Optional[List[str]] = None
    ) -> Histogram:
        """Register a histogram metric"""
        with self.lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Histogram):
                    raise ValueError(f"Metric {name} already exists with different type")
                return metric

            histogram = Histogram(name, description, buckets, labels)
            self.metrics[name] = histogram
            self.logger.debug(f"Registered histogram metric: {name}")
            return histogram

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get metric by name"""
        with self.lock:
            return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all registered metrics"""
        with self.lock:
            return self.metrics.copy()

    def cleanup_old_data(self):
        """Clean up old metric data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.config.metrics_retention_hours)

        with self.lock:
            for metric in self.metrics.values():
                with metric.lock:
                    for label_key in metric.values:
                        # Remove old values
                        while (metric.values[label_key] and
                               metric.values[label_key][0].timestamp < cutoff_time):
                            metric.values[label_key].popleft()


class FinOpsMetrics:
    """FinOps-specific metrics collector"""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self.logger = get_logger(__name__)

        # Business metrics
        self.total_cost = registry.register_gauge(
            "finops_total_cost",
            "Total cost across all resources",
            ["cost_center", "currency"]
        )

        self.cost_by_service = registry.register_gauge(
            "finops_cost_by_service",
            "Cost breakdown by service type",
            ["service_type", "cost_center", "currency"]
        )

        self.budget_utilization = registry.register_gauge(
            "finops_budget_utilization_percentage",
            "Budget utilization percentage",
            ["cost_center", "budget_name"]
        )

        self.optimization_savings = registry.register_counter(
            "finops_optimization_savings_total",
            "Total savings from applied optimizations",
            ["optimization_type", "currency"]
        )

        self.recommendations_generated = registry.register_counter(
            "finops_recommendations_generated_total",
            "Total optimization recommendations generated",
            ["recommendation_type", "confidence_level"]
        )

        self.recommendations_applied = registry.register_counter(
            "finops_recommendations_applied_total",
            "Total optimization recommendations applied",
            ["recommendation_type"]
        )

        # Technical metrics
        self.http_requests = registry.register_counter(
            "finops_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"]
        )

        self.http_request_duration = registry.register_histogram(
            "finops_http_request_duration_seconds",
            "HTTP request duration in seconds",
            labels=["method", "endpoint"]
        )

        self.database_connections = registry.register_gauge(
            "finops_database_connections",
            "Number of active database connections",
            ["pool_name"]
        )

        self.database_query_duration = registry.register_histogram(
            "finops_database_query_duration_seconds",
            "Database query duration in seconds",
            labels=["query_type", "table"]
        )

        self.cache_hits = registry.register_counter(
            "finops_cache_hits_total",
            "Total cache hits",
            ["cache_type"]
        )

        self.cache_misses = registry.register_counter(
            "finops_cache_misses_total",
            "Total cache misses",
            ["cache_type"]
        )

    def record_cost_analysis(
        self,
        total_cost: float,
        cost_center: str,
        currency: str = "USD",
        service_breakdown: Optional[Dict[str, float]] = None
    ):
        """Record cost analysis metrics"""
        self.total_cost.set(total_cost, {
            "cost_center": cost_center,
            "currency": currency
        })

        if service_breakdown:
            for service_type, cost in service_breakdown.items():
                self.cost_by_service.set(cost, {
                    "service_type": service_type,
                    "cost_center": cost_center,
                    "currency": currency
                })

        self.logger.debug(f"Recorded cost analysis metrics for {cost_center}: {total_cost} {currency}")

    def record_budget_utilization(
        self,
        cost_center: str,
        budget_name: str,
        utilization_percentage: float
    ):
        """Record budget utilization metrics"""
        self.budget_utilization.set(utilization_percentage, {
            "cost_center": cost_center,
            "budget_name": budget_name
        })

        self.logger.debug(f"Recorded budget utilization: {budget_name} at {utilization_percentage}%")

    def record_optimization_recommendation(
        self,
        recommendation_type: str,
        confidence_score: float,
        potential_savings: float,
        currency: str = "USD"
    ):
        """Record optimization recommendation metrics"""
        confidence_level = "high" if confidence_score >= 0.8 else "medium" if confidence_score >= 0.6 else "low"

        self.recommendations_generated.increment(1, {
            "recommendation_type": recommendation_type,
            "confidence_level": confidence_level
        })

        self.logger.debug(f"Recorded optimization recommendation: {recommendation_type} with {confidence_level} confidence")

    def record_optimization_applied(
        self,
        recommendation_type: str,
        realized_savings: float,
        currency: str = "USD"
    ):
        """Record applied optimization metrics"""
        self.recommendations_applied.increment(1, {
            "recommendation_type": recommendation_type
        })

        self.optimization_savings.increment(realized_savings, {
            "optimization_type": recommendation_type,
            "currency": currency
        })

        self.logger.debug(f"Recorded applied optimization: {recommendation_type} saving {realized_savings} {currency}")

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float
    ):
        """Record HTTP request metrics"""
        self.http_requests.increment(1, {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code)
        })

        self.http_request_duration.observe(duration_seconds, {
            "method": method,
            "endpoint": endpoint
        })

    def record_database_query(
        self,
        query_type: str,
        table: str,
        duration_seconds: float
    ):
        """Record database query metrics"""
        self.database_query_duration.observe(duration_seconds, {
            "query_type": query_type,
            "table": table
        })

    def record_cache_operation(self, cache_type: str, hit: bool):
        """Record cache operation metrics"""
        if hit:
            self.cache_hits.increment(1, {"cache_type": cache_type})
        else:
            self.cache_misses.increment(1, {"cache_type": cache_type})

    @contextmanager
    def time_operation(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time

            # Record in appropriate histogram based on operation type
            if "http" in operation_name.lower():
                self.http_request_duration.observe(duration, labels or {})
            elif "database" in operation_name.lower() or "query" in operation_name.lower():
                self.database_query_duration.observe(duration, labels or {})


# Global metrics registry
_registry: Optional[MetricsRegistry] = None
_finops_metrics: Optional[FinOpsMetrics] = None


def setup_metrics(config: Optional[MetricsConfig] = None) -> None:
    """Setup global metrics system"""
    global _registry, _finops_metrics

    if config is None:
        config = MetricsConfig()

    _registry = MetricsRegistry(config)
    _finops_metrics = FinOpsMetrics(_registry)


def get_metrics_registry() -> MetricsRegistry:
    """Get global metrics registry"""
    global _registry

    if _registry is None:
        setup_metrics()

    return _registry


def get_finops_metrics() -> FinOpsMetrics:
    """Get FinOps metrics collector"""
    global _finops_metrics

    if _finops_metrics is None:
        setup_metrics()

    return _finops_metrics


def export_prometheus_metrics() -> str:
    """Export metrics in Prometheus format"""
    registry = get_metrics_registry()
    lines = []

    for name, metric in registry.get_all_metrics().items():
        # Add metric help
        lines.append(f"# HELP {name} {metric.description}")
        lines.append(f"# TYPE {name} {metric.metric_type.value}")

        # Add metric values
        with metric.lock:
            for label_key, values in metric.values.items():
                if not values:
                    continue

                current_value = values[-1]

                if label_key == "default":
                    lines.append(f"{name} {current_value.value}")
                else:
                    label_str = ",".join(f'{k}="{v}"' for k, v in current_value.labels.items())
                    lines.append(f"{name}{{{label_str}}} {current_value.value}")

    return "\n".join(lines)
