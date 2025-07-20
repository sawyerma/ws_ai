"""
API Connection Tests for Bitget System
Tests external API connections for market data and trading
"""
import pytest
import asyncio
import aiohttp
import time
import websockets
from market.bitget.config import bitget_config
from market.bitget.services.bitget_rest import BitgetRestAPI

class TestBitgetAPIConnections:
    
    @pytest.fixture
    def event_loop(self):
        """Create event loop for async tests"""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
    
    @pytest.mark.asyncio
    async def test_bitget_rest_api_connection(self):
        """Test Bitget REST API connection"""
        try:
            rest_api = BitgetRestAPI()
            
            # Test basic connection with public endpoint
            async with aiohttp.ClientSession() as session:
                url = f"{bitget_config.rest_base_url}/api/v2/spot/public/time"
                async with session.get(url, timeout=10) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "code" in data
                    assert data["code"] == "00000"  # Success code
                    assert "data" in data
                    print(f"✅ Bitget REST API connection successful - Server time: {data['data']}")
        except Exception as e:
            pytest.fail(f"❌ Bitget REST API connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_spot_symbols(self):
        """Test fetching Bitget spot symbols"""
        try:
            rest_api = BitgetRestAPI()
            
            async with aiohttp.ClientSession() as session:
                url = f"{bitget_config.rest_base_url}/api/v2/spot/public/symbols"
                async with session.get(url, timeout=15) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "code" in data
                    assert data["code"] == "00000"
                    assert "data" in data
                    assert isinstance(data["data"], list)
                    assert len(data["data"]) > 0
                    
                    # Check for common symbols
                    symbols = [s["symbol"] for s in data["data"]]
                    assert "BTCUSDT" in symbols
                    assert "ETHUSDT" in symbols
                    print(f"✅ Bitget spot symbols fetch successful - {len(symbols)} symbols")
        except Exception as e:
            pytest.fail(f"❌ Bitget spot symbols fetch failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_futures_symbols(self):
        """Test fetching Bitget futures symbols"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{bitget_config.rest_base_url}/api/v2/mix/market/contracts"
                params = {"productType": "USDT-FUTURES"}
                async with session.get(url, params=params, timeout=15) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "code" in data
                    assert data["code"] == "00000"
                    assert "data" in data
                    assert isinstance(data["data"], list)
                    assert len(data["data"]) > 0
                    
                    # Check for common futures symbols
                    symbols = [s["symbol"] for s in data["data"]]
                    assert "BTCUSDT" in symbols
                    assert "ETHUSDT" in symbols
                    print(f"✅ Bitget futures symbols fetch successful - {len(symbols)} symbols")
        except Exception as e:
            pytest.fail(f"❌ Bitget futures symbols fetch failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_spot_ticker(self):
        """Test fetching Bitget spot ticker data"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{bitget_config.rest_base_url}/api/v2/spot/market/tickers"
                async with session.get(url, timeout=15) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "code" in data
                    assert data["code"] == "00000"
                    assert "data" in data
                    assert isinstance(data["data"], list)
                    assert len(data["data"]) > 0
                    
                    # Find BTCUSDT ticker
                    btc_ticker = next((t for t in data["data"] if t["symbol"] == "BTCUSDT"), None)
                    assert btc_ticker is not None
                    assert "lastPr" in btc_ticker  # Last price
                    assert "baseVolume" in btc_ticker  # Volume
                    assert float(btc_ticker["lastPr"]) > 0
                    print(f"✅ Bitget spot ticker fetch successful - BTCUSDT: ${btc_ticker['lastPr']}")
        except Exception as e:
            pytest.fail(f"❌ Bitget spot ticker fetch failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_futures_ticker(self):
        """Test fetching Bitget futures ticker data"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{bitget_config.rest_base_url}/api/v2/mix/market/tickers"
                params = {"productType": "USDT-FUTURES"}
                async with session.get(url, params=params, timeout=15) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "code" in data
                    assert data["code"] == "00000"
                    assert "data" in data
                    assert isinstance(data["data"], list)
                    assert len(data["data"]) > 0
                    
                    # Find BTCUSDT ticker
                    btc_ticker = next((t for t in data["data"] if t["symbol"] == "BTCUSDT"), None)
                    assert btc_ticker is not None
                    assert "lastPr" in btc_ticker  # Last price
                    assert "baseVolume" in btc_ticker  # Volume
                    assert float(btc_ticker["lastPr"]) > 0
                    print(f"✅ Bitget futures ticker fetch successful - BTCUSDT: ${btc_ticker['lastPr']}")
        except Exception as e:
            pytest.fail(f"❌ Bitget futures ticker fetch failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_spot_orderbook(self):
        """Test fetching Bitget spot orderbook"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{bitget_config.rest_base_url}/api/v2/spot/market/orderbook"
                params = {"symbol": "BTCUSDT", "limit": "50"}
                async with session.get(url, params=params, timeout=10) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "code" in data
                    assert data["code"] == "00000"
                    assert "data" in data
                    assert "bids" in data["data"]
                    assert "asks" in data["data"]
                    assert isinstance(data["data"]["bids"], list)
                    assert isinstance(data["data"]["asks"], list)
                    assert len(data["data"]["bids"]) > 0
                    assert len(data["data"]["asks"]) > 0
                    print(f"✅ Bitget spot orderbook fetch successful - {len(data['data']['bids'])} bids, {len(data['data']['asks'])} asks")
        except Exception as e:
            pytest.fail(f"❌ Bitget spot orderbook fetch failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_spot_candles(self):
        """Test fetching Bitget spot candle data"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{bitget_config.rest_base_url}/api/v2/spot/market/candles"
                params = {"symbol": "BTCUSDT", "granularity": "1m", "limit": "100"}
                async with session.get(url, params=params, timeout=15) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "code" in data
                    assert data["code"] == "00000"
                    assert "data" in data
                    assert isinstance(data["data"], list)
                    assert len(data["data"]) > 0
                    
                    # Check candle structure
                    candle = data["data"][0]
                    assert isinstance(candle, list)
                    assert len(candle) >= 6  # timestamp, open, high, low, close, volume
                    print(f"✅ Bitget spot candles fetch successful - {len(data['data'])} candles")
        except Exception as e:
            pytest.fail(f"❌ Bitget spot candles fetch failed: {e}")
    
    @pytest.mark.asyncio 
    async def test_bitget_websocket_connection(self):
        """Test Bitget WebSocket connection"""
        try:
            ws_url = bitget_config.market_mappings["spot"]["ws_url"]
            
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
                # Send subscription message
                subscribe_msg = {
                    "op": "subscribe",
                    "args": [{
                        "instType": "SP",
                        "channel": "ticker",
                        "instId": "BTCUSDT_SPBL"
                    }]
                }
                await ws.send(str(subscribe_msg).replace("'", '"'))
                
                # Wait for response
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                data = eval(response)  # Simple eval for test
                
                # Should get subscription confirmation or data
                assert isinstance(data, dict)
                print(f"✅ Bitget WebSocket connection successful - Response: {data}")
                
        except Exception as e:
            pytest.fail(f"❌ Bitget WebSocket connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_api_rate_limiting(self):
        """Test Bitget API rate limiting behavior"""
        try:
            async with aiohttp.ClientSession() as session:
                # Make multiple rapid requests
                request_times = []
                for i in range(5):
                    start_time = time.time()
                    url = f"{bitget_config.rest_base_url}/api/v2/spot/public/time"
                    async with session.get(url, timeout=10) as response:
                        request_times.append(time.time() - start_time)
                        assert response.status == 200
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                
                avg_time = sum(request_times) / len(request_times)
                print(f"✅ Bitget API rate limiting test successful - Avg response time: {avg_time:.3f}s")
                assert avg_time < 5.0  # Should be reasonable
        except Exception as e:
            pytest.fail(f"❌ Bitget API rate limiting test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_error_handling(self):
        """Test Bitget API error handling"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test invalid symbol
                url = f"{bitget_config.rest_base_url}/api/v2/spot/market/orderbook"
                params = {"symbol": "INVALIDUSDT", "limit": "50"}
                async with session.get(url, params=params, timeout=10) as response:
                    data = await response.json()
                    # Should get error response
                    assert "code" in data
                    assert data["code"] != "00000"  # Not success
                    print(f"✅ Bitget error handling test successful - Error code: {data['code']}")
        except Exception as e:
            pytest.fail(f"❌ Bitget error handling test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bitget_all_market_types(self):
        """Test all configured market types"""
        try:
            for market_type, config in bitget_config.market_mappings.items():
                print(f"🔄 Testing {market_type} market...")
                
                # Test WebSocket URL accessibility
                ws_url = config["ws_url"]
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=5) as ws:
                    # Just test connection, no need to subscribe
                    await ws.ping()
                    print(f"✅ {market_type} WebSocket connection successful")
                
                await asyncio.sleep(0.5)  # Avoid too rapid connections
            
            print(f"✅ All {len(bitget_config.market_mappings)} market types tested successfully")
        except Exception as e:
            pytest.fail(f"❌ Bitget all market types test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
