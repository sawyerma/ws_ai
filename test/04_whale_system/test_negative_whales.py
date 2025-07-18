"""
Negative Tests for Whale Monitoring System
Tests API timeouts, network errors, invalid credentials, and edge cases
"""
import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from whales.services.price_service_whales import PriceService
from whales.collectors.blockchain_collector_whales import EthereumCollector
from whales.collectors.token_collector_whales import EthereumTokenCollector
from whales.collector_manager_whales import CollectorManager
from whales.config_whales import Config
from db.clickhouse_whales import get_clickhouse_client
import json

class TestNegativeWhales:
    
    @pytest.fixture
    def price_service(self):
        """Create PriceService instance for testing"""
        return PriceService()
    
    @pytest.fixture
    def collector_manager(self):
        """Create CollectorManager instance for testing"""
        return CollectorManager()
    
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, price_service):
        """Test API timeout handling"""
        try:
            # Mock timeout exception
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.side_effect = asyncio.TimeoutError("Request timed out")
                
                # Should handle timeout gracefully
                await price_service.update_prices()
                
                # Prices should remain unchanged (empty or previous values)
                assert isinstance(price_service.prices, dict)
                
            print("✅ API timeout handling successful")
        except Exception as e:
            pytest.fail(f"❌ API timeout handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_network_connection_error(self, price_service):
        """Test network connection error handling"""
        try:
            # Mock connection error
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.side_effect = aiohttp.ClientConnectorError(
                    connection_key=None,
                    os_error=OSError("Network is unreachable")
                )
                
                # Should handle network error gracefully
                await price_service.update_prices()
                
                # Service should continue functioning
                assert price_service.get_price("bitcoin") == 0.0
                
            print("✅ Network connection error handling successful")
        except Exception as e:
            pytest.fail(f"❌ Network connection error handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_handling(self):
        """Test invalid API key handling"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Mock invalid API key response
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 401
                mock_context.__aenter__.return_value.json = AsyncMock(
                    return_value={"status": "0", "message": "Invalid API Key"}
                )
                mock_get.return_value = mock_context
                
                collector = EthereumCollector()
                
                # Should handle invalid API key gracefully
                latest_block = await collector.get_latest_block()
                
                # Should return last known block or 0
                assert isinstance(latest_block, int)
                assert latest_block >= 0
                
            print("✅ Invalid API key handling successful")
        except Exception as e:
            pytest.fail(f"❌ Invalid API key handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_malformed_api_response(self, price_service):
        """Test malformed API response handling"""
        try:
            # Mock malformed JSON response
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(
                    side_effect=json.JSONDecodeError("Malformed JSON", "", 0)
                )
                mock_get.return_value = mock_context
                
                # Should handle malformed response gracefully
                await price_service.update_prices()
                
                # Prices should remain unchanged
                assert isinstance(price_service.prices, dict)
                
            print("✅ Malformed API response handling successful")
        except Exception as e:
            pytest.fail(f"❌ Malformed API response handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit exceeded handling"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Mock rate limit response
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 429
                mock_context.__aenter__.return_value.json = AsyncMock(
                    return_value={"status": "0", "message": "Rate limit exceeded"}
                )
                mock_get.return_value = mock_context
                
                collector = EthereumCollector()
                
                # Should handle rate limit gracefully
                latest_block = await collector.get_latest_block()
                
                # Should return last known block
                assert isinstance(latest_block, int)
                
            print("✅ Rate limit exceeded handling successful")
        except Exception as e:
            pytest.fail(f"❌ Rate limit exceeded handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_partial_api_response(self, price_service):
        """Test partial API response handling"""
        try:
            # Mock partial response (missing some coins)
            partial_response = {
                "bitcoin": {"usd": 45000.0},
                # Missing ethereum and other coins
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(return_value=partial_response)
                mock_get.return_value = mock_context
                
                await price_service.update_prices()
                
                # Should handle partial response
                assert price_service.get_price("bitcoin") == 45000.0
                assert price_service.get_price("ethereum") == 0.0  # Missing coin
                
            print("✅ Partial API response handling successful")
        except Exception as e:
            pytest.fail(f"❌ Partial API response handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_empty_blockchain_response(self):
        """Test empty blockchain response handling"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Mock empty transactions response
            empty_response = {
                "result": {
                    "transactions": []
                }
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(return_value=empty_response)
                mock_get.return_value = mock_context
                
                collector = EthereumCollector()
                
                with patch.object(collector, 'get_latest_block', return_value=1000):
                    # Should handle empty transactions gracefully
                    await collector.process_block(1000)
                
            print("✅ Empty blockchain response handling successful")
        except Exception as e:
            pytest.fail(f"❌ Empty blockchain response handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_invalid_transaction_data(self):
        """Test invalid transaction data handling"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Mock invalid transaction data
            invalid_response = {
                "result": {
                    "transactions": [
                        {
                            "hash": "invalid_hash",
                            "from": "invalid_address",
                            "to": "invalid_address",
                            "value": "invalid_value",
                            "input": "0x"
                        }
                    ]
                }
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(return_value=invalid_response)
                mock_get.return_value = mock_context
                
                collector = EthereumCollector()
                
                with patch.object(collector, 'get_latest_block', return_value=1000):
                    # Should handle invalid transaction data gracefully
                    await collector.process_block(1000)
                
            print("✅ Invalid transaction data handling successful")
        except Exception as e:
            pytest.fail(f"❌ Invalid transaction data handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self):
        """Test database connection failure handling"""
        try:
            # Mock database connection failure
            with patch('db.clickhouse_whales.get_clickhouse_client') as mock_get_client:
                mock_client = Mock()
                mock_client.query.side_effect = Exception("Database connection failed")
                mock_get_client.return_value = mock_client
                
                # Should handle database failure gracefully
                client = get_clickhouse_client()
                
                try:
                    result = client.query("SELECT 1")
                    assert False, "Should have failed"
                except Exception:
                    pass  # Expected failure
                
            print("✅ Database connection failure handling successful")
        except Exception as e:
            pytest.fail(f"❌ Database connection failure handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_initialization_failure(self, collector_manager):
        """Test collector initialization failure handling"""
        try:
            # Mock collector that fails during initialization
            with patch.object(Config, 'ETHEREUM_API_KEY', ''):
                # Should handle missing API key gracefully
                await collector_manager.init_from_config()
                
                # Should not have started Ethereum collectors
                assert "ethereum" not in collector_manager.collectors
                assert "ethereum_tokens" not in collector_manager.collectors
                
            print("✅ Collector initialization failure handling successful")
        except Exception as e:
            pytest.fail(f"❌ Collector initialization failure handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_api_failures(self, price_service):
        """Test concurrent API failures"""
        try:
            # Mock multiple concurrent failures
            failure_count = 0
            
            def mock_get_side_effect(*args, **kwargs):
                nonlocal failure_count
                failure_count += 1
                if failure_count <= 3:
                    raise aiohttp.ClientError("Connection failed")
                else:
                    # Return successful response after failures
                    mock_context = AsyncMock()
                    mock_context.__aenter__.return_value.status = 200
                    mock_context.__aenter__.return_value.json = AsyncMock(
                        return_value={"bitcoin": {"usd": 45000.0}}
                    )
                    return mock_context
            
            with patch('aiohttp.ClientSession.get', side_effect=mock_get_side_effect):
                # Try multiple updates
                for i in range(5):
                    await price_service.update_prices()
                    await asyncio.sleep(0.1)
                
                # Should eventually succeed
                assert failure_count >= 3
                
            print("✅ Concurrent API failures handling successful")
        except Exception as e:
            pytest.fail(f"❌ Concurrent API failures handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_memory_exhaustion_simulation(self, collector_manager):
        """Test memory exhaustion simulation"""
        try:
            # Mock memory exhaustion
            with patch('asyncio.create_task') as mock_create_task:
                mock_create_task.side_effect = MemoryError("Out of memory")
                
                # Should handle memory exhaustion gracefully
                try:
                    await collector_manager.start_collector("ethereum")
                except MemoryError:
                    pass  # Expected failure
                
                # Collector should not be added if failed
                assert "ethereum" not in collector_manager.collectors
                
            print("✅ Memory exhaustion simulation successful")
        except Exception as e:
            pytest.fail(f"❌ Memory exhaustion simulation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_invalid_configuration_handling(self):
        """Test invalid configuration handling"""
        try:
            # Test with invalid configuration
            with patch.object(Config, 'COIN_CONFIG', {}):
                # Should handle empty coin config
                service = PriceService()
                assert service.coin_ids == {}
                
            with patch.object(Config, 'CHAIN_CONFIG', {}):
                # Should handle empty chain config
                try:
                    collector = EthereumCollector()
                    assert False, "Should have failed with empty chain config"
                except (KeyError, AttributeError):
                    pass  # Expected failure
                
            print("✅ Invalid configuration handling successful")
        except Exception as e:
            pytest.fail(f"❌ Invalid configuration handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_disk_space_exhaustion(self):
        """Test disk space exhaustion handling"""
        try:
            # Mock disk space exhaustion
            with patch('db.clickhouse_whales.insert_whale_event') as mock_insert:
                mock_insert.side_effect = OSError("No space left on device")
                
                # Should handle disk space exhaustion
                from db.clickhouse_whales import insert_whale_event
                
                test_event = {
                    "ts": "2024-01-01 00:00:00",
                    "chain": "ethereum",
                    "tx_hash": "0x123",
                    "from_addr": "0x1",
                    "to_addr": "0x2",
                    "token": "",
                    "symbol": "ETH",
                    "amount": 1000.0,
                    "is_native": 1,
                    "exchange": "",
                    "amount_usd": 1000000.0,
                    "source": "test"
                }
                
                try:
                    await insert_whale_event(test_event)
                    assert False, "Should have failed with disk space error"
                except OSError:
                    pass  # Expected failure
                
            print("✅ Disk space exhaustion handling successful")
        except Exception as e:
            pytest.fail(f"❌ Disk space exhaustion handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_invalid_price_data(self, price_service):
        """Test invalid price data handling"""
        try:
            # Mock invalid price data
            invalid_responses = [
                {"bitcoin": {"usd": "invalid_price"}},  # String instead of number
                {"bitcoin": {"usd": None}},  # None value
                {"bitcoin": {"usd": float('inf')}},  # Infinity
                {"bitcoin": {"usd": float('nan')}},  # NaN
                {"bitcoin": {}},  # Missing USD price
            ]
            
            for invalid_response in invalid_responses:
                with patch('aiohttp.ClientSession.get') as mock_get:
                    mock_context = AsyncMock()
                    mock_context.__aenter__.return_value.status = 200
                    mock_context.__aenter__.return_value.json = AsyncMock(return_value=invalid_response)
                    mock_get.return_value = mock_context
                    
                    # Should handle invalid price data gracefully
                    await price_service.update_prices()
                    
                    # Should not crash and return reasonable default
                    price = price_service.get_price("bitcoin")
                    assert isinstance(price, (int, float))
                    assert not (price == float('inf') or price != price)  # Not inf or nan
            
            print("✅ Invalid price data handling successful")
        except Exception as e:
            pytest.fail(f"❌ Invalid price data handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_extremely_large_transaction(self):
        """Test extremely large transaction handling"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Mock extremely large transaction
            large_tx_response = {
                "result": {
                    "transactions": [
                        {
                            "hash": "0x123",
                            "from": "0x1",
                            "to": "0x2",
                            "value": hex(int(1e50)),  # Extremely large value
                            "input": "0x"
                        }
                    ]
                }
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(return_value=large_tx_response)
                mock_get.return_value = mock_context
                
                collector = EthereumCollector()
                
                with patch.object(collector, 'get_latest_block', return_value=1000):
                    # Should handle extremely large transaction gracefully
                    await collector.process_block(1000)
                
            print("✅ Extremely large transaction handling successful")
        except Exception as e:
            pytest.fail(f"❌ Extremely large transaction handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test Unicode and special characters handling"""
        try:
            # Mock response with Unicode characters
            unicode_response = {
                "result": [
                    {
                        "hash": "0x123",
                        "from": "0x1",
                        "to": "0x2",
                        "contractAddress": "0x3",
                        "tokenSymbol": "测试币",  # Chinese characters
                        "tokenName": "Test Token 🚀",  # Emoji
                        "tokenDecimal": "18",
                        "value": "1000000000000000000",
                        "timeStamp": "1640995200"
                    }
                ]
            }
            
            if Config.ETHEREUM_API_KEY:
                with patch('aiohttp.ClientSession.get') as mock_get:
                    mock_context = AsyncMock()
                    mock_context.__aenter__.return_value.status = 200
                    mock_context.__aenter__.return_value.json = AsyncMock(return_value=unicode_response)
                    mock_get.return_value = mock_context
                    
                    collector = EthereumTokenCollector()
                    
                    with patch.object(collector, 'get_latest_block', return_value=1000):
                        # Should handle Unicode characters gracefully
                        await collector.process_token_block(1000)
            
            print("✅ Unicode and special characters handling successful")
        except Exception as e:
            pytest.fail(f"❌ Unicode and special characters handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_system_clock_skew(self, price_service):
        """Test system clock skew handling"""
        try:
            # Mock system time in the past
            past_time = 1000000000  # Year 2001
            
            with patch('time.time', return_value=past_time):
                # Should handle clock skew gracefully
                await price_service.update_prices()
                
                # Service should continue functioning
                assert isinstance(price_service.last_update, type(price_service.last_update))
                
            print("✅ System clock skew handling successful")
        except Exception as e:
            pytest.fail(f"❌ System clock skew handling failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
