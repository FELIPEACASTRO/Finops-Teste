"""Unit tests for resilience patterns."""

import pytest
import asyncio
from src.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerException,
    CircuitState
)
from src.infrastructure.resilience.retry import retry_async, retry_sync, RetryException
from src.infrastructure.cache.cost_cache import CostDataCache
from src.domain.entities import CostData
from decimal import Decimal


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise Exception("Test error")
        
        # First failure
        with pytest.raises(Exception):
            cb.call(failing_func)
        assert cb.state == CircuitState.CLOSED
        
        # Second failure - opens circuit
        with pytest.raises(Exception):
            cb.call(failing_func)
        assert cb.state == CircuitState.OPEN
    
    def test_circuit_breaker_rejects_when_open(self):
        """Test circuit breaker rejects calls when open."""
        cb = CircuitBreaker(failure_threshold=1)
        
        def failing_func():
            raise Exception("Test error")
        
        # Open the circuit
        with pytest.raises(Exception):
            cb.call(failing_func)
        assert cb.state == CircuitState.OPEN
        
        # Now should reject immediately
        with pytest.raises(CircuitBreakerException):
            cb.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_async(self):
        """Test circuit breaker with async functions."""
        cb = CircuitBreaker(failure_threshold=1)
        
        async def failing_func():
            raise Exception("Test error")
        
        with pytest.raises(Exception):
            await cb.call_async(failing_func)
        
        assert cb.state == CircuitState.OPEN
        
        with pytest.raises(CircuitBreakerException):
            await cb.call_async(failing_func)


class TestRetry:
    """Tests for retry pattern."""
    
    @pytest.mark.asyncio
    async def test_retry_succeeds_on_third_attempt(self):
        """Test retry succeeds after failures."""
        attempts = 0
        
        @retry_async(max_attempts=3, base_delay=0.01)
        async def flaky_func():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise Exception("Not yet")
            return "Success"
        
        result = await flaky_func()
        assert result == "Success"
        assert attempts == 3
    
    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self):
        """Test retry fails after max attempts exceeded."""
        @retry_async(max_attempts=2, base_delay=0.01)
        async def always_fails():
            raise Exception("Always fails")
        
        with pytest.raises(RetryException):
            await always_fails()
    
    def test_retry_sync(self):
        """Test synchronous retry."""
        attempts = 0
        
        @retry_sync(max_attempts=3, base_delay=0.01)
        def flaky_func():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise Exception("Not yet")
            return "Success"
        
        result = flaky_func()
        assert result == "Success"


class TestCostDataCache:
    """Tests for cost data cache."""
    
    def test_cache_stores_and_retrieves(self):
        """Test cache stores and retrieves data."""
        cache = CostDataCache(ttl_minutes=30)
        
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30
        )
        
        cache.set("us-east-1", cost_data)
        retrieved = cache.get("us-east-1")
        
        assert retrieved is not None
        assert retrieved.total_cost_usd == Decimal('1000.00')
    
    def test_cache_returns_none_for_missing_key(self):
        """Test cache returns None for missing key."""
        cache = CostDataCache()
        assert cache.get("nonexistent") is None
    
    def test_cache_expires_old_entries(self):
        """Test cache expires old entries."""
        cache = CostDataCache(ttl_minutes=0)  # Immediate expiry
        
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30
        )
        
        cache.set("us-east-1", cost_data)
        
        # Should be expired immediately
        import time
        time.sleep(0.1)
        retrieved = cache.get("us-east-1")
        assert retrieved is None
    
    def test_cache_clear(self):
        """Test cache clear."""
        cache = CostDataCache()
        
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30
        )
        
        cache.set("us-east-1", cost_data)
        cache.clear()
        
        assert cache.get("us-east-1") is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CostDataCache(ttl_minutes=30)
        
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30
        )
        
        cache.set("us-east-1", cost_data)
        stats = cache.stats()
        
        assert stats["total_entries"] == 1
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 0
