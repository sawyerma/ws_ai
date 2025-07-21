#!/usr/bin/env python3
"""
Einfacher Bitget API Test mit Standard-Python-Modulen
"""
import urllib.request
import urllib.parse
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from market.bitget.config import bitget_config
    print("✅ Bitget config imported successfully")
    print(f"🔧 Base URL: {bitget_config.rest_base_url}")
    print(f"🔧 Market mappings: {list(bitget_config.market_mappings.keys())}")
except ImportError as e:
    print(f"❌ Failed to import bitget config: {e}")
    print("Trying to load config manually...")
    
    # Fallback manual config
    class FallbackConfig:
        rest_base_url = "https://api.bitget.com"
        market_mappings = {
            "spot": {"ws_url": "wss://ws.bitget.com/spot/v1/stream"}
        }
    
    bitget_config = FallbackConfig()
    print(f"🔧 Using fallback config - Base URL: {bitget_config.rest_base_url}")

def test_basic_connection():
    """Test basic REST API connection"""
    print("\n🔄 Testing basic REST API connection...")
    try:
        url = f"{bitget_config.rest_base_url}/api/v2/spot/public/symbols"
        print(f"   Connecting to: {url}")
        
        # Add proper headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get("code") == "00000" and isinstance(data.get("data"), list) and len(data["data"]) > 0:
                    print(f"✅ Basic connection successful - API responding with {len(data['data'])} symbols")
                    return True
                else:
                    print(f"❌ API returned error code: {data.get('code')}")
                    print(f"   Full response: {data}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_spot_symbols():
    """Test fetching spot symbols"""
    print("\n🔄 Testing spot symbols fetch...")
    try:
        url = f"{bitget_config.rest_base_url}/api/v2/spot/public/symbols"
        print(f"   Connecting to: {url}")
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get("code") == "00000" and isinstance(data.get("data"), list):
                    symbols = [s["symbol"] for s in data["data"]]
                    btc_found = "BTCUSDT" in symbols
                    eth_found = "ETHUSDT" in symbols
                    print(f"✅ Spot symbols fetch successful - {len(symbols)} symbols")
                    print(f"   BTCUSDT found: {btc_found}, ETHUSDT found: {eth_found}")
                    if len(symbols) > 0:
                        print(f"   Sample symbols: {symbols[:5]}")
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

def test_spot_ticker():
    """Test fetching spot ticker"""
    print("\n🔄 Testing spot ticker fetch...")
    try:
        url = f"{bitget_config.rest_base_url}/api/v2/spot/market/tickers"
        print(f"   Connecting to: {url}")
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
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
                        print(f"   Available tickers sample: {[t['symbol'] for t in tickers[:5]]}")
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

def test_orderbook():
    """Test fetching orderbook"""
    print("\n🔄 Testing orderbook fetch...")
    try:
        url = f"{bitget_config.rest_base_url}/api/v2/spot/market/orderbook"
        params = urllib.parse.urlencode({"symbol": "BTCUSDT", "limit": "50"})
        full_url = f"{url}?{params}"
        print(f"   Connecting to: {full_url}")
        
        req = urllib.request.Request(full_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
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

def test_futures_symbols():
    """Test fetching futures symbols"""
    print("\n🔄 Testing futures symbols fetch...")
    try:
        url = f"{bitget_config.rest_base_url}/api/v2/mix/market/contracts"
        params = urllib.parse.urlencode({"productType": "USDT-FUTURES"})
        full_url = f"{url}?{params}"
        print(f"   Connecting to: {full_url}")
        
        req = urllib.request.Request(full_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get("code") == "00000" and isinstance(data.get("data"), list):
                    symbols = [s["symbol"] for s in data["data"]]
                    btc_found = "BTCUSDT" in symbols
                    eth_found = "ETHUSDT" in symbols
                    print(f"✅ Futures symbols fetch successful - {len(symbols)} symbols")
                    print(f"   BTCUSDT found: {btc_found}, ETHUSDT found: {eth_found}")
                    if len(symbols) > 0:
                        print(f"   Sample symbols: {symbols[:5]}")
                    return True
                else:
                    print(f"❌ Invalid response format: {data}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Futures symbols fetch failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Bitget API Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Spot Symbols", test_spot_symbols),
        ("Spot Ticker", test_spot_ticker),
        ("Orderbook", test_orderbook),
        ("Futures Symbols", test_futures_symbols)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
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
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
