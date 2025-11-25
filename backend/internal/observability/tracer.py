"""
Distributed Tracing System

This module provides distributed tracing capabilities using OpenTelemetry
for comprehensive observability across the FinOps platform.

Features:
- OpenTelemetry integration
- Automatic instrumentation for FastAPI, PostgreSQL, Redis
- Custom spans for business operations
- Trace correlation with logs and metrics
- Integration with Jaeger, Zipkin, and other tracing backends
- Performance monitoring and bottleneck detection
"""

import functools
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from pydantic import Field
from pydantic_settings import BaseSettings

from .logger import get_logger


class TracingConfig(BaseSettings):
    """Tracing configuration settings"""

    # General settings
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    service_name: str = Field(default="finops-teste", env="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Jaeger settings
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
    jaeger_agent_host: str = Field(default="localhost", env="JAEGER_AGENT_HOST")
    jaeger_agent_port: int = Field(default=6831, env="JAEGER_AGENT_PORT")

    # Sampling settings
    trace_sample_rate: float = Field(default=1.0, env="TRACE_SAMPLE_RATE")

    # Export settings
    export_timeout: int = Field(default=30, env="TRACE_EXPORT_TIMEOUT")
    max_export_batch_size: int = Field(default=512, env="TRACE_MAX_EXPORT_BATCH_SIZE")

    class Config:
        env_file = ".env"
        case_sensitive = False


class FinOpsTracer:
    """FinOps-specific tracing wrapper"""

    def __init__(self, config: TracingConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self._tracer: Optional[trace.Tracer] = None
        self._setup_tracing()

    def _setup_tracing(self):
        """Setup OpenTelemetry tracing"""
        if not self.config.enable_tracing:
            self.logger.info("Tracing is disabled")
            return

        try:
            # Create resource
            resource = Resource.create({
                "service.name": self.config.service_name,
                "service.version": self.config.service_version,
                "deployment.environment": self.config.environment
            })

            # Create tracer provider
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)

            # Setup exporters
            if self.config.jaeger_endpoint:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=self.config.jaeger_agent_host,
                    agent_port=self.config.jaeger_agent_port,
                    collector_endpoint=self.config.jaeger_endpoint
                )

                span_processor = BatchSpanProcessor(
                    jaeger_exporter,
                    max_export_batch_size=self.config.max_export_batch_size,
                    export_timeout_millis=self.config.export_timeout * 1000
                )

                tracer_provider.add_span_processor(span_processor)
                self.logger.info(f"Jaeger tracing configured: {self.config.jaeger_endpoint}")

            # Get tracer
            self._tracer = trace.get_tracer(__name__)

            # Setup automatic instrumentation
            self._setup_auto_instrumentation()

            self.logger.info("Distributed tracing initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to setup tracing: {e}")
            self._tracer = None

    def _setup_auto_instrumentation(self):
        """Setup automatic instrumentation for common libraries"""
        try:
            # FastAPI instrumentation
            FastAPIInstrumentor().instrument()

            # Database instrumentation
            AsyncPGInstrumentor().instrument()

            # Redis instrumentation
            RedisInstrumentor().instrument()

            # HTTP requests instrumentation
            RequestsInstrumentor().instrument()

            self.logger.debug("Automatic instrumentation configured")

        except Exception as e:
            self.logger.warning(f"Some automatic instrumentation failed: {e}")

    @property
    def tracer(self) -> Optional[trace.Tracer]:
        """Get the tracer instance"""
        return self._tracer

    def start_span(
        self,
        name: str,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ) -> trace.Span:
        """Start a new span"""
        if not self._tracer:
            return trace.NonRecordingSpan(trace.SpanContext(0, 0, False))

        span = self._tracer.start_span(name, kind=kind, attributes=attributes or {})
        return span

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing operations"""
        if not self._tracer:
            yield None
            return

        with self._tracer.start_as_current_span(
            operation_name,
            kind=kind,
            attributes=attributes or {}
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def trace_cost_analysis(
        self,
        cost_center: Optional[str] = None,
        resource_count: Optional[int] = None,
        time_range_days: Optional[int] = None
    ):
        """Trace cost analysis operations"""
        attributes = {
            "finops.operation": "cost_analysis",
            "finops.operation_type": "business"
        }

        if cost_center:
            attributes["finops.cost_center"] = cost_center
        if resource_count:
            attributes["finops.resource_count"] = resource_count
        if time_range_days:
            attributes["finops.time_range_days"] = time_range_days

        return self.trace_operation(
            "finops.cost_analysis",
            kind=trace.SpanKind.INTERNAL,
            attributes=attributes
        )

    def trace_optimization(
        self,
        optimization_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        potential_savings: Optional[float] = None
    ):
        """Trace optimization operations"""
        attributes = {
            "finops.operation": "optimization",
            "finops.operation_type": "business"
        }

        if optimization_type:
            attributes["finops.optimization_type"] = optimization_type
        if resource_id:
            attributes["finops.resource_id"] = resource_id
        if potential_savings:
            attributes["finops.potential_savings"] = potential_savings

        return self.trace_operation(
            "finops.optimization",
            kind=trace.SpanKind.INTERNAL,
            attributes=attributes
        )

    def trace_budget_operation(
        self,
        budget_id: Optional[str] = None,
        cost_center: Optional[str] = None,
        utilization: Optional[float] = None
    ):
        """Trace budget operations"""
        attributes = {
            "finops.operation": "budget_management",
            "finops.operation_type": "business"
        }

        if budget_id:
            attributes["finops.budget_id"] = budget_id
        if cost_center:
            attributes["finops.cost_center"] = cost_center
        if utilization:
            attributes["finops.budget_utilization"] = utilization

        return self.trace_operation(
            "finops.budget_management",
            kind=trace.SpanKind.INTERNAL,
            attributes=attributes
        )

    def trace_database_operation(
        self,
        operation: str,
        table: Optional[str] = None,
        query_type: Optional[str] = None
    ):
        """Trace database operations"""
        attributes = {
            "db.operation": operation,
            "db.system": "postgresql"
        }

        if table:
            attributes["db.sql.table"] = table
        if query_type:
            attributes["db.operation.type"] = query_type

        return self.trace_operation(
            f"db.{operation}",
            kind=trace.SpanKind.CLIENT,
            attributes=attributes
        )

    def trace_external_api(
        self,
        service_name: str,
        operation: str,
        url: Optional[str] = None
    ):
        """Trace external API calls"""
        attributes = {
            "http.client": service_name,
            "external.operation": operation
        }

        if url:
            attributes["http.url"] = url

        return self.trace_operation(
            f"external.{service_name}.{operation}",
            kind=trace.SpanKind.CLIENT,
            attributes=attributes
        )

    def add_span_attributes(self, span: trace.Span, attributes: Dict[str, Any]):
        """Add attributes to an existing span"""
        if span and span.is_recording():
            for key, value in attributes.items():
                span.set_attribute(key, value)

    def add_span_event(
        self,
        span: trace.Span,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Add an event to an existing span"""
        if span and span.is_recording():
            span.add_event(name, attributes or {})

    def set_span_error(self, span: trace.Span, error: Exception):
        """Mark span as error and record exception"""
        if span and span.is_recording():
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.record_exception(error)

    def inject_trace_context(self, carrier: Dict[str, str]):
        """Inject trace context into carrier (for outgoing requests)"""
        if self._tracer:
            inject(carrier)

    def extract_trace_context(self, carrier: Dict[str, str]):
        """Extract trace context from carrier (for incoming requests)"""
        if self._tracer:
            return extract(carrier)
        return None


