"""
Integration Tests for Whale Monitoring System
Tests end-to-end whale detection and system integration
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from whales.main_whales import start_whale_system, stop_whale_system
from whales.collector_manager_whales import collector_manager
from whales.services.price_service_whales import price_service
from whales.collectors.blockchain_collector_whales import EthereumCollector
from whales.collectors.token_collector_whales import EthereumTokenCollector
from db.clickhouse_whales import insert_whale_event, get_whale_events
from whales.config_whales import Config

class TestIntegrationWhales:
    
    @pytest.fixture
    def mock_blockchain_response(self):
        """Mock blockchain API response"""
        return {
            "result": {
                "transactions": [
                    {
                        "hash": f"0x{uuid.uuid4().hex}",
                        "from": "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE",  # Binance
                        "to": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43",    # Coinbase
                        "value": hex(int(1000 * 10**18)),  # 1000 ETH
                        "input": "0x"
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_token_response(self):
        """Mock token transfer API response"""
        return {
            "result": [
                {
                    "hash": f"0x{uuid.uuid4().hex}",
                    "from": "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE",
                    "to": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43",
                    "contractAddress": "0xA0b86a33E6441c8C6CBE4A6B2c6Ca16014ABCd7A",
                    "tokenSymbol": "USDT",
                    "tokenDecimal": "6",
                    "value": str(50_000_000 * 10**6),  # 50M USDT
                    "timeStamp": str(int(datetime.now().timestamp()))
                }
            ]
        }
    
    @pytest.fixture
    def mock_price_response(self):
        """Mock CoinGecko price response"""
        return {
            "ethereum": {"usd": 2500.0},
            "tether": {"usd": 1.0},
            "bitcoin": {"usd": 45000.0}
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_whale_detection(self, mock_blockchain_response, mock_price_response):
        """Test complete end-to-end whale detection process"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Mock API responses
            with patch('aiohttp.ClientSession.get') as mock_get:
                # Mock blockchain API
                mock_blockchain_context = AsyncMock()
                mock_blockchain_context.__aenter__.return_value.status = 200
                mock_blockchain_context.__aenter__.return_value.json = AsyncMock(return_value=mock_blockchain_response)
                
                # Mock price API
                mock_price_context = AsyncMock()
                mock_price_context.__aenter__.return_value.status = 200
                mock_price_context.__aenter__.return_value.json = AsyncMock(return_value=mock_price_response)
                
                # Configure mock to return different responses based on URL
                def mock_get_side_effect(url, **kwargs):
                    if "coingecko" in url:
                        return mock_price_context
                    else:
                        return mock_blockchain_context
                
                mock_get.side_effect = mock_get_side_effect
                
                # Initialize collector
                collector = EthereumCollector()
                
                # Mock get_latest_block
                with patch.object(collector, 'get_latest_block', return_value=1000):
                    # Mock is_duplicate to return False
                    with patch('whales.collectors.blockchain_collector_whales.is_duplicate', return_value=False):
                        # Mock insert_whale_event to return True
                        with patch('whales.collectors.blockchain_collector_whales.insert_whale_event', return_value=True):
                            # Process the block
                            await collector.process_block(1000)
                
            print("✅ End-to-end whale detection successful")
        except Exception as e:
            pytest.fail(f"❌ End-to-end whale detection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_token_whale_detection(self, mock_token_response, mock_price_response):
        """Test token whale detection process"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Mock API responses
            with patch('aiohttp.ClientSession.get') as mock_get:
                # Mock token API
                mock_token_context = AsyncMock()
                mock_token_context.__aenter__.return_value.status = 200
                mock_token_context.__aenter__.return_value.json = AsyncMock(return_value=mock_token_response)
                
                # Mock price API
                mock_price_context = AsyncMock()
                mock_price_context.__aenter__.return_value.status = 200
                mock_price_context.__aenter__.return_value.json = AsyncMock(return_value=mock_price_response)
                
                # Configure mock responses
                def mock_get_side_effect(url, **kwargs):
                    if "coingecko" in url:
                        return mock_price_context
                    else:
                        return mock_token_context
                
                mock_get.side_effect = mock_get_side_effect
                
                # Initialize token collector
                collector = EthereumTokenCollector()
                
                # Mock get_latest_block
                with patch.object(collector, 'get_latest_block', return_value=1000):
                    # Mock is_duplicate to return False
                    with patch('whales.collectors.token_collector_whales.is_duplicate', return_value=False):
                        # Mock insert_whale_event to return True
                        with patch('whales.collectors.token_collector_whales.insert_whale_event', return_value=True):
                            # Process the token block
                            await collector.process_token_block(1000)
                
            print("✅ Token whale detection successful")
        except Exception as e:
            pytest.fail(f"❌ Token whale detection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_cross_border_detection(self, mock_blockchain_response, mock_price_response):
        """Test cross-border whale detection"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Modify mock to have cross-border transaction
            cross_border_response = mock_blockchain_response.copy()
            cross_border_response["result"]["transactions"][0]["from"] = "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE"  # Binance (Malta)
            cross_border_response["result"]["transactions"][0]["to"] = "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43"    # Coinbase (USA)
            
            # Mock API responses
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(return_value=cross_border_response)
                mock_get.return_value = mock_context
                
                # Initialize collector
                collector = EthereumCollector()
                
                # Test cross-border detection
                from_location = collector.get_location("0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE")
                to_location = collector.get_location("0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43")
                
                assert from_location["country"] == "Malta"
                assert to_location["country"] == "USA"
                
                # Should detect cross-border
                is_cross_border = from_location["country"] != to_location["country"]
                assert is_cross_border == True
                
            print("✅ Cross-border whale detection successful")
        except Exception as e:
            pytest.fail(f"❌ Cross-border whale detection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_price_service_integration(self, mock_price_response):
        """Test price service integration with collectors"""
        try:
            # Mock CoinGecko API
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(return_value=mock_price_response)
                mock_get.return_value = mock_context
                
                # Update prices
                test_price_service = price_service
                await test_price_service.update_prices()
                
                # Verify prices were updated
                assert test_price_service.get_price("ethereum") == 2500.0
                assert test_price_service.get_price("tether") == 1.0
                assert test_price_service.get_price("bitcoin") == 45000.0
                
            print("✅ Price service integration successful")
        except Exception as e:
            pytest.fail(f"❌ Price service integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_manager_integration(self):
        """Test collector manager integration"""
        try:
            # Mock collectors
            mock_ethereum_collector = Mock()
            mock_ethereum_collector.start = AsyncMock()
            mock_ethereum_collector.stop = AsyncMock()
            
            mock_token_collector = Mock()
            mock_token_collector.start = AsyncMock()
            mock_token_collector.stop = AsyncMock()
            
            # Mock collector classes
            with patch.object(collector_manager.collector_classes, "ethereum", return_value=mock_ethereum_collector):
                with patch.object(collector_manager.collector_classes, "ethereum_tokens", return_value=mock_token_collector):
                    
                    # Start collectors
                    await collector_manager.start_collector("ethereum")
                    await collector_manager.start_collector("ethereum_tokens")
                    
                    # Verify collectors were started
                    assert len(collector_manager.collectors) == 2
                    mock_ethereum_collector.start.assert_called_once()
                    mock_token_collector.start.assert_called_once()
                    
                    # Stop all collectors
                    await collector_manager.stop_all()
                    
                    # Verify collectors were stopped
                    assert len(collector_manager.collectors) == 0
                    mock_ethereum_collector.stop.assert_called_once()
                    mock_token_collector.stop.assert_called_once()
                    
            print("✅ Collector manager integration successful")
        except Exception as e:
            pytest.fail(f"❌ Collector manager integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_system_startup_shutdown(self):
        """Test whale system startup and shutdown"""
        try:
            # Mock all external dependencies
            with patch('whales.services.price_service_whales.price_service.start') as mock_price_start:
                with patch('whales.collector_manager_whales.collector_manager.init_from_config') as mock_collector_init:
                    with patch('whales.collector_manager_whales.collector_manager.stop_all') as mock_collector_stop:
                        
                        # Test startup
                        await start_whale_system()
                        
                        # Verify services were started
                        mock_price_start.assert_called_once()
                        mock_collector_init.assert_called_once()
                        
                        # Test shutdown
                        await stop_whale_system()
                        
                        # Verify services were stopped
                        mock_collector_stop.assert_called_once()
                        
            print("✅ Whale system startup/shutdown successful")
        except Exception as e:
            pytest.fail(f"❌ Whale system startup/shutdown failed: {e}")
    
    @pytest.mark.asyncio
    async def test_database_integration(self):
        """Test database integration with whale events"""
        try:
            # Create test whale event
            test_event = {
                "ts": datetime.now(),
                "chain": "ethereum",
                "tx_hash": f"0x{uuid.uuid4().hex}",
                "from_addr": "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE",
                "to_addr": "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43",
                "token": "",
                "symbol": "ETH",
                "amount": 1000.0,
                "is_native": 1,
                "exchange": "Binance",
                "amount_usd": 2500000.0,
                "from_exchange": "Binance",
                "from_country": "Malta",
                "from_city": "Valletta",
                "to_exchange": "Coinbase",
                "to_country": "USA",
                "to_city": "San Francisco",
                "is_cross_border": 1,
                "source": "integration_test",
                "threshold_usd": 1000000.0,
                "coin_rank": 1
            }
            
            # Insert event
            result = await insert_whale_event(test_event)
            assert result == True
            
            # Retrieve event
            events = await get_whale_events(
                filters={"tx_hash": test_event["tx_hash"]},
                limit=1
            )
            
            assert len(events) == 1
            retrieved_event = events[0]
            assert retrieved_event["tx_hash"] == test_event["tx_hash"]
            assert retrieved_event["is_cross_border"] == 1
            
            print("✅ Database integration successful")
        except Exception as e:
            pytest.fail(f"❌ Database integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_multi_chain_integration(self):
        """Test multi-chain whale detection"""
        try:
            # Test different chains
            chains = ["ethereum", "binance", "polygon"]
            
            for chain in chains:
                # Create chain-specific test event
                test_event = {
                    "ts": datetime.now(),
                    "chain": chain,
                    "tx_hash": f"0x{uuid.uuid4().hex}",
                    "from_addr": "0x" + "1" * 40,
                    "to_addr": "0x" + "2" * 40,
                    "token": "",
                    "symbol": "ETH" if chain == "ethereum" else "BNB" if chain == "binance" else "MATIC",
                    "amount": 1000.0,
                    "is_native": 1,
                    "exchange": "",
                    "amount_usd": 2500000.0,
                    "from_exchange": "",
                    "from_country": "Unknown",
                    "from_city": "Unknown",
                    "to_exchange": "",
                    "to_country": "Unknown",
                    "to_city": "Unknown",
                    "is_cross_border": 0,
                    "source": f"integration_test_{chain}",
                    "threshold_usd": 1000000.0,
                    "coin_rank": 1
                }
                
                # Insert event
                result = await insert_whale_event(test_event)
                assert result == True
            
            # Retrieve events by chain
            for chain in chains:
                events = await get_whale_events(
                    filters={"chain": chain},
                    limit=10
                )
                assert isinstance(events, list)
                
                # Check if we have events for this chain
                chain_events = [e for e in events if e["chain"] == chain]
                print(f"✅ {chain.capitalize()} chain events: {len(chain_events)}")
            
            print("✅ Multi-chain integration successful")
        except Exception as e:
            pytest.fail(f"❌ Multi-chain integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_threshold_detection(self):
        """Test whale threshold detection for different coins"""
        try:
            # Test different coins with their thresholds
            test_coins = [
                {"symbol": "BTC", "amount": 100.0, "price": 45000.0, "threshold": 100_000_000},
                {"symbol": "ETH", "amount": 10000.0, "price": 2500.0, "threshold": 25_000_000},
                {"symbol": "USDT", "amount": 150_000_000.0, "price": 1.0, "threshold": 100_000_000}
            ]
            
            for coin in test_coins:
                usd_value = coin["amount"] * coin["price"]
                
                # Create test event
                test_event = {
                    "ts": datetime.now(),
                    "chain": "ethereum",
                    "tx_hash": f"0x{uuid.uuid4().hex}",
                    "from_addr": "0x" + "1" * 40,
                    "to_addr": "0x" + "2" * 40,
                    "token": "",
                    "symbol": coin["symbol"],
                    "amount": coin["amount"],
                    "is_native": 1,
                    "exchange": "",
                    "amount_usd": usd_value,
                    "from_exchange": "",
                    "from_country": "Unknown",
                    "from_city": "Unknown",
                    "to_exchange": "",
                    "to_country": "Unknown",
                    "to_city": "Unknown",
                    "is_cross_border": 0,
                    "source": f"threshold_test_{coin['symbol']}",
                    "threshold_usd": coin["threshold"],
                    "coin_rank": 1
                }
                
                # Only insert if above threshold
                if usd_value >= coin["threshold"]:
                    result = await insert_whale_event(test_event)
                    assert result == True
                    print(f"✅ {coin['symbol']} whale detected: ${usd_value:,.0f} (threshold: ${coin['threshold']:,.0f})")
                else:
                    print(f"❌ {coin['symbol']} below threshold: ${usd_value:,.0f} < ${coin['threshold']:,.0f}")
            
            print("✅ Whale threshold detection successful")
        except Exception as e:
            pytest.fail(f"❌ Whale threshold detection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_whale_detection(self):
        """Test concurrent whale detection from multiple sources"""
        try:
            # Create multiple test events concurrently
            test_events = []
            for i in range(10):
                test_events.append({
                    "ts": datetime.now(),
                    "chain": "ethereum",
                    "tx_hash": f"0x{uuid.uuid4().hex}",
                    "from_addr": "0x" + str(i) * 40,
                    "to_addr": "0x" + str(i+1) * 40,
                    "token": "",
                    "symbol": "ETH",
                    "amount": 1000.0 + i * 100,
                    "is_native": 1,
                    "exchange": "",
                    "amount_usd": 2500000.0 + i * 250000,
                    "from_exchange": "",
                    "from_country": "Unknown",
                    "from_city": "Unknown",
                    "to_exchange": "",
                    "to_country": "Unknown",
                    "to_city": "Unknown",
                    "is_cross_border": 0,
                    "source": f"concurrent_test_{i}",
                    "threshold_usd": 1000000.0,
                    "coin_rank": 1
                })
            
            # Insert all events concurrently
            results = await asyncio.gather(*[
                insert_whale_event(event) for event in test_events
            ])
            
            # All should succeed
            assert all(results)
            
            # Verify all events were inserted
            events = await get_whale_events(
                filters={"source": "concurrent_test_0"},
                limit=50
            )
            concurrent_events = [e for e in events if e["source"].startswith("concurrent_test_")]
            assert len(concurrent_events) >= 10
            
            print("✅ Concurrent whale detection successful")
        except Exception as e:
            pytest.fail(f"❌ Concurrent whale detection failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
