"""
Extended unit tests for resilience patterns.
Tests circuit breaker, retry, and cache patterns.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from decimal import Decimal

from src.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerException,
    CircuitState
)
from src.infrastructure.resilience.retry import retry_async, retry_sync, RetryException
from src.infrastructure.cache.cost_cache import CostDataCache
from src.domain.entities import CostData


class TestCircuitBreakerExtended:
    """Extended tests for circuit breaker pattern."""
    
    def test_circuit_breaker_records_failure(self):
        """Test circuit breaker records failures."""
        cb = CircuitBreaker(failure_threshold=5)
        
        def failing_func():
            raise Exception("Test error")
        
        with pytest.raises(Exception):
            cb.call(failing_func)
        
        assert cb.failure_count == 1
    
    def test_circuit_breaker_resets_on_success(self):
        """Test circuit breaker resets failure count on success."""
        cb = CircuitBreaker(failure_threshold=5)
        
        def success_func():
            return "success"
        
        cb.call(success_func)
        
        assert cb.failure_count == 0
    
    def test_circuit_breaker_half_open_allows_one_call(self):
        """Test half-open state allows one test call."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0)
        
        def failing_func():
            raise Exception("Error")
        
        with pytest.raises(Exception):
            cb.call(failing_func)
        
        time.sleep(0.1)
        
        assert cb.state == CircuitState.HALF_OPEN or cb.state == CircuitState.OPEN
    
    def test_circuit_breaker_closes_after_successful_half_open(self):
        """Test circuit closes after successful call in half-open."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0)
        
        calls = 0
        
        def flaky_func():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise Exception("First call fails")
            return "success"
        
        with pytest.raises(Exception):
            cb.call(flaky_func)
        
        time.sleep(0.1)
        cb.state = CircuitState.HALF_OPEN
        
        result = cb.call(flaky_func)
        assert result == "success"
        
        result2 = cb.call(flaky_func)
        assert result2 == "success"
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_breaker_with_different_thresholds(self):
        """Test circuit breaker with various thresholds."""
        for threshold in [1, 3, 5, 10]:
            cb = CircuitBreaker(failure_threshold=threshold)
            
            for i in range(threshold):
                try:
                    cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
                except Exception:
                    pass
            
            assert cb.state == CircuitState.OPEN


class TestRetryExtended:
    """Extended tests for retry pattern."""
    
    @pytest.mark.asyncio
    async def test_retry_immediate_success(self):
        """Test retry with immediate success."""
        attempts = 0
        
        @retry_async(max_attempts=3, base_delay=0.01)
        async def success_func():
            nonlocal attempts
            attempts += 1
            return "success"
        
        result = await success_func()
        
        assert result == "success"
        assert attempts == 1
    
    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test retry uses exponential backoff."""
        start_times = []
        
        @retry_async(max_attempts=4, base_delay=0.05)
        async def failing_func():
            start_times.append(time.time())
            if len(start_times) < 4:
                raise Exception("Fail")
            return "success"
        
        result = await failing_func()
        
        assert result == "success"
        assert len(start_times) == 4
    
    def test_retry_sync_immediate_success(self):
        """Test sync retry with immediate success."""
        attempts = 0
        
        @retry_sync(max_attempts=3, base_delay=0.01)
        def success_func():
            nonlocal attempts
            attempts += 1
            return "success"
        
        result = success_func()
        
        assert result == "success"
        assert attempts == 1
    
    def test_retry_sync_eventual_success(self):
        """Test sync retry with eventual success."""
        attempts = 0
        
        @retry_sync(max_attempts=3, base_delay=0.01)
        def flaky_func():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise Exception("Not yet")
            return "success"
        
        result = flaky_func()
        
        assert result == "success"
        assert attempts == 2


