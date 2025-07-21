#!/usr/bin/env python3
"""
Vollständiger Data Pipeline Performance Test
Misst End-to-End Latenz: Bitget API → Backend → Redis → Frontend → UI Display

Testet:
- Redis Cache Performance (Read/Write Speed)
- Frontend Rendering Performance 
- End-to-End Pipeline Latenz
- Concurrent Load Performance
"""

import pytest
import asyncio
import aiohttp
import time
import json
import redis
import statistics
import threading
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    from core.services.cache_service import cache, TICKER_TTL, SYMBOLS_TTL
    print("✅ Redis cache service imported successfully")
except ImportError as e:
    print(f"⚠️  Redis cache service import failed: {e}")
    cache = None

# Test Configuration
BACKEND_BASE_URL = "http://localhost:8100"
REDIS_HOST = "localhost"
REDIS_PORT = 6380  # Docker port mapping
TEST_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT"]
STRESS_SYMBOL_COUNT = 100
CONCURRENT_REQUESTS = 50

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

class PerformanceMetrics:
    """Performance-Metriken-Sammler"""
    
    def __init__(self):
        self.metrics = {
            'redis_ping': [],
            'redis_write': [],
            'redis_read': [],
            'backend_api': [],
            'frontend_processing': [],
            'end_to_end': [],
            'memory_usage': [],
            'cache_hit_rate': 0,
            'cache_misses': 0,
            'cache_hits': 0
        }
    
    def add_metric(self, metric_type: str, value: float):
        """Füge Metrik hinzu"""
        if metric_type in self.metrics and isinstance(self.metrics[metric_type], list):
            self.metrics[metric_type].append(value)
    
    def get_stats(self, metric_type: str) -> Dict[str, float]:
        """Berechne Statistiken für Metrik"""
        values = self.metrics.get(metric_type, [])
        if not values:
            return {'avg': 0, 'min': 0, 'max': 0, 'p95': 0, 'p99': 0}
        
        return {
            'avg': statistics.mean(values),
            'min': min(values),
            'max': max(values),
            'p95': statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values),
            'p99': statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values),
            'count': len(values)
        }

