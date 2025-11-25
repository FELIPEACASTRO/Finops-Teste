"""
Resilience Patterns Implementation
Following KNOWLEDGE_BASE.md specifications for circuit breaker, retry, and fallback patterns

Implements:
- Circuit Breaker pattern for preventing cascade failures
- Retry with exponential backoff
- Fallback mechanisms
- Timeout handling
- Health checks
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: float = 30.0  # Request timeout in seconds
    expected_exception: type = Exception


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeouts: int = 0
    circuit_breaker_opens: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Circuit breaker implementation following the pattern from KNOWLEDGE_BASE.md"""
    
    def __init__(self, config: CircuitBreakerConfig, name: str = "default"):
        self.config = config
        self.name = name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.metrics = CircuitBreakerMetrics()
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            self.metrics.total_requests += 1
            
            # Check if circuit breaker should open
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN state")
                else:
                    self.metrics.circuit_breaker_opens += 1
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Last failure: {self.last_failure_time}"
                    )
        
        # Execute the function
        try:
            # Apply timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            # Handle success
            await self._on_success()
            return result
            
        except asyncio.TimeoutError:
            self.metrics.timeouts += 1
            await self._on_failure(f"Timeout after {self.config.timeout}s")
            raise
        except self.config.expected_exception as e:
            await self._on_failure(str(e))
            raise
        except Exception as e:
            await self._on_failure(f"Unexpected error: {str(e)}")
            raise
    
    async def _on_success(self):
        """Handle successful execution"""
        async with self._lock:
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = datetime.utcnow()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to CLOSED state")
            else:
                self.failure_count = 0
    
    async def _on_failure(self, error_message: str):
        """Handle failed execution"""
        async with self._lock:
            self.metrics.failed_requests += 1
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            self.metrics.last_failure_time = self.last_failure_time
            
            logger.warning(
                f"Circuit breaker '{self.name}' failure #{self.failure_count}: {error_message}"
            )
            
            if (self.state == CircuitBreakerState.CLOSED and 
                self.failure_count >= self.config.failure_threshold):
                self.state = CircuitBreakerState.OPEN
                self.metrics.circuit_breaker_opens += 1
                logger.error(f"Circuit breaker '{self.name}' moved to OPEN state")
            elif self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                logger.error(f"Circuit breaker '{self.name}' moved back to OPEN state")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state"""
        return self.state
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get circuit breaker metrics"""
        return self.metrics


class RetryConfig:
    """Configuration for retry mechanism"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


class RetryExhaustedException(Exception):
    """Exception raised when all retry attempts are exhausted"""
    pass


class RetryMechanism:
    """Retry mechanism with exponential backoff"""
    
    def __init__(self, config: RetryConfig, name: str = "default"):
        self.config = config
        self.name = name
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Retry '{self.name}' attempt {attempt}/{self.config.max_attempts}")
                
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"Retry '{self.name}' succeeded on attempt {attempt}")
                
                return result
                
            except self.config.retryable_exceptions as e:
                last_exception = e
                logger.warning(f"Retry '{self.name}' attempt {attempt} failed: {str(e)}")
                
                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.debug(f"Retry '{self.name}' waiting {delay:.2f}s before next attempt")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Retry '{self.name}' exhausted all {self.config.max_attempts} attempts")
            
            except Exception as e:
                # Non-retryable exception
                logger.error(f"Retry '{self.name}' non-retryable exception: {str(e)}")
                raise
        
        raise RetryExhaustedException(
            f"Retry '{self.name}' failed after {self.config.max_attempts} attempts. "
            f"Last error: {str(last_exception)}"
        ) from last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff"""
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add jitter to prevent thundering herd
            import random
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


class FallbackStrategy(ABC):
    """Abstract fallback strategy"""
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute fallback logic"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get fallback strategy name"""
        pass


class CachedDataFallback(FallbackStrategy):
    """Fallback strategy using cached data"""
    
    def __init__(self, cache_service: 'CacheService', cache_key: str, max_age_seconds: int = 3600):
        self.cache_service = cache_service
        self.cache_key = cache_key
        self.max_age_seconds = max_age_seconds
    
    async def execute(self, *args, **kwargs) -> Any:
        """Return cached data as fallback"""
        cached_data = await self.cache_service.get(self.cache_key)
        
        if cached_data is None:
            raise Exception(f"No cached data available for key: {self.cache_key}")
        
        # Check cache age
        cache_timestamp = cached_data.get('timestamp')
        if cache_timestamp:
            cache_age = datetime.utcnow().timestamp() - cache_timestamp
            if cache_age > self.max_age_seconds:
                logger.warning(f"Cached data is {cache_age:.0f}s old (max: {self.max_age_seconds}s)")
        
        logger.info(f"Using cached data fallback for key: {self.cache_key}")
        return cached_data.get('data')
    
    def get_name(self) -> str:
        return f"CachedDataFallback({self.cache_key})"


class DefaultValueFallback(FallbackStrategy):
    """Fallback strategy returning default value"""
    
    def __init__(self, default_value: Any):
        self.default_value = default_value
    
    async def execute(self, *args, **kwargs) -> Any:
        """Return default value as fallback"""
        logger.info(f"Using default value fallback: {self.default_value}")
        return self.default_value
    
    def get_name(self) -> str:
        return f"DefaultValueFallback({self.default_value})"