def trace_function(
    operation_name: Optional[str] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
):
    """Decorator for tracing functions"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.trace_operation(span_name, kind, attributes) as span:
                try:
                    # Add function metadata
                    if span:
                        tracer.add_span_attributes(span, {
                            "code.function": func.__name__,
                            "code.namespace": func.__module__,
                        })

                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    if span:
                        tracer.set_span_error(span, e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.trace_operation(span_name, kind, attributes) as span:
                try:
                    # Add function metadata
                    if span:
                        tracer.add_span_attributes(span, {
                            "code.function": func.__name__,
                            "code.namespace": func.__module__,
                        })

                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    if span:
                        tracer.set_span_error(span, e)
                    raise

        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def trace_cost_analysis(
    cost_center: Optional[str] = None,
    resource_count: Optional[int] = None,
    time_range_days: Optional[int] = None
):
    """Decorator for tracing cost analysis operations"""
    return trace_function(
        operation_name="finops.cost_analysis",
        attributes={
            "finops.operation": "cost_analysis",
            "finops.cost_center": cost_center,
            "finops.resource_count": resource_count,
            "finops.time_range_days": time_range_days
        }
    )


def trace_optimization(
    optimization_type: Optional[str] = None,
    resource_id: Optional[str] = None
):
    """Decorator for tracing optimization operations"""
    return trace_function(
        operation_name="finops.optimization",
        attributes={
            "finops.operation": "optimization",
            "finops.optimization_type": optimization_type,
            "finops.resource_id": resource_id
        }
    )


def trace_budget_operation(
    budget_id: Optional[str] = None,
    cost_center: Optional[str] = None
):
    """Decorator for tracing budget operations"""
    return trace_function(
        operation_name="finops.budget_management",
        attributes={
            "finops.operation": "budget_management",
            "finops.budget_id": budget_id,
            "finops.cost_center": cost_center
        }
    )


# Global tracer instance
_tracer: Optional[FinOpsTracer] = None


def setup_tracing(config: Optional[TracingConfig] = None) -> None:
    """Setup global tracing"""
    global _tracer

    if config is None:
        config = TracingConfig()

    _tracer = FinOpsTracer(config)


def get_tracer() -> FinOpsTracer:
    """Get global tracer instance"""
    global _tracer

    if _tracer is None:
        setup_tracing()

    return _tracer


def get_current_span() -> trace.Span:
    """Get current active span"""
    return trace.get_current_span()


def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    span = trace.get_current_span()
    if span and span.is_recording():
        trace_id = span.get_span_context().trace_id
        return f"{trace_id:032x}"
    return None


def get_span_id() -> Optional[str]:
    """Get current span ID"""
    span = trace.get_current_span()
    if span and span.is_recording():
        span_id = span.get_span_context().span_id
        return f"{span_id:016x}"
    return None


# Context manager for manual span management
@contextmanager
def trace_span(
    name: str,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
):
    """Context manager for creating spans"""
    tracer = get_tracer()
    with tracer.trace_operation(name, kind, attributes) as span:
        yield span


# Performance monitoring utilities
class PerformanceTracer:
    """Performance-focused tracing utilities"""

    @staticmethod
    @contextmanager
    def trace_performance(operation_name: str, threshold_ms: float = 1000.0):
        """Trace operation performance with threshold alerting"""
        tracer = get_tracer()
        start_time = time.time()

        with tracer.trace_operation(f"perf.{operation_name}") as span:
            try:
                yield span
            finally:
                duration_ms = (time.time() - start_time) * 1000

                if span:
                    tracer.add_span_attributes(span, {
                        "performance.duration_ms": duration_ms,
                        "performance.is_slow": duration_ms > threshold_ms,
                        "performance.threshold_ms": threshold_ms
                    })

                    if duration_ms > threshold_ms:
                        tracer.add_span_event(span, "slow_operation", {
                            "duration_ms": duration_ms,
                            "threshold_ms": threshold_ms
                        })

    @staticmethod
    def trace_database_performance(table: str, operation: str):
        """Trace database operation performance"""
        return PerformanceTracer.trace_performance(
            f"db.{table}.{operation}",
            threshold_ms=500.0  # Database operations should be faster
        )

    @staticmethod
    def trace_api_performance(endpoint: str, method: str):
        """Trace API endpoint performance"""
        return PerformanceTracer.trace_performance(
            f"api.{method}.{endpoint}",
            threshold_ms=2000.0  # API calls can be slower
        )
