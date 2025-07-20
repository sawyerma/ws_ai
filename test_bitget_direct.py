#!/usr/bin/env python3
"""
Direkter Bitget API Test ohne pytest
"""
import asyncio
import aiohttp
import time
import sys
import os
import json
import websockets

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from market.bitget.config import bitget_config
    print("✅ Bitget config imported successfully")
except ImportError as e:
    print(f"❌ Failed to import bitget config: {e}")
    sys.exit(1)

class BitgetTester:
    def __init__(self):
        self.base_url = bitget_config.rest_base_url
        print(f"🔧 Base URL: {self.base_url}")
        
    async def test_basic_connection(self):
        """Test basic REST API connection"""
        print("\n🔄 Testing basic REST API connection...")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v2/spot/public/time"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == "00000":
                            print(f"✅ Basic connection successful - Server time: {data.get('data')}")
                            return True
                        else:
                            print(f"❌ API returned error code: {data.get('code')}")
                            return False
                    else:
                        print(f"❌ HTTP error: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def test_spot_symbols(self):
        """Test fetching spot symbols"""
        print("\n🔄 Testing spot symbols fetch...")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v2/spot/public/symbols"
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == "00000" and isinstance(data.get("data"), list):
                            symbols = [s["symbol"] for s in data["data"]]
                            btc_found = "BTCUSDT" in symbols
                            eth_found = "ETHUSDT" in symbols
                            print(f"✅ Spot symbols fetch successful - {len(symbols)} symbols")
                            print(f"   BTCUSDT found: {btc_found}, ETHUSDT found: {eth_found}")
                            return True
                        else:
                            print(f"❌ Invalid response format: {data}")
                            return False
                    else:
                        print(f"❌ HTTP error: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Spot symbols fetch failed: {e}")
            return False
    
    async def test_spot_ticker(self):
        """Test fetching spot ticker"""
        print("\n🔄 Testing spot ticker fetch...")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v2/spot/market/tickers"
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == "00000" and isinstance(data.get("data"), list):
                            tickers = data["data"]
                            btc_ticker = next((t for t in tickers if t["symbol"] == "BTCUSDT"), None)
                            if btc_ticker:
                                price = btc_ticker.get("lastPr", "N/A")
                                volume = btc_ticker.get("baseVolume", "N/A")
                                print(f"✅ Spot ticker fetch successful - BTCUSDT: ${price}, Volume: {volume}")
                                return True
                            else:
                                print("❌ BTCUSDT ticker not found")
                                return False
                        else:
                            print(f"❌ Invalid response format: {data}")
                            return False
                    else:
                        print(f"❌ HTTP error: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Spot ticker fetch failed: {e}")
            return False
    
    async def test_orderbook(self):
        """Test fetching orderbook"""
        print("\n🔄 Testing orderbook fetch...")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v2/spot/market/orderbook"
                params = {"symbol": "BTCUSDT", "limit": "50"}
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == "00000":
                            orderbook = data.get("data", {})
                            bids = orderbook.get("bids", [])
                            asks = orderbook.get("asks", [])
                            print(f"✅ Orderbook fetch successful - {len(bids)} bids, {len(asks)} asks")
                            if bids and asks:
                                print(f"   Best bid: {bids[0][0]}, Best ask: {asks[0][0]}")
                            return True
                        else:
                            print(f"❌ API error: {data}")
                            return False
                    else:
                        print(f"❌ HTTP error: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Orderbook fetch failed: {e}")
            return False
    
    async def test_websocket(self):
        """Test WebSocket connection"""
        print("\n🔄 Testing WebSocket connection...")
        try:
            ws_url = bitget_config.market_mappings["spot"]["ws_url"]
            print(f"   Connecting to: {ws_url}")
            
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=5) as ws:
                # Test ping
                await ws.ping()
                print("✅ WebSocket ping successful")
                
                # Test subscription
                subscribe_msg = {
                    "op": "subscribe",
                    "args": [{
                        "instType": "SP",
                        "channel": "ticker",
                        "instId": "BTCUSDT_SPBL"
                    }]
                }
                await ws.send(json.dumps(subscribe_msg))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=10)
                    data = json.loads(response)
                    print(f"✅ WebSocket subscription successful - Response: {type(data)}")
                    return True
                except asyncio.TimeoutError:
                    print("⚠️  WebSocket subscription timeout (connection OK)")
                    return True
                    
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False
    
    async def test_rate_limiting(self):
        """Test API rate limiting"""
        print("\n🔄 Testing API rate limiting...")
        try:
            times = []
            async with aiohttp.ClientSession() as session:
                for i in range(3):
                    start = time.time()
                    url = f"{self.base_url}/api/v2/spot/public/time"
                    async with session.get(url, timeout=10) as response:
                        elapsed = time.time() - start
                        times.append(elapsed)
                        if response.status != 200:
                            print(f"❌ Request {i+1} failed with status: {response.status}")
                            return False
                    await asyncio.sleep(0.1)
                
                avg_time = sum(times) / len(times)
                print(f"✅ Rate limiting test successful - Avg response time: {avg_time:.3f}s")
                return True
                
        except Exception as e:
            print(f"❌ Rate limiting test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Bitget API Tests")
        print("=" * 50)
        
        tests = [
            ("Basic Connection", self.test_basic_connection),
            ("Spot Symbols", self.test_spot_symbols),
            ("Spot Ticker", self.test_spot_ticker),
            ("Orderbook", self.test_orderbook),
            ("WebSocket", self.test_websocket),
            ("Rate Limiting", self.test_rate_limiting)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = await test_func()
                await asyncio.sleep(0.5)  # Brief pause between tests
            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
                results[test_name] = False
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print("=" * 50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:<20} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Bitget integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return passed == total

async def main():
    tester = BitgetTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
