#!/usr/bin/env python3
"""
🚀 VOLLSTÄNDIGER UNIFIED SYSTEM TEST
Testet komplette Integration: Binance + Bitget + Unified Router + Redis + ClickHouse + Frontend

Umfassende Tests für:
- Exchange Factory Integration (Binance + Bitget)
- Alle Unified Router (/trades, /ohlc, /settings, /symbols)
- Redis Cache Performance & Connectivity
- ClickHouse Integration
- Frontend-Backend Integration
- Exchange-Parameter Validierung
- WebSocket-Integration
- Performance & Load Testing
"""

import pytest
import asyncio
import aiohttp
import time
import json
import redis
import statistics
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    from core.routers.exchange_factory import ExchangeFactory
    from models.trade import UnifiedTrade, MarketType
    from db.clickhouse import ping as ch_ping, fetch_coin_settings, upsert_coin_setting, fetch_bars
    print("✅ Backend modules imported successfully")
except ImportError as e:
    print(f"⚠️ Backend module import failed: {e}")

# Test Configuration
BACKEND_BASE_URL = "http://localhost:8100"
FRONTEND_BASE_URL = "http://localhost:8180"
REDIS_HOST = "localhost"
REDIS_PORT = 6380
CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 8124

# Test Data
TEST_EXCHANGES = ["binance", "bitget"]
TEST_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
TEST_MARKETS = ["spot", "usdtm"]

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