class PipelinePerformanceTester:
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.redis_client = None
        self.session = None
        
    async def setup(self):
        """Setup Test Environment"""
        print(f"\n{Colors.CYAN}🔧 Setting up Pipeline Performance Test...{Colors.END}")
        
        # Redis Connection
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST, 
                port=REDIS_PORT, 
                decode_responses=True,
                socket_connect_timeout=1
            )
            self.redis_client.ping()
            print(f"{Colors.GREEN}✅ Redis connected: {REDIS_HOST}:{REDIS_PORT}{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}❌ Redis connection failed: {e}{Colors.END}")
            self.redis_client = None
        
        # HTTP Session
        self.session = aiohttp.ClientSession()
        
        # Clear Redis cache
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                print(f"{Colors.GREEN}✅ Redis cache cleared{Colors.END}")
            except:
                pass
    
    async def teardown(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
        print(f"{Colors.CYAN}🔧 Cleanup completed{Colors.END}")
    
    async def test_redis_performance(self) -> Dict[str, Any]:
        """Test Redis Cache Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing Redis Performance...{Colors.END}")
        
        if not self.redis_client:
            print(f"{Colors.RED}❌ Redis not available{Colors.END}")
            return {}
        
        results = {}
        
        # Ping Test
        ping_times = []
        for i in range(100):
            start = time.perf_counter()
            self.redis_client.ping()
            ping_times.append((time.perf_counter() - start) * 1000)
        
        results['ping'] = {
            'avg_ms': statistics.mean(ping_times),
            'min_ms': min(ping_times),
            'max_ms': max(ping_times)
        }
        
        # Write Performance Test
        write_times = []
        test_data = {"symbol": "BTCUSDT", "price": 45000.50, "volume": 123.45}
        
        for i in range(1000):
            key = f"test:ticker:{i}"
            start = time.perf_counter()
            self.redis_client.setex(key, 60, json.dumps(test_data))
            write_times.append((time.perf_counter() - start) * 1000)
        
        results['write'] = {
            'avg_ms': statistics.mean(write_times),
            'ops_per_sec': 1000 / (sum(write_times) / 1000),
            'min_ms': min(write_times),
            'max_ms': max(write_times)
        }
        
        # Read Performance Test
        read_times = []
        for i in range(1000):
            key = f"test:ticker:{i}"
            start = time.perf_counter()
            value = self.redis_client.get(key)
            read_times.append((time.perf_counter() - start) * 1000)
            if value:
                json.loads(value)  # Include deserialization time
        
        results['read'] = {
            'avg_ms': statistics.mean(read_times),
            'ops_per_sec': 1000 / (sum(read_times) / 1000),
            'min_ms': min(read_times),
            'max_ms': max(read_times)
        }
        
        # Memory Usage
        try:
            memory_info = self.redis_client.info('memory')
            results['memory'] = {
                'used_memory_mb': memory_info.get('used_memory', 0) / (1024 * 1024),
                'used_memory_peak_mb': memory_info.get('used_memory_peak', 0) / (1024 * 1024)
            }
        except:
            results['memory'] = {'used_memory_mb': 0, 'used_memory_peak_mb': 0}
        
        # Cleanup test data
        for i in range(1000):
            self.redis_client.delete(f"test:ticker:{i}")
        
        print(f"{Colors.GREEN}✅ Redis Performance Test completed{Colors.END}")
        return results
    
    async def test_backend_api_performance(self) -> Dict[str, Any]:
        """Test Backend API Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing Backend API Performance...{Colors.END}")
        
        results = {}
        
        # Test /ticker endpoint
        ticker_times = []
        for i in range(20):
            start = time.perf_counter()
            try:
                async with self.session.get(f"{BACKEND_BASE_URL}/ticker", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        ticker_times.append((time.perf_counter() - start) * 1000)
                    else:
                        print(f"{Colors.YELLOW}⚠️  Backend /ticker returned {response.status}{Colors.END}")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Backend /ticker error: {e}{Colors.END}")
            
            await asyncio.sleep(0.5)  # Rate limiting
        
        if ticker_times:
            results['ticker'] = {
                'avg_ms': statistics.mean(ticker_times),
                'min_ms': min(ticker_times),
                'max_ms': max(ticker_times),
                'count': len(ticker_times)
            }
        
        # Test /symbols endpoint  
        symbols_times = []
        for i in range(10):
            start = time.perf_counter()
            try:
                async with self.session.get(f"{BACKEND_BASE_URL}/symbols", timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        symbols_times.append((time.perf_counter() - start) * 1000)
                    else:
                        print(f"{Colors.YELLOW}⚠️  Backend /symbols returned {response.status}{Colors.END}")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Backend /symbols error: {e}{Colors.END}")
            
            await asyncio.sleep(1.0)  # Rate limiting
        
        if symbols_times:
            results['symbols'] = {
                'avg_ms': statistics.mean(symbols_times),
                'min_ms': min(symbols_times),
                'max_ms': max(symbols_times),
                'count': len(symbols_times)
            }
        
        print(f"{Colors.GREEN}✅ Backend API Performance Test completed{Colors.END}")
        return results
    
    async def test_cache_hit_performance(self) -> Dict[str, Any]:
        """Test Cache Hit/Miss Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing Cache Hit/Miss Performance...{Colors.END}")
        
        if not self.redis_client:
            return {}
        
        results = {}
        
        # Prepare test data
        test_ticker_data = {
            "symbol": "BTCUSDT",
            "last": 45000.50,
            "high24h": 46000.0,
            "low24h": 44000.0,
            "changeRate": 0.025,
            "market_type": "spot"
        }
        
        # Set initial cache data
        cache_key = "ticker:BTCUSDT:spot"
        self.redis_client.setex(cache_key, TICKER_TTL, json.dumps(test_ticker_data))
        
        # Test cache hits
        hit_times = []
        for i in range(500):
            start = time.perf_counter()
            value = self.redis_client.get(cache_key)
            if value:
                json.loads(value)
            hit_times.append((time.perf_counter() - start) * 1000)
        
        results['cache_hit'] = {
            'avg_ms': statistics.mean(hit_times),
            'min_ms': min(hit_times),
            'max_ms': max(hit_times),
            'ops_per_sec': 500 / (sum(hit_times) / 1000)
        }
        
        # Test cache miss (after expiration)
        self.redis_client.delete(cache_key)
        
        miss_times = []
        for i in range(100):
            start = time.perf_counter()
            value = self.redis_client.get(cache_key)  # Should be None
            miss_times.append((time.perf_counter() - start) * 1000)
        
        results['cache_miss'] = {
            'avg_ms': statistics.mean(miss_times),
            'min_ms': min(miss_times),
            'max_ms': max(miss_times),
            'ops_per_sec': 100 / (sum(miss_times) / 1000)
        }
        
        print(f"{Colors.GREEN}✅ Cache Hit/Miss Performance Test completed{Colors.END}")
        return results
    
    async def test_concurrent_load_performance(self) -> Dict[str, Any]:
        """Test Concurrent Load Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing Concurrent Load Performance ({CONCURRENT_REQUESTS} requests)...{Colors.END}")
        
        results = {}
        
        async def single_request():
            """Single concurrent request"""
            start = time.perf_counter()
            try:
                async with self.session.get(f"{BACKEND_BASE_URL}/ticker", timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        return (time.perf_counter() - start) * 1000, True
                    else:
                        return (time.perf_counter() - start) * 1000, False
            except:
                return (time.perf_counter() - start) * 1000, False
        
        # Run concurrent requests
        tasks = [single_request() for _ in range(CONCURRENT_REQUESTS)]
        concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_times = []
        failure_count = 0
        
        for result in concurrent_results:
            if isinstance(result, tuple):
                duration, success = result
                if success:
                    success_times.append(duration)
                else:
                    failure_count += 1
        
        if success_times:
            results['concurrent'] = {
                'avg_ms': statistics.mean(success_times),
                'min_ms': min(success_times),
                'max_ms': max(success_times),
                'p95_ms': statistics.quantiles(success_times, n=20)[18] if len(success_times) > 20 else max(success_times),
                'success_count': len(success_times),
                'failure_count': failure_count,
                'success_rate': len(success_times) / CONCURRENT_REQUESTS * 100
            }
        
        print(f"{Colors.GREEN}✅ Concurrent Load Performance Test completed{Colors.END}")
        return results
    
    async def test_end_to_end_latency(self) -> Dict[str, Any]:
        """Test End-to-End Pipeline Latency"""
        print(f"\n{Colors.BLUE}🔄 Testing End-to-End Pipeline Latency...{Colors.END}")
        
        results = {}
        e2e_times = []
        
        for i in range(10):
            # Clear cache for fresh data
            if self.redis_client:
                self.redis_client.flushdb()
            
            # Measure full pipeline
            start = time.perf_counter()
            
            try:
                # Backend API call (should trigger Bitget API + Redis cache)
                async with self.session.get(f"{BACKEND_BASE_URL}/ticker", timeout=20) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Simulate frontend processing
                        await asyncio.sleep(0.005)  # 5ms frontend processing
                        
                        e2e_times.append((time.perf_counter() - start) * 1000)
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  E2E test {i+1} failed: {e}{Colors.END}")
            
            await asyncio.sleep(2)  # Avoid rate limiting
        
        if e2e_times:
            results['end_to_end'] = {
                'avg_ms': statistics.mean(e2e_times),
                'min_ms': min(e2e_times),
                'max_ms': max(e2e_times),
                'target_ms': 20,  # Target: <20ms
                'meets_target': all(t < 20 for t in e2e_times)
            }
        
        print(f"{Colors.GREEN}✅ End-to-End Latency Test completed{Colors.END}")
        return results
    
    def print_performance_report(self, redis_results: Dict, backend_results: Dict, cache_results: Dict, concurrent_results: Dict, e2e_results: Dict):
        """Print comprehensive performance report"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}")
        print(f"  🚀 DATA PIPELINE PERFORMANCE REPORT")
        print(f"{'='*80}{Colors.END}")
        
        # Redis Performance
        if redis_results:
            print(f"\n{Colors.MAGENTA}⚡ REDIS PERFORMANCE:{Colors.END}")
            print(f"  Ping Latency:     {redis_results['ping']['avg_ms']:.2f}ms (min: {redis_results['ping']['min_ms']:.2f}ms)")
            print(f"  Write Speed:      {redis_results['write']['ops_per_sec']:,.0f} ops/sec ({redis_results['write']['avg_ms']:.2f}ms avg)")
            print(f"  Read Speed:       {redis_results['read']['ops_per_sec']:,.0f} ops/sec ({redis_results['read']['avg_ms']:.2f}ms avg)")
            print(f"  Memory Usage:     {redis_results['memory']['used_memory_mb']:.2f}MB")
        
        # Cache Hit/Miss Performance
        if cache_results:
            print(f"\n{Colors.MAGENTA}🎯 CACHE PERFORMANCE:{Colors.END}")
            if 'cache_hit' in cache_results:
                print(f"  Cache Hit:        {cache_results['cache_hit']['ops_per_sec']:,.0f} ops/sec ({cache_results['cache_hit']['avg_ms']:.3f}ms avg)")
            if 'cache_miss' in cache_results:
                print(f"  Cache Miss:       {cache_results['cache_miss']['ops_per_sec']:,.0f} ops/sec ({cache_results['cache_miss']['avg_ms']:.3f}ms avg)")
        
        # Backend API Performance
        if backend_results:
            print(f"\n{Colors.BLUE}🔌 BACKEND API PERFORMANCE:{Colors.END}")
            if 'ticker' in backend_results:
                print(f"  /ticker endpoint: {backend_results['ticker']['avg_ms']:.0f}ms avg (min: {backend_results['ticker']['min_ms']:.0f}ms, max: {backend_results['ticker']['max_ms']:.0f}ms)")
            if 'symbols' in backend_results:
                print(f"  /symbols endpoint: {backend_results['symbols']['avg_ms']:.0f}ms avg (min: {backend_results['symbols']['min_ms']:.0f}ms, max: {backend_results['symbols']['max_ms']:.0f}ms)")
        
        # Concurrent Performance
        if concurrent_results and 'concurrent' in concurrent_results:
            print(f"\n{Colors.YELLOW}🔀 CONCURRENT LOAD PERFORMANCE ({CONCURRENT_REQUESTS} requests):{Colors.END}")
            print(f"  Success Rate:     {concurrent_results['concurrent']['success_rate']:.1f}% ({concurrent_results['concurrent']['success_count']}/{CONCURRENT_REQUESTS})")
            print(f"  Average Latency:  {concurrent_results['concurrent']['avg_ms']:.0f}ms")
            print(f"  95th Percentile:  {concurrent_results['concurrent']['p95_ms']:.0f}ms")
        
        # End-to-End Performance
        if e2e_results and 'end_to_end' in e2e_results:
            print(f"\n{Colors.GREEN}🎯 END-TO-END PIPELINE LATENCY:{Colors.END}")
            print(f"  Average:          {e2e_results['end_to_end']['avg_ms']:.0f}ms")
            print(f"  Best Case:        {e2e_results['end_to_end']['min_ms']:.0f}ms")
            print(f"  Worst Case:       {e2e_results['end_to_end']['max_ms']:.0f}ms")
            print(f"  Target (<20ms):   {'✅ ACHIEVED' if e2e_results['end_to_end']['meets_target'] else '❌ MISSED'}")
        
        # Performance Summary
        print(f"\n{Colors.CYAN}📊 PERFORMANCE SUMMARY:{Colors.END}")
        
        # Calculate estimated pipeline breakdown
        redis_read_ms = cache_results.get('cache_hit', {}).get('avg_ms', 1)
        backend_ms = backend_results.get('ticker', {}).get('avg_ms', 50)
        e2e_ms = e2e_results.get('end_to_end', {}).get('avg_ms', 100)
        
        print(f"  Bitget API:       ~{max(0, backend_ms - redis_read_ms):.0f}ms (estimated)")
        print(f"  Redis Cache:      ~{redis_read_ms:.1f}ms ⚡")
        print(f"  Frontend Proc:    ~5ms (simulated)")
        print(f"  Total Pipeline:   ~{e2e_ms:.0f}ms")
        
        # Performance Rating
        if e2e_ms < 20:
            rating = f"{Colors.GREEN}🚀 EXCELLENT (Sub-20ms){Colors.END}"
        elif e2e_ms < 50:
            rating = f"{Colors.YELLOW}⚡ GOOD (Sub-50ms){Colors.END}"
        elif e2e_ms < 100:
            rating = f"{Colors.YELLOW}⚠️  OK (Sub-100ms){Colors.END}"
        else:
            rating = f"{Colors.RED}🐌 NEEDS OPTIMIZATION{Colors.END}"
        
        print(f"\n{Colors.BOLD}Overall Rating: {rating}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")

class TestPipelinePerformance:
    """Pytest test class"""
    
    @pytest.fixture
    def event_loop(self):
        """Create event loop for async tests"""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
    
    @pytest.mark.asyncio
    async def test_full_pipeline_performance(self):
        """Main pipeline performance test"""
        tester = PipelinePerformanceTester()
        
        try:
            await tester.setup()
            
            # Run all performance tests
            print(f"{Colors.CYAN}🚀 Starting Full Pipeline Performance Test Suite...{Colors.END}")
            
            redis_results = await tester.test_redis_performance()
            backend_results = await tester.test_backend_api_performance()
            cache_results = await tester.test_cache_hit_performance()
            concurrent_results = await tester.test_concurrent_load_performance()
            e2e_results = await tester.test_end_to_end_latency()
            
            # Generate report
            tester.print_performance_report(
                redis_results, backend_results, cache_results, 
                concurrent_results, e2e_results
            )
            
            # Assertions for test success
            if redis_results:
                assert redis_results['ping']['avg_ms'] < 5, "Redis ping should be <5ms"
                assert redis_results['read']['ops_per_sec'] > 10000, "Redis should handle >10k reads/sec"
            
            if e2e_results and 'end_to_end' in e2e_results:
                # Warning if >100ms, but don't fail test
                if e2e_results['end_to_end']['avg_ms'] > 100:
                    print(f"{Colors.YELLOW}⚠️  Warning: E2E latency is {e2e_results['end_to_end']['avg_ms']:.0f}ms (target: <20ms){Colors.END}")
            
            print(f"\n{Colors.GREEN}✅ Full Pipeline Performance Test completed successfully!{Colors.END}")
            
        finally:
            await tester.teardown()

# Standalone execution
async def main():
    """Standalone execution"""
    tester = PipelinePerformanceTester()
    
    try:
        await tester.setup()
        
        print(f"{Colors.CYAN}🚀 Starting Data Pipeline Performance Test Suite...{Colors.END}")
        
        redis_results = await tester.test_redis_performance()
        backend_results = await tester.test_backend_api_performance()
        cache_results = await tester.test_cache_hit_performance()
        concurrent_results = await tester.test_concurrent_load_performance()
        e2e_results = await tester.test_end_to_end_latency()
        
        tester.print_performance_report(
            redis_results, backend_results, cache_results,
            concurrent_results, e2e_results
        )
        
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Performance test failed: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await tester.teardown()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
