"""
Services Tests for Whale Monitoring System
Tests Price Service, Collector Manager, and core services
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from whales.services.price_service_whales import PriceService, price_service
from whales.collector_manager_whales import CollectorManager, collector_manager
from whales.collectors.blockchain_collector_whales import EthereumCollector, BinanceCollector
from whales.collectors.token_collector_whales import EthereumTokenCollector
from whales.config_whales import Config

class TestServicesWhales:
    
    @pytest.fixture
    def price_service_instance(self):
        """Create fresh PriceService instance for testing"""
        return PriceService()
    
    @pytest.fixture
    def collector_manager_instance(self):
        """Create fresh CollectorManager instance for testing"""
        return CollectorManager()
    
    @pytest.mark.asyncio
    async def test_price_service_initialization(self, price_service_instance):
        """Test PriceService initialization"""
        try:
            service = price_service_instance
            assert service.prices == {}
            assert service.update_interval == Config.PRICE_UPDATE_INTERVAL
            assert isinstance(service.coin_ids, dict)
            assert len(service.coin_ids) >= 12  # Should have all configured coins
            print("✅ PriceService initialization successful")
        except Exception as e:
            pytest.fail(f"❌ PriceService initialization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_price_service_update_prices(self, price_service_instance):
        """Test PriceService price updates"""
        try:
            service = price_service_instance
            
            # Mock CoinGecko API response
            mock_response = {
                "bitcoin": {"usd": 45000.0},
                "ethereum": {"usd": 2500.0},
                "binancecoin": {"usd": 350.0}
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
                mock_get.return_value = mock_context
                
                await service.update_prices()
                
                # Check if prices were updated
                assert service.get_price("bitcoin") == 45000.0
                assert service.get_price("ethereum") == 2500.0
                assert service.get_price("binancecoin") == 350.0
                
            print("✅ PriceService price updates successful")
        except Exception as e:
            pytest.fail(f"❌ PriceService price updates failed: {e}")
    
    @pytest.mark.asyncio
    async def test_price_service_get_price(self, price_service_instance):
        """Test PriceService get_price method"""
        try:
            service = price_service_instance
            
            # Set test prices
            service.prices = {
                "bitcoin": 45000.0,
                "ethereum": 2500.0
            }
            
            # Test existing prices
            assert service.get_price("bitcoin") == 45000.0
            assert service.get_price("ethereum") == 2500.0
            
            # Test non-existing price
            assert service.get_price("nonexistent") == 0.0
            
            print("✅ PriceService get_price method successful")
        except Exception as e:
            pytest.fail(f"❌ PriceService get_price method failed: {e}")
    
    @pytest.mark.asyncio
    async def test_price_service_update_interval(self, price_service_instance):
        """Test PriceService update interval behavior"""
        try:
            service = price_service_instance
            
            # Set a short update interval for testing
            service.update_interval = 1  # 1 second
            
            # First update
            await service.update_prices()
            first_update_time = service.last_update
            
            # Immediate second update (should be skipped)
            await service.update_prices()
            second_update_time = service.last_update
            
            # Should be the same time (update skipped)
            assert first_update_time == second_update_time
            
            # Wait and update again
            await asyncio.sleep(1.1)
            await service.update_prices()
            third_update_time = service.last_update
            
            # Should be different time (update executed)
            assert third_update_time > first_update_time
            
            print("✅ PriceService update interval behavior successful")
        except Exception as e:
            pytest.fail(f"❌ PriceService update interval behavior failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_manager_initialization(self, collector_manager_instance):
        """Test CollectorManager initialization"""
        try:
            manager = collector_manager_instance
            assert manager.collectors == {}
            assert isinstance(manager.collector_classes, dict)
            assert len(manager.collector_classes) == 6  # 3 chains x 2 collector types
            
            # Check collector classes
            assert "ethereum" in manager.collector_classes
            assert "binance" in manager.collector_classes
            assert "polygon" in manager.collector_classes
            assert "ethereum_tokens" in manager.collector_classes
            assert "binance_tokens" in manager.collector_classes
            assert "polygon_tokens" in manager.collector_classes
            
            print("✅ CollectorManager initialization successful")
        except Exception as e:
            pytest.fail(f"❌ CollectorManager initialization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_manager_start_collector(self, collector_manager_instance):
        """Test CollectorManager start_collector method"""
        try:
            manager = collector_manager_instance
            
            # Mock collector
            mock_collector = Mock()
            mock_collector.start = AsyncMock()
            
            with patch.object(manager.collector_classes["ethereum"], '__call__', return_value=mock_collector):
                await manager.start_collector("ethereum")
                
                # Check collector was added
                assert "ethereum" in manager.collectors
                assert manager.collectors["ethereum"] == mock_collector
                mock_collector.start.assert_called_once()
                
            print("✅ CollectorManager start_collector successful")
        except Exception as e:
            pytest.fail(f"❌ CollectorManager start_collector failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_manager_stop_collector(self, collector_manager_instance):
        """Test CollectorManager stop_collector method"""
        try:
            manager = collector_manager_instance
            
            # Mock collector
            mock_collector = Mock()
            mock_collector.stop = AsyncMock()
            
            # Add collector to manager
            manager.collectors["ethereum"] = mock_collector
            
            # Stop collector
            await manager.stop_collector("ethereum")
            
            # Check collector was removed
            assert "ethereum" not in manager.collectors
            mock_collector.stop.assert_called_once()
            
            print("✅ CollectorManager stop_collector successful")
        except Exception as e:
            pytest.fail(f"❌ CollectorManager stop_collector failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_manager_stop_all(self, collector_manager_instance):
        """Test CollectorManager stop_all method"""
        try:
            manager = collector_manager_instance
            
            # Mock collectors
            mock_collectors = {}
            for name in ["ethereum", "binance", "polygon"]:
                mock_collector = Mock()
                mock_collector.stop = AsyncMock()
                mock_collectors[name] = mock_collector
                manager.collectors[name] = mock_collector
            
            # Stop all collectors
            await manager.stop_all()
            
            # Check all collectors were stopped and removed
            assert len(manager.collectors) == 0
            for mock_collector in mock_collectors.values():
                mock_collector.stop.assert_called_once()
            
            print("✅ CollectorManager stop_all successful")
        except Exception as e:
            pytest.fail(f"❌ CollectorManager stop_all failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_manager_duplicate_start(self, collector_manager_instance):
        """Test CollectorManager duplicate start handling"""
        try:
            manager = collector_manager_instance
            
            # Mock collector
            mock_collector = Mock()
            mock_collector.start = AsyncMock()
            
            # Add collector to manager
            manager.collectors["ethereum"] = mock_collector
            
            # Try to start same collector again
            with patch.object(manager.collector_classes["ethereum"], '__call__', return_value=mock_collector):
                await manager.start_collector("ethereum")
                
                # Should still have only one collector
                assert len(manager.collectors) == 1
                assert manager.collectors["ethereum"] == mock_collector
                
            print("✅ CollectorManager duplicate start handling successful")
        except Exception as e:
            pytest.fail(f"❌ CollectorManager duplicate start handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_manager_invalid_collector(self, collector_manager_instance):
        """Test CollectorManager invalid collector handling"""
        try:
            manager = collector_manager_instance
            
            # Try to start invalid collector
            await manager.start_collector("invalid_collector")
            
            # Should not have added any collectors
            assert len(manager.collectors) == 0
            
            print("✅ CollectorManager invalid collector handling successful")
        except Exception as e:
            pytest.fail(f"❌ CollectorManager invalid collector handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_manager_init_from_config(self, collector_manager_instance):
        """Test CollectorManager init_from_config method"""
        try:
            manager = collector_manager_instance
            
            # Mock API keys
            with patch.object(Config, 'ETHEREUM_API_KEY', 'test_key'):
                with patch.object(Config, 'BSC_API_KEY', ''):
                    with patch.object(Config, 'POLYGON_API_KEY', ''):
                        
                        # Mock collector classes
                        for name in ["ethereum", "ethereum_tokens"]:
                            mock_collector = Mock()
                            mock_collector.start = AsyncMock()
                            manager.collector_classes[name] = Mock(return_value=mock_collector)
                        
                        await manager.init_from_config()
                        
                        # Should have started only Ethereum collectors
                        assert len(manager.collectors) == 2
                        assert "ethereum" in manager.collectors
                        assert "ethereum_tokens" in manager.collectors
                        
            print("✅ CollectorManager init_from_config successful")
        except Exception as e:
            pytest.fail(f"❌ CollectorManager init_from_config failed: {e}")
    
    @pytest.mark.asyncio
    async def test_ethereum_collector_initialization(self):
        """Test EthereumCollector initialization"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            collector = EthereumCollector()
            assert collector.chain == "ethereum"
            assert collector.native_symbol == "ETH"
            assert collector.api_key == Config.ETHEREUM_API_KEY
            assert collector.running == False
            
            print("✅ EthereumCollector initialization successful")
        except Exception as e:
            pytest.fail(f"❌ EthereumCollector initialization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_binance_collector_initialization(self):
        """Test BinanceCollector initialization"""
        try:
            if not Config.BSC_API_KEY:
                pytest.skip("BSC API key not configured")
            
            collector = BinanceCollector()
            assert collector.chain == "binance"
            assert collector.native_symbol == "BNB"
            assert collector.api_key == Config.BSC_API_KEY
            assert collector.running == False
            
            print("✅ BinanceCollector initialization successful")
        except Exception as e:
            pytest.fail(f"❌ BinanceCollector initialization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_token_collector_initialization(self):
        """Test TokenCollector initialization"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            collector = EthereumTokenCollector()
            assert collector.chain == "ethereum"
            assert collector.running == False
            assert collector.token_cache == {}
            
            print("✅ TokenCollector initialization successful")
        except Exception as e:
            pytest.fail(f"❌ TokenCollector initialization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_location_mapping(self):
        """Test collector location mapping"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            collector = EthereumCollector()
            
            # Test known exchange address
            binance_addr = "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE"
            location = collector.get_location(binance_addr)
            
            assert location["exchange"] == "Binance"
            assert location["country"] == "Malta"
            assert location["city"] == "Valletta"
            
            # Test unknown address
            unknown_addr = "0x" + "1" * 40
            location = collector.get_location(unknown_addr)
            
            assert location["exchange"] == ""
            assert location["country"] == "Unknown"
            assert location["city"] == "Unknown"
            
            print("✅ Collector location mapping successful")
        except Exception as e:
            pytest.fail(f"❌ Collector location mapping failed: {e}")
    
    @pytest.mark.asyncio
    async def test_service_integration(self):
        """Test service integration between components"""
        try:
            # Test price service integration
            test_price_service = PriceService()
            test_price_service.prices = {"bitcoin": 45000.0}
            
            # Test collector manager integration
            test_collector_manager = CollectorManager()
            
            # Verify they work together
            assert test_price_service.get_price("bitcoin") == 45000.0
            assert len(test_collector_manager.collector_classes) == 6
            
            print("✅ Service integration successful")
        except Exception as e:
            pytest.fail(f"❌ Service integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_global_service_instances(self):
        """Test global service instances"""
        try:
            # Test global price service
            assert price_service is not None
            assert isinstance(price_service, PriceService)
            
            # Test global collector manager
            assert collector_manager is not None
            assert isinstance(collector_manager, CollectorManager)
            
            print("✅ Global service instances successful")
        except Exception as e:
            pytest.fail(f"❌ Global service instances failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