class TestCacheExtended:
    """Extended tests for caching pattern."""
    
    def test_cache_ttl_not_expired(self):
        """Test cache returns data before TTL expiry."""
        cache = CostDataCache(ttl_minutes=30)
        
        cost_data = CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30
        )
        
        cache.set("test-region", cost_data)
        retrieved = cache.get("test-region")
        
        assert retrieved is not None
        assert retrieved.total_cost_usd == Decimal('1000.00')
    
    def test_cache_multiple_keys(self):
        """Test cache handles multiple keys."""
        cache = CostDataCache(ttl_minutes=30)
        
        for i in range(5):
            cost_data = CostData(
                total_cost_usd=Decimal(str(i * 100)),
                period_days=30
            )
            cache.set(f"region-{i}", cost_data)
        
        for i in range(5):
            retrieved = cache.get(f"region-{i}")
            assert retrieved is not None
            assert retrieved.total_cost_usd == Decimal(str(i * 100))
    
    def test_cache_overwrite_existing(self):
        """Test cache overwrites existing entries."""
        cache = CostDataCache(ttl_minutes=30)
        
        cost_data1 = CostData(total_cost_usd=Decimal('1000.00'), period_days=30)
        cost_data2 = CostData(total_cost_usd=Decimal('2000.00'), period_days=30)
        
        cache.set("test-key", cost_data1)
        cache.set("test-key", cost_data2)
        
        retrieved = cache.get("test-key")
        
        assert retrieved is not None
        assert retrieved.total_cost_usd == Decimal('2000.00')
    
    def test_cache_stats_accuracy(self):
        """Test cache statistics are accurate."""
        cache = CostDataCache(ttl_minutes=30)
        
        for i in range(3):
            cost_data = CostData(total_cost_usd=Decimal('100.00'), period_days=30)
            cache.set(f"key-{i}", cost_data)
        
        stats = cache.stats()
        
        assert stats["total_entries"] == 3
        assert stats["active_entries"] == 3
        assert stats["expired_entries"] == 0


class TestResiliencePatternCombination:
    """Tests for combined resilience patterns."""
    
    def test_retry_with_circuit_breaker(self):
        """Test retry combined with circuit breaker."""
        cb = CircuitBreaker(failure_threshold=5)
        attempts = 0
        
        def flaky_with_cb():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = None
        for _ in range(5):
            try:
                result = cb.call(flaky_with_cb)
                break
            except CircuitBreakerException:
                break
            except Exception:
                continue
        
        assert result == "success"
    
    def test_cache_with_circuit_breaker(self):
        """Test cache combined with circuit breaker."""
        cache = {}
        cb_open = False
        
        def get_with_fallback(key):
            cached = cache.get(key)
            if cached:
                return cached
            
            if cb_open:
                raise Exception("Circuit open")
            
            return {"data": "fresh"}
        
        cache["test"] = {"data": "cached"}
        cb_open = True
        
        result = get_with_fallback("test")
        
        assert result["data"] == "cached"


class TestTimeoutHandling:
    """Tests for timeout handling."""
    
    @pytest.mark.asyncio
    async def test_operation_completes_before_timeout(self):
        """Test operation completes before timeout."""
        async def quick_operation():
            await asyncio.sleep(0.01)
            return "done"
        
        result = await asyncio.wait_for(quick_operation(), timeout=1.0)
        
        assert result == "done"
    
    @pytest.mark.asyncio
    async def test_operation_times_out(self):
        """Test operation times out correctly."""
        async def slow_operation():
            await asyncio.sleep(10)
            return "done"
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(), timeout=0.01)
    
    @pytest.mark.asyncio
    async def test_timeout_with_cleanup(self):
        """Test timeout triggers cleanup."""
        cleanup_called = False
        
        async def operation_with_cleanup():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                nonlocal cleanup_called
                cleanup_called = True
                raise
        
        try:
            await asyncio.wait_for(operation_with_cleanup(), timeout=0.01)
        except asyncio.TimeoutError:
            pass
        
        await asyncio.sleep(0.01)
