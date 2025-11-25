"""Circuit breaker implementation for fault tolerance."""

from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, TypeVar, Optional
import asyncio
import logging

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failed, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerException(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern for handling failures gracefully.
    
    States:
    - CLOSED: Requests pass through normally
    - OPEN: Requests rejected immediately after failure threshold
    - HALF_OPEN: Limited requests allowed to test recovery
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        expected_exception: type = Exception,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout_seconds: Time to wait before attempting recovery
            expected_exception: Exception type to track
            logger: Logger instance
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.expected_exception = expected_exception
        self.logger = logger or logging.getLogger(__name__)
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.state != CircuitState.OPEN:
            return False
        
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout_seconds

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection."""
        # Check if we should attempt recovery
        if self._should_attempt_reset():
            self.state = CircuitState.HALF_OPEN
            self.logger.info(f"Circuit breaker entering HALF_OPEN state")
        
        # Reject if open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerException(
                f"Circuit breaker is OPEN. Service unavailable. "
                f"Retry after {self.recovery_timeout_seconds}s"
            )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    async def call_async(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """Execute async function with circuit breaker protection."""
        # Check if we should attempt recovery
        if self._should_attempt_reset():
            self.state = CircuitState.HALF_OPEN
            self.logger.info(f"Circuit breaker entering HALF_OPEN state")
        
        # Reject if open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerException(
                f"Circuit breaker is OPEN. Service unavailable. "
                f"Retry after {self.recovery_timeout_seconds}s"
            )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # 2 successful calls to close
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.logger.info("Circuit breaker closed - service recovered")
        else:
            self.success_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.success_count = 0
        
        self.logger.warning(
            f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}"
        )
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.error(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