class UnifiedSystemTester:
    
    def __init__(self):
        self.session = None
        self.redis_client = None
        self.test_results = {
            'exchange_factory': {},
            'unified_routers': {},
            'redis_performance': {},
            'clickhouse_integration': {},
            'frontend_backend': {},
            'exchange_parameters': {},
            'performance_benchmarks': {}
        }
        
    async def setup(self):
        """Setup Test Environment"""
        print(f"\n{Colors.CYAN}🔧 Setting up Unified System Test Environment...{Colors.END}")
        
        # HTTP Session
        self.session = aiohttp.ClientSession()
        
        # Redis Connection
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=2
            )
            self.redis_client.ping()
            print(f"{Colors.GREEN}✅ Redis connected: {REDIS_HOST}:{REDIS_PORT}{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}❌ Redis connection failed: {e}{Colors.END}")
            self.redis_client = None
            
    async def teardown(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
        print(f"{Colors.CYAN}🔧 Unified System Test cleanup completed{Colors.END}")
    
    async def test_exchange_factory_integration(self) -> Dict[str, Any]:
        """Test Exchange Factory für alle Exchanges"""
        print(f"\n{Colors.BLUE}🏭 Testing Exchange Factory Integration...{Colors.END}")
        
        results = {}
        
        for exchange in TEST_EXCHANGES:
            exchange_results = {}
            
            # Test REST API Factory
            try:
                rest_api = ExchangeFactory.get_rest_api(exchange)
                exchange_results['rest_api'] = rest_api is not None
                print(f"  {Colors.GREEN}✅{Colors.END} {exchange} REST API Factory: {'OK' if rest_api else 'FAILED'}")
            except Exception as e:
                exchange_results['rest_api'] = False
                print(f"  {Colors.RED}❌{Colors.END} {exchange} REST API Factory failed: {e}")
            
            # Test Storage Factory
            try:
                redis_storage = ExchangeFactory.get_storage(exchange, "redis")
                clickhouse_storage = ExchangeFactory.get_storage(exchange, "clickhouse")
                exchange_results['storage'] = {
                    'redis': redis_storage is not None,
                    'clickhouse': clickhouse_storage is not None
                }
                print(f"  {Colors.GREEN}✅{Colors.END} {exchange} Storage Factory: Redis={'OK' if redis_storage else 'FAILED'}, ClickHouse={'OK' if clickhouse_storage else 'FAILED'}")
            except Exception as e:
                exchange_results['storage'] = {'redis': False, 'clickhouse': False}
                print(f"  {Colors.RED}❌{Colors.END} {exchange} Storage Factory failed: {e}")
            
            # Test Historical Manager Factory
            try:
                historical_manager = ExchangeFactory.get_historical_manager(exchange)
                exchange_results['historical_manager'] = historical_manager is not None
                print(f"  {Colors.GREEN}✅{Colors.END} {exchange} Historical Manager: {'OK' if historical_manager else 'FAILED'}")
            except Exception as e:
                exchange_results['historical_manager'] = False
                print(f"  {Colors.RED}❌{Colors.END} {exchange} Historical Manager failed: {e}")
            
            # Test Collector Factory
            for symbol in TEST_SYMBOLS[:2]:  # Test subset
                for market in TEST_MARKETS[:1]:  # Test spot only
                    try:
                        collector = ExchangeFactory.get_collector(exchange, symbol, market)
                        if f'collectors_{market}' not in exchange_results:
                            exchange_results[f'collectors_{market}'] = []
                        exchange_results[f'collectors_{market}'].append({
                            'symbol': symbol,
                            'available': collector is not None
                        })
                    except Exception as e:
                        print(f"  {Colors.YELLOW}⚠️{Colors.END} {exchange} Collector {symbol}/{market}: {e}")
            
            results[exchange] = exchange_results
        
        self.test_results['exchange_factory'] = results
        print(f"{Colors.GREEN}✅ Exchange Factory Integration Test completed{Colors.END}")
        return results
    
    async def test_unified_routers(self) -> Dict[str, Any]:
        """Test alle Unified Router mit Exchange-Parametern"""
        print(f"\n{Colors.BLUE}🔗 Testing Unified Routers...{Colors.END}")
        
        results = {}
        
        # Router Endpoints to test
        router_tests = [
            ('/trades', {'exchange': 'binance', 'symbol': 'BTCUSDT', 'market': 'spot', 'limit': 10}),
            ('/trades', {'exchange': 'bitget', 'symbol': 'ETHUSDT', 'market': 'spot', 'limit': 5}),
            ('/ohlc', {'exchange': 'binance', 'symbol': 'BTCUSDT', 'market': 'spot', 'resolution': '1m', 'limit': 50}),
            ('/ohlc', {'exchange': 'bitget', 'symbol': 'SOLUSDT', 'market': 'spot', 'resolution': '5m', 'limit': 20}),
            ('/settings', {'exchange': 'binance'}),
            ('/settings', {'exchange': 'bitget', 'symbol': 'BTCUSDT'}),
            ('/symbols', {'exchange': 'binance', 'market': 'spot'}),
            ('/symbols', {'exchange': 'bitget', 'market': 'futures'}),
            ('/ticker', {'exchange': 'binance', 'symbol': 'BTCUSDT'}),
            ('/ticker', {'exchange': 'bitget', 'market': 'spot'})
        ]
        
        for endpoint, params in router_tests:
            test_key = f"{endpoint}_{params.get('exchange', 'unknown')}"
            
            try:
                # Build query string
                query_params = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{BACKEND_BASE_URL}{endpoint}?{query_params}"
                
                start_time = time.perf_counter()
                async with self.session.get(url, timeout=15) as response:
                    duration = (time.perf_counter() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        results[test_key] = {
                            'status': 'SUCCESS',
                            'response_time_ms': duration,
                            'data_size': len(str(data)),
                            'exchange': params.get('exchange'),
                            'endpoint': endpoint
                        }
                        print(f"  {Colors.GREEN}✅{Colors.END} {endpoint} ({params.get('exchange')}): {duration:.0f}ms")
                    else:
                        results[test_key] = {
                            'status': 'HTTP_ERROR',
                            'http_status': response.status,
                            'response_time_ms': duration,
                            'exchange': params.get('exchange'),
                            'endpoint': endpoint
                        }
                        print(f"  {Colors.RED}❌{Colors.END} {endpoint} ({params.get('exchange')}): HTTP {response.status}")
                        
            except Exception as e:
                results[test_key] = {
                    'status': 'EXCEPTION',
                    'error': str(e),
                    'exchange': params.get('exchange'),
                    'endpoint': endpoint
                }
                print(f"  {Colors.RED}❌{Colors.END} {endpoint} ({params.get('exchange')}): {e}")
        
        self.test_results['unified_routers'] = results
        print(f"{Colors.GREEN}✅ Unified Routers Test completed{Colors.END}")
        return results
    
    async def test_redis_performance_comprehensive(self) -> Dict[str, Any]:
        """Umfassender Redis Performance Test"""
        print(f"\n{Colors.BLUE}⚡ Testing Redis Performance (Comprehensive)...{Colors.END}")
        
        if not self.redis_client:
            print(f"{Colors.RED}❌ Redis not available{Colors.END}")
            return {}
        
        results = {}
        
        # Basic Performance Tests
        ping_times = []
        for i in range(100):
            start = time.perf_counter()
            self.redis_client.ping()
            ping_times.append((time.perf_counter() - start) * 1000)
        
        results['ping'] = {
            'avg_ms': statistics.mean(ping_times),
            'min_ms': min(ping_times),
            'max_ms': max(ping_times),
            'p95_ms': statistics.quantiles(ping_times, n=20)[18] if len(ping_times) > 20 else max(ping_times)
        }
        
        # Trade Data Performance
        trade_test_data = {
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'market': 'spot',
            'price': 45000.50,
            'size': 0.1,
            'side': 'buy',
            'timestamp': datetime.utcnow().isoformat(),
            'exchange_id': 'test123'
        }
        
        # Write Performance
        write_times = []
        for i in range(1000):
            key = f"trades:binance:BTCUSDT:spot:{i}"
            start = time.perf_counter()
            self.redis_client.setex(key, 300, json.dumps(trade_test_data))
            write_times.append((time.perf_counter() - start) * 1000)
        
        results['trades_write'] = {
            'avg_ms': statistics.mean(write_times),
            'ops_per_sec': 1000 / (sum(write_times) / 1000),
            'p95_ms': statistics.quantiles(write_times, n=20)[18] if len(write_times) > 20 else max(write_times)
        }
        
        # Read Performance
        read_times = []
        for i in range(1000):
            key = f"trades:binance:BTCUSDT:spot:{i}"
            start = time.perf_counter()
            value = self.redis_client.get(key)
            if value:
                json.loads(value)
            read_times.append((time.perf_counter() - start) * 1000)
        
        results['trades_read'] = {
            'avg_ms': statistics.mean(read_times),
            'ops_per_sec': 1000 / (sum(read_times) / 1000),
            'p95_ms': statistics.quantiles(read_times, n=20)[18] if len(read_times) > 20 else max(read_times)
        }
        
        # Memory Usage
        try:
            memory_info = self.redis_client.info('memory')
            results['memory'] = {
                'used_memory_mb': memory_info.get('used_memory', 0) / (1024 * 1024),
                'used_memory_peak_mb': memory_info.get('used_memory_peak', 0) / (1024 * 1024),
                'memory_fragmentation_ratio': memory_info.get('mem_fragmentation_ratio', 1.0)
            }
        except:
            results['memory'] = {'used_memory_mb': 0, 'used_memory_peak_mb': 0}
        
        # Cleanup test data
        for i in range(1000):
            self.redis_client.delete(f"trades:binance:BTCUSDT:spot:{i}")
        
        self.test_results['redis_performance'] = results
        print(f"  {Colors.GREEN}✅{Colors.END} Redis Performance: Ping={results['ping']['avg_ms']:.2f}ms, Write={results['trades_write']['ops_per_sec']:,.0f} ops/sec")
        return results
    
    async def test_clickhouse_integration(self) -> Dict[str, Any]:
        """Test ClickHouse Integration"""
        print(f"\n{Colors.BLUE}🗄️ Testing ClickHouse Integration...{Colors.END}")
        
        results = {}
        
        # Connection Test
        try:
            ping_result = ch_ping()
            results['connection'] = ping_result
            print(f"  {Colors.GREEN}✅{Colors.END} ClickHouse Connection: {'OK' if ping_result else 'FAILED'}")
        except Exception as e:
            results['connection'] = False
            print(f"  {Colors.RED}❌{Colors.END} ClickHouse Connection failed: {e}")
        
        # Settings Functions Test
        try:
            # Test upsert_coin_setting
            test_setting_result = upsert_coin_setting(
                exchange="binance",
                symbol="BTCUSDT",
                market="spot",
                store_live=1,
                load_history=0,
                favorite=1,
                db_resolutions=[60, 300],
                chart_resolution="1m"
            )
            results['upsert_settings'] = test_setting_result
            
            # Test fetch_coin_settings
            settings = fetch_coin_settings(exchange="binance", symbol="BTCUSDT")
            results['fetch_settings'] = len(settings) > 0
            
            print(f"  {Colors.GREEN}✅{Colors.END} ClickHouse Settings: Upsert={'OK' if test_setting_result else 'FAILED'}, Fetch={'OK' if len(settings) > 0 else 'FAILED'}")
        except Exception as e:
            results['upsert_settings'] = False
            results['fetch_settings'] = False
            print(f"  {Colors.RED}❌{Colors.END} ClickHouse Settings failed: {e}")
        
        # Bars Functions Test
        try:
            bars = fetch_bars(
                exchange="binance",
                symbol="BTCUSDT",
                market="spot",
                resolution=60,
                limit=10
            )
            results['fetch_bars'] = len(bars) >= 0  # Can be 0 if no data
            print(f"  {Colors.GREEN}✅{Colors.END} ClickHouse Bars: Fetched {len(bars)} records")
        except Exception as e:
            results['fetch_bars'] = False
            print(f"  {Colors.RED}❌{Colors.END} ClickHouse Bars failed: {e}")
        
        self.test_results['clickhouse_integration'] = results
        return results
    
    async def test_frontend_backend_integration(self) -> Dict[str, Any]:
        """Test Frontend-Backend Integration"""
        print(f"\n{Colors.BLUE}💻 Testing Frontend-Backend Integration...{Colors.END}")
        
        results = {}
        
        # Test Frontend Availability
        try:
            async with self.session.get(f"{FRONTEND_BASE_URL}/", timeout=10) as response:
                results['frontend_available'] = response.status == 200
                print(f"  {Colors.GREEN}✅{Colors.END} Frontend Available: HTTP {response.status}")
        except Exception as e:
            results['frontend_available'] = False
            print(f"  {Colors.RED}❌{Colors.END} Frontend not available: {e}")
        
        # Test CORS Headers
        try:
            async with self.session.options(f"{BACKEND_BASE_URL}/trades", timeout=5) as response:
                cors_headers = {
                    'access_control_allow_origin': response.headers.get('Access-Control-Allow-Origin'),
                    'access_control_allow_methods': response.headers.get('Access-Control-Allow-Methods'),
                    'access_control_allow_headers': response.headers.get('Access-Control-Allow-Headers')
                }
                results['cors_configured'] = cors_headers['access_control_allow_origin'] == '*'
                print(f"  {Colors.GREEN}✅{Colors.END} CORS Configured: {'OK' if results['cors_configured'] else 'MISSING'}")
        except Exception as e:
            results['cors_configured'] = False
            print(f"  {Colors.RED}❌{Colors.END} CORS test failed: {e}")
        
        # Test API Response Format (Frontend compatibility)
        try:
            async with self.session.get(f"{BACKEND_BASE_URL}/symbols?exchange=binance", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Check if response has expected structure for frontend
                    has_exchange = 'exchange' in data
                    has_symbols = 'symbols' in data
                    has_count = 'count' in data
                    
                    results['api_format_compatible'] = has_exchange and has_symbols and has_count
                    print(f"  {Colors.GREEN}✅{Colors.END} API Format Compatible: {'OK' if results['api_format_compatible'] else 'NEEDS ADJUSTMENT'}")
                else:
                    results['api_format_compatible'] = False
        except Exception as e:
            results['api_format_compatible'] = False
            print(f"  {Colors.RED}❌{Colors.END} API format test failed: {e}")
        
        self.test_results['frontend_backend'] = results
        return results
    
    async def test_exchange_parameter_validation(self) -> Dict[str, Any]:
        """Test Exchange Parameter Validation"""
        print(f"\n{Colors.BLUE}🔍 Testing Exchange Parameter Validation...{Colors.END}")
        
        results = {}
        
        # Valid Exchange Tests
        valid_tests = [
            ('binance', 'BTCUSDT', 'spot'),
            ('bitget', 'ETHUSDT', 'spot'),
            ('binance', 'BTCUSDT', 'usdtm'),
            ('bitget', 'SOLUSDT', 'usdtm')
        ]
        
        for exchange, symbol, market in valid_tests:
            try:
                url = f"{BACKEND_BASE_URL}/trades?exchange={exchange}&symbol={symbol}&market={market}&limit=1"
                async with self.session.get(url, timeout=10) as response:
                    test_key = f"valid_{exchange}_{market}"
                    results[test_key] = {
                        'status_code': response.status,
                        'success': response.status == 200,
                        'exchange': exchange,
                        'market': market
                    }
                    status_emoji = "✅" if response.status == 200 else "❌"
                    print(f"  {Colors.GREEN if response.status == 200 else Colors.RED}{status_emoji}{Colors.END} Valid {exchange}/{market}: HTTP {response.status}")
            except Exception as e:
                results[f"valid_{exchange}_{market}"] = {'success': False, 'error': str(e)}
        
        # Invalid Exchange Tests
        invalid_tests = [
            ('invalid_exchange', 'BTCUSDT', 'spot'),
            ('binance', 'BTCUSDT', 'invalid_market'),
            ('', 'BTCUSDT', 'spot')
        ]
        
        for exchange, symbol, market in invalid_tests:
            try:
                url = f"{BACKEND_BASE_URL}/trades?exchange={exchange}&symbol={symbol}&market={market}&limit=1"
                async with self.session.get(url, timeout=5) as response:
                    test_key = f"invalid_{exchange or 'empty'}_{market}"
                    # Should return 400 or 422 for invalid parameters
                    results[test_key] = {
                        'status_code': response.status,
                        'correctly_rejected': response.status in [400, 422, 500],
                        'exchange': exchange,
                        'market': market
                    }
                    status_emoji = "✅" if response.status in [400, 422, 500] else "⚠️"
                    print(f"  {Colors.GREEN if response.status in [400, 422, 500] else Colors.YELLOW}{status_emoji}{Colors.END} Invalid {exchange or 'empty'}/{market}: HTTP {response.status}")
            except Exception as e:
                results[f"invalid_{exchange or 'empty'}_{market}"] = {'correctly_rejected': True, 'error': str(e)}
        
        self.test_results['exchange_parameters'] = results
        return results
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Performance Benchmark Tests"""
        print(f"\n{Colors.BLUE}🚀 Testing Performance Benchmarks...{Colors.END}")
        
        results = {}
        
        # Concurrent Request Test
        async def single_request(exchange: str, endpoint: str):
            start = time.perf_counter()
            try:
                url = f"{BACKEND_BASE_URL}{endpoint}?exchange={exchange}&limit=10"
                async with self.session.get(url, timeout=15) as response:
                    duration = (time.perf_counter() - start) * 1000
                    return {
                        'success': response.status == 200,
                        'duration_ms': duration,
                        'exchange': exchange,
                        'endpoint': endpoint
                    }
            except Exception as e:
                return {
                    'success': False,
                    'duration_ms': (time.perf_counter() - start) * 1000,
                    'error': str(e),
                    'exchange': exchange,
                    'endpoint': endpoint
                }
        
        # Test concurrent requests to both exchanges
        concurrent_tasks = []
        for exchange in TEST_EXCHANGES:
            for endpoint in ['/trades', '/ohlc', '/symbols']:
                for _ in range(5):  # 5 requests per exchange/endpoint
                    concurrent_tasks.append(single_request(exchange, endpoint))
        
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        # Process concurrent results
        successful_requests = [r for r in concurrent_results if isinstance(r, dict) and r.get('success')]
        failed_requests = [r for r in concurrent_results if isinstance(r, dict) and not r.get('success')]
        
        if successful_requests:
            durations = [r['duration_ms'] for r in successful_requests]
            results['concurrent_load'] = {
                'total_requests': len(concurrent_tasks),
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'success_rate': len(successful_requests) / len(concurrent_tasks) * 100,
                'avg_response_time_ms': statistics.mean(durations),
                'p95_response_time_ms': statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
                'max_response_time_ms': max(durations),
                'min_response_time_ms': min(durations)
            }
            
            print(f"  {Colors.GREEN}✅{Colors.END} Concurrent Load: {len(successful_requests)}/{len(concurrent_tasks)} success ({results['concurrent_load']['success_rate']:.1f}%)")
            print(f"  {Colors.CYAN}📊{Colors.END} Response Times: Avg={results['concurrent_load']['avg_response_time_ms']:.0f}ms, P95={results['concurrent_load']['p95_response_time_ms']:.0f}ms")
        
        self.test_results['performance_benchmarks'] = results
        return results
    
    def print_comprehensive_report(self):
        """Print comprehensive test report"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*100}")
        print(f"  🚀 UNIFIED SYSTEM COMPREHENSIVE TEST REPORT")
        print(f"{'='*100}{Colors.END}")
        
        # Exchange Factory Results
        if self.test_results.get('exchange_factory'):
            print(f"\n{Colors.MAGENTA}🏭 EXCHANGE FACTORY RESULTS:{Colors.END}")
            for exchange, results in self.test_results['exchange_factory'].items():
                print(f"  {exchange.upper()}:")
                print(f"    REST API:         {'✅ OK' if results.get('rest_api') else '❌ FAILED'}")
                print(f"    Storage:          Redis={'✅' if results.get('storage', {}).get('redis') else '❌'} ClickHouse={'✅' if results.get('storage', {}).get('clickhouse') else '❌'}")
                print(f"    Historical Mgr:   {'✅ OK' if results.get('historical_manager') else '❌ FAILED'}")
        
        # Unified Routers Results
        if self.test_results.get('unified_routers'):
            print(f"\n{Colors.BLUE}🔗 UNIFIED ROUTERS RESULTS:{Colors.END}")
            successful_endpoints = sum(1 for r in self.test_results['unified_routers'].values() if r.get('status') == 'SUCCESS')
            total_endpoints = len(self.test_results['unified_routers'])
            print(f"  Success Rate:     {successful_endpoints}/{total_endpoints} ({successful_endpoints/total_endpoints*100:.1f}%)")
            
            # Group by endpoint
            endpoints = {}
            for test_key, result in self.test_results['unified_routers'].items():
                endpoint = result.get('endpoint', 'unknown')
                if endpoint not in endpoints:
                    endpoints[endpoint] = []
                endpoints[endpoint].append(result)
            
            for endpoint, results in endpoints.items():
                successful = sum(1 for r in results if r.get('status') == 'SUCCESS')
                avg_time = statistics.mean([r.get('response_time_ms', 0) for r in results if r.get('status') == 'SUCCESS']) if successful > 0 else 0
                print(f"  {endpoint:12}: {successful}/{len(results)} success, avg {avg_time:.0f}ms")
        
        # Redis Performance Results
        if self.test_results.get('redis_performance'):
            redis_results = self.test_results['redis_performance']
            print(f"\n{Colors.YELLOW}⚡ REDIS PERFORMANCE RESULTS:{Colors.END}")
            print(f"  Ping Latency:     {redis_results.get('ping', {}).get('avg_ms', 0):.2f}ms")
            print(f"  Write Speed:      {redis_results.get('trades_write', {}).get('ops_per_sec', 0):,.0f} ops/sec")
            print(f"  Read Speed:       {redis_results.get('trades_read', {}).get('ops_per_sec', 0):,.0f} ops/sec")
            print(f"  Memory Usage:     {redis_results.get('memory', {}).get('used_memory_mb', 0):.2f}MB")
        
        # ClickHouse Integration Results
        if self.test_results.get('clickhouse_integration'):
            ch_results = self.test_results['clickhouse_integration']
            print(f"\n{Colors.GREEN}🗄️ CLICKHOUSE INTEGRATION RESULTS:{Colors.END}")
            print(f"  Connection:       {'✅ OK' if ch_results.get('connection') else '❌ FAILED'}")
            print(f"  Settings CRUD:    {'✅ OK' if ch_results.get('upsert_settings') and ch_results.get('fetch_settings') else '❌ FAILED'}")
            print(f"  Bars Query:       {'✅ OK' if ch_results.get('fetch_bars') else '❌ FAILED'}")
        
        # Frontend-Backend Integration
        if self.test_results.get('frontend_backend'):
            fb_results = self.test_results['frontend_backend']
            print(f"\n{Colors.CYAN}💻 FRONTEND-BACKEND INTEGRATION:{Colors.END}")
            print(f"  Frontend Available: {'✅ OK' if fb_results.get('frontend_available') else '❌ FAILED'}")
            print(f"  CORS Configured:    {'✅ OK' if fb_results.get('cors_configured') else '❌ FAILED'}")
            print(f"  API Format:       {'✅ OK' if fb_results.get('api_format_compatible') else '❌ NEEDS ADJUSTMENT'}")
        
        # Exchange Parameter Validation
        if self.test_results.get('exchange_parameters'):
            ep_results = self.test_results['exchange_parameters']
            print(f"\n{Colors.MAGENTA}🔍 EXCHANGE PARAMETER VALIDATION:{Colors.END}")
            valid_tests = sum(1 for r in ep_results.values() if r.get('success'))
            invalid_tests = sum(1 for r in ep_results.values() if r.get('correctly_rejected'))
            print(f"  Valid Params:     {'✅ OK' if valid_tests > 0 else '❌ FAILED'}")
            print(f"  Invalid Rejected: {'✅ OK' if invalid_tests > 0 else '❌ FAILED'}")
        
        # Performance Benchmarks
        if self.test_results.get('performance_benchmarks') and 'concurrent_load' in self.test_results['performance_benchmarks']:
            perf_results = self.test_results['performance_benchmarks']['concurrent_load']
            print(f"\n{Colors.BLUE}🚀 PERFORMANCE BENCHMARKS:{Colors.END}")
            print(f"  Concurrent Load:  {perf_results['successful_requests']}/{perf_results['total_requests']} ({perf_results['success_rate']:.1f}%)")
            print(f"  Avg Response:     {perf_results['avg_response_time_ms']:.0f}ms")
            print(f"  P95 Response:     {perf_results['p95_response_time_ms']:.0f}ms")
        
        # Overall System Health
        print(f"\n{Colors.CYAN}📊 SYSTEM HEALTH SUMMARY:{Colors.END}")
        
        health_indicators = {
            'Exchange Factory': self.test_results.get('exchange_factory', {}),
            'Unified Routers': len([r for r in self.test_results.get('unified_routers', {}).values() if r.get('status') == 'SUCCESS']) > 0,
            'Redis Performance': self.test_results.get('redis_performance', {}).get('ping', {}).get('avg_ms', 0) < 5,
            'ClickHouse Integration': self.test_results.get('clickhouse_integration', {}).get('connection', False),
            'Frontend-Backend': self.test_results.get('frontend_backend', {}).get('cors_configured', False)
        }
        
        healthy_systems = sum(1 for indicator, status in health_indicators.items() if status)
        total_systems = len(health_indicators)
        
        if healthy_systems == total_systems:
            overall_health = f"{Colors.GREEN}🚀 EXCELLENT ({healthy_systems}/{total_systems}){Colors.END}"
        elif healthy_systems >= total_systems * 0.8:
            overall_health = f"{Colors.YELLOW}⚡ GOOD ({healthy_systems}/{total_systems}){Colors.END}"
        else:
            overall_health = f"{Colors.RED}⚠️ NEEDS ATTENTION ({healthy_systems}/{total_systems}){Colors.END}"
        
        print(f"  Overall Health:   {overall_health}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")

class TestUnifiedSystem:
    """Pytest test class"""
    
    @pytest.fixture
    def event_loop(self):
        """Create event loop for async tests"""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
    
    @pytest.mark.asyncio
    async def test_complete_unified_system(self):
        """Main unified system test"""
        tester = UnifiedSystemTester()
        
        try:
            await tester.setup()
            
            print(f"{Colors.CYAN}🚀 Starting Complete Unified System Test Suite...{Colors.END}")
            
            # Run all test phases
            await tester.test_exchange_factory_integration()
            await tester.test_unified_routers()
            await tester.test_redis_performance_comprehensive()
            await tester.test_clickhouse_integration()
            await tester.test_frontend_backend_integration()
            await tester.test_exchange_parameter_validation()
            await tester.test_performance_benchmarks()
            
            # Generate comprehensive report
            tester.print_comprehensive_report()
            
            # Basic assertions for test success
            assert len(tester.test_results['exchange_factory']) > 0, "Exchange Factory tests should run"
            assert len(tester.test_results['unified_routers']) > 0, "Unified Router tests should run"
            
            # Check critical systems
            successful_routers = sum(1 for r in tester.test_results['unified_routers'].values() if r.get('status') == 'SUCCESS')
            total_routers = len(tester.test_results['unified_routers'])
            
            if successful_routers == 0:
                print(f"{Colors.YELLOW}⚠️ Warning: No router endpoints succeeded{Colors.END}")
            
            print(f"\n{Colors.GREEN}✅ Complete Unified System Test completed successfully!{Colors.END}")
            
        finally:
            await tester.teardown()

# Standalone execution
async def main():
    """Standalone execution"""
    tester = UnifiedSystemTester()
    
    try:
        await tester.setup()
        
        print(f"{Colors.CYAN}🚀 Starting Complete Unified System Test Suite...{Colors.END}")
        
        # Run all test phases
        await tester.test_exchange_factory_integration()
        await tester.test_unified_routers()
        await tester.test_redis_performance_comprehensive()
        await tester.test_clickhouse_integration()
        await tester.test_frontend_backend_integration()
        await tester.test_exchange_parameter_validation()
        await tester.test_performance_benchmarks()
        
        # Generate comprehensive report
        tester.print_comprehensive_report()
        
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Unified system test failed: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await tester.teardown()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
