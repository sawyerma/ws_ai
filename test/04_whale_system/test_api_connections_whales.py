"""
API Connection Tests for Whale Monitoring System
Tests external API connections for blockchain data and pricing
"""
import pytest
import asyncio
import aiohttp
import time
from whales.config_whales import Config

class TestAPIConnections:
    
    @pytest.fixture
    def event_loop(self):
        """Create event loop for async tests"""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
    
    @pytest.mark.asyncio
    async def test_ethereum_api_connection(self):
        """Test Ethereum API connection"""
        api_key = Config.get_api_key("ethereum")
        if not Config.has_valid_api_key("ethereum"):
            pytest.skip("Ethereum API key not configured - using fallback system")
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "module": "proxy",
                    "action": "eth_blockNumber",
                    "apikey": api_key
                }
                async with session.get("https://api.etherscan.io/api", params=params, timeout=10) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "result" in data
                    
                    # Handle API key errors gracefully
                    if "Invalid API Key" in data["result"]:
                        pytest.skip(f"Ethereum API key invalid - Expected for demo system")
                    
                    block_number = int(data["result"], 16)
                    assert block_number > 0
                    print(f"✅ Ethereum API connection successful - Latest block: {block_number}")
        except Exception as e:
            if "Invalid API Key" in str(e):
                pytest.skip("Ethereum API key invalid - Expected for demo system")
            pytest.fail(f"❌ Ethereum API connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bsc_api_connection(self):
        """Test BSC API connection"""
        api_key = Config.get_api_key("bsc")
        if not Config.has_valid_api_key("bsc"):
            pytest.skip("BSC API key not configured - using fallback system")
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "module": "proxy",
                    "action": "eth_blockNumber",
                    "apikey": api_key
                }
                async with session.get("https://api.bscscan.com/api", params=params, timeout=10) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "result" in data
                    
                    # Handle API key errors gracefully
                    if "Invalid API Key" in data["result"]:
                        pytest.skip(f"BSC API key invalid - Expected for demo system")
                    
                    block_number = int(data["result"], 16)
                    assert block_number > 0
                    print(f"✅ BSC API connection successful - Latest block: {block_number}")
        except Exception as e:
            if "Invalid API Key" in str(e):
                pytest.skip("BSC API key invalid - Expected for demo system")
            pytest.fail(f"❌ BSC API connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_polygon_api_connection(self):
        """Test Polygon API connection"""
        api_key = Config.get_api_key("polygon")
        if not Config.has_valid_api_key("polygon"):
            pytest.skip("Polygon API key not configured - using fallback system")
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "module": "proxy",
                    "action": "eth_blockNumber",
                    "apikey": api_key
                }
                async with session.get("https://api.polygonscan.com/api", params=params, timeout=10) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "result" in data
                    
                    # Handle API key errors gracefully
                    if "Invalid API Key" in data["result"]:
                        pytest.skip(f"Polygon API key invalid - Expected for demo system")
                    
                    block_number = int(data["result"], 16)
                    assert block_number > 0
                    print(f"✅ Polygon API connection successful - Latest block: {block_number}")
        except Exception as e:
            if "Invalid API Key" in str(e):
                pytest.skip("Polygon API key invalid - Expected for demo system")
            pytest.fail(f"❌ Polygon API connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_coingecko_api_connection(self):
        """Test CoinGecko API connection"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test basic connection
                async with session.get("https://api.coingecko.com/api/v3/ping", timeout=10) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "gecko_says" in data
                    print("✅ CoinGecko API basic connection successful")
                
                # Test price endpoint
                coin_ids = ",".join([
                    "bitcoin", "ethereum", "binancecoin", "tether", "solana"
                ])
                price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd"
                async with session.get(price_url, timeout=10) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "bitcoin" in data
                    assert "usd" in data["bitcoin"]
                    assert isinstance(data["bitcoin"]["usd"], (int, float))
                    print(f"✅ CoinGecko price API successful - BTC: ${data['bitcoin']['usd']}")
        except Exception as e:
            pytest.fail(f"❌ CoinGecko API connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_ethereum_transaction_data(self):
        """Test fetching Ethereum transaction data"""
        api_key = Config.get_api_key("ethereum")
        if not Config.has_valid_api_key("ethereum"):
            pytest.skip("Ethereum API key not configured - using fallback system")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get latest block first
                params = {
                    "module": "proxy",
                    "action": "eth_blockNumber",
                    "apikey": api_key
                }
                async with session.get("https://api.etherscan.io/api", params=params, timeout=10) as response:
                    data = await response.json()
                    
                    # Handle API key errors gracefully
                    if "Invalid API Key" in data.get("result", ""):
                        pytest.skip("Ethereum API key invalid - Expected for demo system")
                    
                    latest_block = int(data["result"], 16)
                
                # Get block data
                params = {
                    "module": "proxy",
                    "action": "eth_getBlockByNumber",
                    "tag": hex(latest_block),
                    "boolean": "true",
                    "apikey": api_key
                }
                async with session.get("https://api.etherscan.io/api", params=params, timeout=15) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "result" in data
                    block_data = data["result"]
                    assert "transactions" in block_data
                    assert isinstance(block_data["transactions"], list)
                    print(f"✅ Ethereum transaction data fetch successful - {len(block_data['transactions'])} transactions")
        except Exception as e:
            if "Invalid API Key" in str(e):
                pytest.skip("Ethereum API key invalid - Expected for demo system")
            pytest.fail(f"❌ Ethereum transaction data fetch failed: {e}")
    
    @pytest.mark.asyncio
    async def test_token_transfer_data(self):
        """Test fetching token transfer data"""
        api_key = Config.get_api_key("ethereum")
        if not Config.has_valid_api_key("ethereum"):
            pytest.skip("Ethereum API key not configured - using fallback system")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get latest block first
                params = {
                    "module": "proxy",
                    "action": "eth_blockNumber",
                    "apikey": api_key
                }
                async with session.get("https://api.etherscan.io/api", params=params, timeout=10) as response:
                    data = await response.json()
                    
                    # Handle API key errors gracefully
                    if "Invalid API Key" in data.get("result", ""):
                        pytest.skip("Ethereum API key invalid - Expected for demo system")
                    
                    latest_block = int(data["result"], 16)
                
                # Get token transfers for recent block
                start_block = latest_block - 10
                params = {
                    "module": "account",
                    "action": "tokentx",
                    "startblock": start_block,
                    "endblock": latest_block,
                    "sort": "asc",
                    "apikey": api_key
                }
                async with session.get("https://api.etherscan.io/api", params=params, timeout=20) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "result" in data
                    transfers = data["result"]
                    assert isinstance(transfers, list)
                    print(f"✅ Token transfer data fetch successful - {len(transfers)} transfers")
        except Exception as e:
            if "Invalid API Key" in str(e):
                pytest.skip("Ethereum API key invalid - Expected for demo system")
            pytest.fail(f"❌ Token transfer data fetch failed: {e}")
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self):
        """Test API rate limiting behavior"""
        api_key = Config.get_api_key("ethereum")
        if not Config.has_valid_api_key("ethereum"):
            pytest.skip("Ethereum API key not configured - using fallback system")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Make multiple rapid requests
                request_times = []
                for i in range(3):
                    start_time = time.time()
                    params = {
                        "module": "proxy",
                        "action": "eth_blockNumber",
                        "apikey": api_key
                    }
                    async with session.get("https://api.etherscan.io/api", params=params, timeout=10) as response:
                        request_times.append(time.time() - start_time)
                        assert response.status == 200
                    
                    # Small delay between requests
                    await asyncio.sleep(0.2)
                
                avg_time = sum(request_times) / len(request_times)
                print(f"✅ API rate limiting test successful - Avg response time: {avg_time:.3f}s")
                assert avg_time < 5.0  # Should be reasonable
        except Exception as e:
            if "Invalid API Key" in str(e):
                pytest.skip("Ethereum API key invalid - Expected for demo system")
            pytest.fail(f"❌ API rate limiting test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_coingecko_all_coins_pricing(self):
        """Test CoinGecko pricing for all configured coins"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get all coingecko IDs from config
                coin_ids = ",".join([
                    config["coingecko_id"] for config in Config.COIN_CONFIG.values()
                ])
                
                price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd"
                async with session.get(price_url, timeout=15) as response:
                    assert response.status == 200
                    data = await response.json()
                    
                    # Check all coins have prices
                    missing_prices = []
                    for symbol, config in Config.COIN_CONFIG.items():
                        coin_id = config["coingecko_id"]
                        if coin_id not in data or "usd" not in data[coin_id]:
                            missing_prices.append(f"{symbol} ({coin_id})")
                    
                    assert len(missing_prices) == 0, f"Missing prices for: {missing_prices}"
                    print(f"✅ All {len(Config.COIN_CONFIG)} coins have price data")
        except Exception as e:
            pytest.fail(f"❌ CoinGecko all coins pricing test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test API error handling"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test invalid API key
                params = {
                    "module": "proxy",
                    "action": "eth_blockNumber",
                    "apikey": "invalid_key"
                }
                async with session.get("https://api.etherscan.io/api", params=params, timeout=10) as response:
                    # Should get response but with error
                    data = await response.json()
                    assert "status" in data
                    # Either rate limited or invalid key error
                    assert data["status"] == "0" or "rate limit" in data.get("result", "").lower()
                    print("✅ API error handling test successful")
        except Exception as e:
            pytest.fail(f"❌ API error handling test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