class AlternativeServiceFallback(FallbackStrategy):
    """Fallback strategy using alternative service"""
    
    def __init__(self, alternative_func: Callable, name: str = "alternative"):
        self.alternative_func = alternative_func
        self.name = name
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute alternative service as fallback"""
        logger.info(f"Using alternative service fallback: {self.name}")
        
        if asyncio.iscoroutinefunction(self.alternative_func):
            return await self.alternative_func(*args, **kwargs)
        else:
            return self.alternative_func(*args, **kwargs)
    
    def get_name(self) -> str:
        return f"AlternativeServiceFallback({self.name})"


class ResilientService:
    """Service combining circuit breaker, retry, and fallback patterns"""
    
    def __init__(
        self,
        name: str,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        fallback_strategy: Optional[FallbackStrategy] = None
    ):
        self.name = name
        self.circuit_breaker = CircuitBreaker(
            circuit_breaker_config or CircuitBreakerConfig(),
            name
        ) if circuit_breaker_config else None
        
        self.retry_mechanism = RetryMechanism(
            retry_config or RetryConfig(),
            name
        ) if retry_config else None
        
        self.fallback_strategy = fallback_strategy
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with full resilience patterns"""
        try:
            if self.circuit_breaker and self.retry_mechanism:
                # Combine circuit breaker with retry
                return await self.circuit_breaker.call(
                    self.retry_mechanism.execute,
                    func, *args, **kwargs
                )
            elif self.circuit_breaker:
                # Circuit breaker only
                return await self.circuit_breaker.call(func, *args, **kwargs)
            elif self.retry_mechanism:
                # Retry only
                return await self.retry_mechanism.execute(func, *args, **kwargs)
            else:
                # No resilience patterns
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
        except Exception as e:
            if self.fallback_strategy:
                logger.warning(f"Primary execution failed for '{self.name}', using fallback: {str(e)}")
                try:
                    return await self.fallback_strategy.execute(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for '{self.name}': {str(fallback_error)}")
                    raise e  # Raise original exception
            else:
                raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the resilient service"""
        status = {
            "name": self.name,
            "healthy": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.circuit_breaker:
            cb_state = self.circuit_breaker.get_state()
            cb_metrics = self.circuit_breaker.get_metrics()
            
            status["circuit_breaker"] = {
                "state": cb_state.value,
                "healthy": cb_state != CircuitBreakerState.OPEN,
                "metrics": {
                    "total_requests": cb_metrics.total_requests,
                    "successful_requests": cb_metrics.successful_requests,
                    "failed_requests": cb_metrics.failed_requests,
                    "success_rate": (
                        cb_metrics.successful_requests / cb_metrics.total_requests * 100
                        if cb_metrics.total_requests > 0 else 0
                    ),
                    "circuit_breaker_opens": cb_metrics.circuit_breaker_opens
                }
            }
            
            if cb_state == CircuitBreakerState.OPEN:
                status["healthy"] = False
        
        if self.fallback_strategy:
            status["fallback"] = {
                "strategy": self.fallback_strategy.get_name(),
                "available": True
            }
        
        return status


# Decorator for easy resilience application
def resilient(
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    retry_config: Optional[RetryConfig] = None,
    fallback_strategy: Optional[FallbackStrategy] = None,
    name: Optional[str] = None
):
    """Decorator to make functions resilient"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        function_name = name or f"{func.__module__}.{func.__name__}"
        resilient_service = ResilientService(
            function_name,
            circuit_breaker_config,
            retry_config,
            fallback_strategy
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await resilient_service.execute(func, *args, **kwargs)
        
        # Add health check method to wrapper
        wrapper.get_health_status = resilient_service.get_health_status
        
        return wrapper
    
    return decorator


# Health Check System
class HealthCheck:
    """Health check for services"""
    
    def __init__(self, name: str, check_func: Callable[[], bool], timeout: float = 5.0):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.last_check_time: Optional[datetime] = None
        self.last_check_result: bool = True
        self.consecutive_failures: int = 0
    
    async def check(self) -> Dict[str, Any]:
        """Perform health check"""
        start_time = time.time()
        
        try:
            if asyncio.iscoroutinefunction(self.check_func):
                result = await asyncio.wait_for(self.check_func(), timeout=self.timeout)
            else:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, self.check_func),
                    timeout=self.timeout
                )
            
            duration = time.time() - start_time
            self.last_check_time = datetime.utcnow()
            self.last_check_result = bool(result)
            
            if self.last_check_result:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
            
            return {
                "name": self.name,
                "healthy": self.last_check_result,
                "duration_ms": round(duration * 1000, 2),
                "timestamp": self.last_check_time.isoformat(),
                "consecutive_failures": self.consecutive_failures
            }
            
        except asyncio.TimeoutError:
            self.consecutive_failures += 1
            self.last_check_result = False
            self.last_check_time = datetime.utcnow()
            
            return {
                "name": self.name,
                "healthy": False,
                "error": f"Health check timeout after {self.timeout}s",
                "timestamp": self.last_check_time.isoformat(),
                "consecutive_failures": self.consecutive_failures
            }
            
        except Exception as e:
            self.consecutive_failures += 1
            self.last_check_result = False
            self.last_check_time = datetime.utcnow()
            
            return {
                "name": self.name,
                "healthy": False,
                "error": str(e),
                "timestamp": self.last_check_time.isoformat(),
                "consecutive_failures": self.consecutive_failures
            }


class HealthCheckRegistry:
    """Registry for health checks"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
    
    def register(self, health_check: HealthCheck):
        """Register a health check"""
        self.health_checks[health_check.name] = health_check
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        for name, health_check in self.health_checks.items():
            result = await health_check.check()
            results[name] = result
            
            if not result["healthy"]:
                overall_healthy = False
        
        return {
            "healthy": overall_healthy,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }
    
    async def check_single(self, name: str) -> Optional[Dict[str, Any]]:
        """Run single health check"""
        health_check = self.health_checks.get(name)
        if not health_check:
            return None
        
        return await health_check.check()


# External Service Interfaces
class CacheService:
    """Interface for cache service"""
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data"""
        pass
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> None:
        """Set cached data"""
        pass