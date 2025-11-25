"""
Unit tests for resilience infrastructure.
Tests actual CircuitBreaker, Retry, and Cache implementations.
"""

import pytest
import asyncio
import time
from decimal import Decimal
from datetime import datetime

from src.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerException,
    CircuitState
)
from src.infrastructure.resilience.retry import retry_async, retry_sync, RetryException
from src.infrastructure.cache.cost_cache import CostDataCache
from src.domain.entities import CostData


class TestCircuitBreakerReal:
    """Tests for actual CircuitBreaker implementation."""
    
    def test_initial_state_is_closed(self):
        """Test circuit breaker starts closed."""
        cb = CircuitBreaker(failure_threshold=3)
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_successful_call_passes_through(self):
        """Test successful calls pass through circuit breaker."""
        cb = CircuitBreaker(failure_threshold=3)
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED
    
    def test_failure_increments_count(self):
        """Test failures increment failure count."""
        cb = CircuitBreaker(failure_threshold=3)
        
        def fail_func():
            raise ValueError("Test failure")
        
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED
    
    def test_opens_after_threshold_failures(self):
        """Test circuit opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)
        
        def fail_func():
            raise ValueError("Failure")
        
        for i in range(3):
            with pytest.raises(ValueError):
                cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
    
    def test_open_circuit_rejects_calls(self):
        """Test open circuit rejects calls immediately."""
        cb = CircuitBreaker(failure_threshold=1)
        
        def fail_func():
            raise ValueError("Failure")
        
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        
        def should_not_run():
            return "should not reach"
        
        with pytest.raises(CircuitBreakerException):
            cb.call(should_not_run)
    
    def test_success_resets_failure_count(self):
        """Test successful call resets failure count."""
        cb = CircuitBreaker(failure_threshold=5)
        
        def fail_func():
            raise ValueError("Failure")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(fail_func)
        
        assert cb.failure_count == 2
        
        def success_func():
            return "ok"
        
        cb.call(success_func)
        
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_async_call_success(self):
        """Test async call passes through."""
        cb = CircuitBreaker(failure_threshold=3)
        
        async def async_success():
            await asyncio.sleep(0.001)
            return "async success"
        
        result = await cb.call_async(async_success)
        
        assert result == "async success"
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_async_call_failure(self):
        """Test async call failure is tracked."""
        cb = CircuitBreaker(failure_threshold=2)
        
        async def async_fail():
            raise RuntimeError("Async failure")
        
        with pytest.raises(RuntimeError):
            await cb.call_async(async_fail)
        
        assert cb.failure_count == 1
        
        with pytest.raises(RuntimeError):
            await cb.call_async(async_fail)
        
        assert cb.state == CircuitState.OPEN


class TestRetryPatternReal:
    """Tests for actual Retry implementation."""
    
    @pytest.mark.asyncio
    async def test_retry_async_immediate_success(self):
        """Test async retry with immediate success."""
        call_count = 0
        
        @retry_async(max_attempts=3, base_delay=0.01)
        async def success_operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await success_operation()
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_async_eventual_success(self):
        """Test async retry with eventual success."""
        call_count = 0
        
        @retry_async(max_attempts=3, base_delay=0.01)
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "finally success"
        
        result = await flaky_operation()
        
        assert result == "finally success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_async_exhausted_raises(self):
        """Test async retry raises after exhausting attempts."""
        @retry_async(max_attempts=2, base_delay=0.01)
        async def always_fail():
            raise RuntimeError("Always fails")
        
        with pytest.raises(RetryException):
            await always_fail()
    
    def test_retry_sync_immediate_success(self):
        """Test sync retry with immediate success."""
        call_count = 0
        
        @retry_sync(max_attempts=3, base_delay=0.01)
        def sync_success():
            nonlocal call_count
            call_count += 1
            return "sync success"
        
        result = sync_success()
        
        assert result == "sync success"
        assert call_count == 1
    
    def test_retry_sync_eventual_success(self):
        """Test sync retry with eventual success."""
        call_count = 0
        
        @retry_sync(max_attempts=3, base_delay=0.01)
        def flaky_sync():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise IOError("Temporary")
            return "recovered"
        
        result = flaky_sync()
        
        assert result == "recovered"
        assert call_count == 2


class TestCostDataCacheReal:
    """Tests for actual CostDataCache implementation."""
    
    def test_cache_stores_and_retrieves(self):
        """Test cache stores and retrieves CostData."""
        cache = CostDataCache(ttl_minutes=30)
        
        cost_data = CostData(
            total_cost_usd=Decimal('5000.00'),
            period_days=30,
            cost_by_service={'EC2': Decimal('3000.00'), 'RDS': Decimal('2000.00')}
        )
        
        cache.set("us-east-1", cost_data)
        retrieved = cache.get("us-east-1")
        
        assert retrieved is not None
        assert retrieved.total_cost_usd == Decimal('5000.00')
        assert retrieved.period_days == 30
    
    def test_cache_returns_none_for_missing(self):
        """Test cache returns None for missing keys."""
        cache = CostDataCache(ttl_minutes=30)
        
        result = cache.get("nonexistent-region")
        
        assert result is None
    
    def test_cache_expiry(self):
        """Test cache expires entries after TTL."""
        cache = CostDataCache(ttl_minutes=0)
        
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=7
        )
        
        cache.set("us-west-2", cost_data)
        time.sleep(0.1)
        
        result = cache.get("us-west-2")
        
        assert result is None
    
    def test_cache_clear(self):
        """Test cache clear removes all entries."""
        cache = CostDataCache(ttl_minutes=30)
        
        for i in range(5):
            cost_data = CostData(
                total_cost_usd=Decimal(str(i * 1000)),
                period_days=30
            )
            cache.set(f"region-{i}", cost_data)
        
        cache.clear()
        
        for i in range(5):
            assert cache.get(f"region-{i}") is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CostDataCache(ttl_minutes=30)
        
        for i in range(3):
            cost_data = CostData(
                total_cost_usd=Decimal('1000.00'),
                period_days=30
            )
            cache.set(f"key-{i}", cost_data)
        
        stats = cache.stats()
        
        assert "total_entries" in stats
        assert stats["total_entries"] == 3
        assert "active_entries" in stats
        assert stats["active_entries"] == 3
    
    def test_cache_overwrite(self):
        """Test cache overwrites existing entries."""
        cache = CostDataCache(ttl_minutes=30)
        
        cost_data_1 = CostData(total_cost_usd=Decimal('1000.00'), period_days=30)
        cost_data_2 = CostData(total_cost_usd=Decimal('2000.00'), period_days=30)
        
        cache.set("test-key", cost_data_1)
        cache.set("test-key", cost_data_2)
        
        retrieved = cache.get("test-key")
        
        assert retrieved is not None
        assert retrieved.total_cost_usd == Decimal('2000.00')


class TestResilienceCombination:
    """Tests for combining resilience patterns."""
    
    def test_circuit_breaker_with_retry_logic(self):
        """Test circuit breaker works with manual retry."""
        cb = CircuitBreaker(failure_threshold=5)
        attempts = 0
        
        def flaky_operation():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("Connection failed")
            return "connected"
        
        result = None
        for _ in range(5):
            try:
                result = cb.call(flaky_operation)
                break
            except ConnectionError:
                continue
            except CircuitBreakerException:
                break
        
        assert result == "connected"
        assert attempts == 3
    
    def test_cache_as_fallback(self):
        """Test cache as fallback when primary fails."""
        cache = CostDataCache(ttl_minutes=30)
        
        cached_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30
        )
        cache.set("fallback-region", cached_data)
        
        def get_with_fallback():
            try:
                raise ConnectionError("API unavailable")
            except ConnectionError:
                return cache.get("fallback-region")
        
        result = get_with_fallback()
        
        assert result is not None
        assert result.total_cost_usd == Decimal('1000.00')
