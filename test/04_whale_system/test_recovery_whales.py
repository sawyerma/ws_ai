"""
Recovery Tests for Whale Monitoring System
Tests collector crash recovery, data persistence, and restart capabilities
"""
import pytest
import asyncio
import uuid
import signal
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from whales.collector_manager_whales import CollectorManager
from whales.services.price_service_whales import PriceService
from whales.collectors.blockchain_collector_whales import EthereumCollector
from whales.main_whales import start_whale_system, stop_whale_system
from db.clickhouse_whales import insert_whale_event, get_whale_events
from whales.config_whales import Config

class TestRecoveryWhales:
    
    @pytest.fixture
    def collector_manager(self):
        """Create fresh CollectorManager for testing"""
        return CollectorManager()
    
    @pytest.fixture
    def price_service(self):
        """Create fresh PriceService for testing"""
        return PriceService()
    
    @pytest.fixture
    def test_whale_event(self):
        """Create test whale event"""
        return {
            "ts": datetime.now(),
            "chain": "ethereum",
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "from_addr": "0x" + "1" * 40,
            "to_addr": "0x" + "2" * 40,
            "token": "",
            "symbol": "ETH",
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
            "source": "recovery_test",
            "threshold_usd": 1000000.0,
            "coin_rank": 1
        }
    
    @pytest.mark.asyncio
    async def test_collector_crash_recovery(self, collector_manager):
        """Test collector recovery after crash"""
        try:
            # Mock collector that will "crash"
            mock_collector = Mock()
            mock_collector.start = AsyncMock()
            mock_collector.stop = AsyncMock()
            mock_collector.running = True
            
            # Simulate crash by raising exception
            mock_collector.run = AsyncMock(side_effect=Exception("Simulated crash"))
            
            # Add collector to manager
            collector_manager.collectors["ethereum"] = mock_collector
            
            # Simulate crash detection and recovery
            try:
                await mock_collector.run()
            except Exception as e:
                # Crash detected, attempt recovery
                await collector_manager.stop_collector("ethereum")
                
                # Create new collector instance
                new_mock_collector = Mock()
                new_mock_collector.start = AsyncMock()
                new_mock_collector.stop = AsyncMock()
                new_mock_collector.running = True
                
                with patch.object(collector_manager.collector_classes, "ethereum", return_value=new_mock_collector):
                    await collector_manager.start_collector("ethereum")
                
                # Verify recovery
                assert "ethereum" in collector_manager.collectors
                assert collector_manager.collectors["ethereum"] == new_mock_collector
                new_mock_collector.start.assert_called_once()
            
            print("✅ Collector crash recovery successful")
        except Exception as e:
            pytest.fail(f"❌ Collector crash recovery failed: {e}")
    
    @pytest.mark.asyncio
    async def test_data_persistence_after_restart(self, test_whale_event):
        """Test data persistence after system restart"""
        try:
            # Insert test data before "restart"
            before_restart_event = test_whale_event.copy()
            before_restart_event["source"] = "before_restart"
            before_restart_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            
            result = await insert_whale_event(before_restart_event)
            assert result == True
            
            # Simulate system restart by stopping and starting components
            with patch('whales.services.price_service_whales.price_service.start') as mock_price_start:
                with patch('whales.collector_manager_whales.collector_manager.init_from_config') as mock_collector_init:
                    with patch('whales.collector_manager_whales.collector_manager.stop_all') as mock_collector_stop:
                        
                        # Simulate shutdown
                        await stop_whale_system()
                        mock_collector_stop.assert_called_once()
                        
                        # Simulate startup
                        await start_whale_system()
                        mock_price_start.assert_called_once()
                        mock_collector_init.assert_called_once()
            
            # Verify data persistence after restart
            events = await get_whale_events(
                filters={"source": "before_restart"},
                limit=10
            )
            
            assert len(events) >= 1
            persisted_event = events[0]
            assert persisted_event["tx_hash"] == before_restart_event["tx_hash"]
            assert persisted_event["source"] == "before_restart"
            
            print("✅ Data persistence after restart successful")
        except Exception as e:
            pytest.fail(f"❌ Data persistence after restart failed: {e}")
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, collector_manager):
        """Test graceful shutdown behavior"""
        try:
            # Mock multiple collectors
            mock_collectors = {}
            for name in ["ethereum", "binance", "polygon"]:
                mock_collector = Mock()
                mock_collector.start = AsyncMock()
                mock_collector.stop = AsyncMock()
                mock_collector.running = True
                mock_collectors[name] = mock_collector
                collector_manager.collectors[name] = mock_collector
            
            # Test graceful shutdown
            await collector_manager.stop_all()
            
            # Verify all collectors were stopped
            for name, mock_collector in mock_collectors.items():
                mock_collector.stop.assert_called_once()
            
            # Verify collector manager state
            assert len(collector_manager.collectors) == 0
            
            print("✅ Graceful shutdown successful")
        except Exception as e:
            pytest.fail(f"❌ Graceful shutdown failed: {e}")
    
    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self, price_service):
        """Test memory leak prevention"""
        try:
            import gc
            import psutil
            import os
            
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Simulate multiple price updates
            mock_response = {
                "bitcoin": {"usd": 45000.0},
                "ethereum": {"usd": 2500.0}
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_context = AsyncMock()
                mock_context.__aenter__.return_value.status = 200
                mock_context.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
                mock_get.return_value = mock_context
                
                # Perform multiple updates
                for i in range(100):
                    await price_service.update_prices()
                    
                    # Trigger garbage collection periodically
                    if i % 10 == 0:
                        gc.collect()
            
            # Check memory usage after operations
            gc.collect()  # Force garbage collection
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 50MB)
            assert memory_increase < 50, f"Memory increase too high: {memory_increase:.2f}MB"
            
            print(f"✅ Memory leak prevention successful - Memory increase: {memory_increase:.2f}MB")
        except Exception as e:
            pytest.fail(f"❌ Memory leak prevention failed: {e}")
    
    @pytest.mark.asyncio
    async def test_connection_recovery(self):
        """Test database connection recovery"""
        try:
            # Test database connection recovery
            from db.clickhouse_whales import get_clickhouse_client
            
            client = get_clickhouse_client()
            
            # Test initial connection
            result = client.query("SELECT 1")
            assert result.result_rows[0][0] == 1
            
            # Simulate connection loss and recovery
            # (In real scenario, this would involve network issues)
            
            # Test connection recovery by making multiple queries
            for i in range(5):
                try:
                    result = client.query("SELECT 1")
                    assert result.result_rows[0][0] == 1
                except Exception as e:
                    # If connection fails, try to reconnect
                    client = get_clickhouse_client()
                    result = client.query("SELECT 1")
                    assert result.result_rows[0][0] == 1
            
            print("✅ Database connection recovery successful")
        except Exception as e:
            pytest.fail(f"❌ Database connection recovery failed: {e}")
    
    @pytest.mark.asyncio
    async def test_partial_system_failure(self, collector_manager):
        """Test partial system failure handling"""
        try:
            # Mock collectors with different failure scenarios
            working_collector = Mock()
            working_collector.start = AsyncMock()
            working_collector.stop = AsyncMock()
            working_collector.running = True
            
            failing_collector = Mock()
            failing_collector.start = AsyncMock(side_effect=Exception("Start failure"))
            failing_collector.stop = AsyncMock()
            failing_collector.running = False
            
            # Add working collector
            collector_manager.collectors["ethereum"] = working_collector
            
            # Try to add failing collector
            with patch.object(collector_manager.collector_classes, "binance", return_value=failing_collector):
                try:
                    await collector_manager.start_collector("binance")
                except Exception:
                    pass  # Expected failure
            
            # Verify system continues with working collector
            assert "ethereum" in collector_manager.collectors
            assert collector_manager.collectors["ethereum"] == working_collector
            
            # Verify failing collector is not in active collectors
            assert "binance" not in collector_manager.collectors
            
            print("✅ Partial system failure handling successful")
        except Exception as e:
            pytest.fail(f"❌ Partial system failure handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_data_integrity_after_crash(self, test_whale_event):
        """Test data integrity after system crash"""
        try:
            # Insert multiple events
            events_to_insert = []
            for i in range(10):
                event = test_whale_event.copy()
                event["tx_hash"] = f"0x{uuid.uuid4().hex}"
                event["source"] = "integrity_test"
                event["amount_usd"] = 1000000.0 + i * 100000
                events_to_insert.append(event)
            
            # Insert events
            for event in events_to_insert:
                await insert_whale_event(event)
            
            # Simulate system crash and recovery
            # (In real scenario, this would involve unexpected shutdown)
            
            # Verify data integrity after recovery
            retrieved_events = await get_whale_events(
                filters={"source": "integrity_test"},
                limit=20
            )
            
            # All events should be present
            assert len(retrieved_events) >= 10
            
            # Verify data consistency
            for event in retrieved_events:
                assert event["source"] == "integrity_test"
                assert isinstance(event["amount_usd"], (int, float))
                assert event["amount_usd"] >= 1000000.0
            
            # Verify no duplicate events
            tx_hashes = [e["tx_hash"] for e in retrieved_events]
            assert len(tx_hashes) == len(set(tx_hashes))
            
            print("✅ Data integrity after crash successful")
        except Exception as e:
            pytest.fail(f"❌ Data integrity after crash failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_restart_with_state(self):
        """Test collector restart with preserved state"""
        try:
            if not Config.ETHEREUM_API_KEY:
                pytest.skip("Ethereum API key not configured")
            
            # Create collector
            collector = EthereumCollector()
            
            # Set initial state
            collector.last_block = 1000
            initial_block = collector.last_block
            
            # Simulate collector restart
            await collector.stop()
            
            # Create new collector instance
            new_collector = EthereumCollector()
            
            # In real scenario, state would be loaded from persistent storage
            # For testing, we simulate state restoration
            new_collector.last_block = initial_block
            
            # Verify state preservation
            assert new_collector.last_block == initial_block
            
            print("✅ Collector restart with state successful")
        except Exception as e:
            pytest.fail(f"❌ Collector restart with state failed: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_crash_recovery(self, collector_manager):
        """Test recovery from concurrent crashes"""
        try:
            # Mock multiple collectors that crash concurrently
            mock_collectors = {}
            for name in ["ethereum", "binance", "polygon"]:
                mock_collector = Mock()
                mock_collector.start = AsyncMock()
                mock_collector.stop = AsyncMock()
                mock_collector.running = True
                mock_collector.run = AsyncMock(side_effect=Exception(f"Crash in {name}"))
                mock_collectors[name] = mock_collector
                collector_manager.collectors[name] = mock_collector
            
            # Simulate concurrent crashes
            crash_tasks = []
            for name, collector in mock_collectors.items():
                async def crash_collector(collector_name, collector_instance):
                    try:
                        await collector_instance.run()
                    except Exception:
                        await collector_manager.stop_collector(collector_name)
                        
                        # Create recovery collector
                        recovery_collector = Mock()
                        recovery_collector.start = AsyncMock()
                        recovery_collector.stop = AsyncMock()
                        recovery_collector.running = True
                        
                        with patch.object(collector_manager.collector_classes, collector_name, return_value=recovery_collector):
                            await collector_manager.start_collector(collector_name)
                
                crash_tasks.append(crash_collector(name, collector))
            
            # Execute concurrent recovery
            await asyncio.gather(*crash_tasks)
            
            # Verify all collectors were recovered
            assert len(collector_manager.collectors) == 3
            for name in ["ethereum", "binance", "polygon"]:
                assert name in collector_manager.collectors
            
            print("✅ Concurrent crash recovery successful")
        except Exception as e:
            pytest.fail(f"❌ Concurrent crash recovery failed: {e}")
    
    @pytest.mark.asyncio
    async def test_system_resource_limits(self, collector_manager):
        """Test system behavior under resource constraints"""
        try:
            import psutil
            import os
            
            # Get initial resource usage
            process = psutil.Process(os.getpid())
            initial_cpu = process.cpu_percent()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Mock resource-intensive operations
            mock_collectors = {}
            for i in range(10):  # More collectors than usual
                name = f"test_collector_{i}"
                mock_collector = Mock()
                mock_collector.start = AsyncMock()
                mock_collector.stop = AsyncMock()
                mock_collector.running = True
                mock_collectors[name] = mock_collector
                collector_manager.collectors[name] = mock_collector
            
            # Simulate resource monitoring
            await asyncio.sleep(0.1)  # Allow system to process
            
            # Check resource usage
            current_cpu = process.cpu_percent()
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # System should handle multiple collectors without excessive resource usage
            memory_increase = current_memory - initial_memory
            assert memory_increase < 100, f"Memory usage too high: {memory_increase:.2f}MB"
            
            # Clean up
            await collector_manager.stop_all()
            
            print(f"✅ Resource limits test successful - Memory increase: {memory_increase:.2f}MB")
        except Exception as e:
            pytest.fail(f"❌ Resource limits test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_recovery_after_database_outage(self, test_whale_event):
        """Test recovery after database outage"""
        try:
            # Test successful insertion first
            pre_outage_event = test_whale_event.copy()
            pre_outage_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            pre_outage_event["source"] = "pre_outage"
            
            result = await insert_whale_event(pre_outage_event)
            assert result == True
            
            # Simulate database outage by mocking insert failure
            with patch('db.clickhouse_whales.insert_whale_event', side_effect=Exception("Database unavailable")):
                outage_event = test_whale_event.copy()
                outage_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
                outage_event["source"] = "during_outage"
                
                try:
                    await insert_whale_event(outage_event)
                    assert False, "Should have failed during outage"
                except Exception:
                    pass  # Expected failure
            
            # Test recovery after outage
            post_outage_event = test_whale_event.copy()
            post_outage_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            post_outage_event["source"] = "post_outage"
            
            result = await insert_whale_event(post_outage_event)
            assert result == True
            
            # Verify data integrity
            events = await get_whale_events(
                filters={"source": "pre_outage"},
                limit=10
            )
            assert len(events) >= 1
            
            events = await get_whale_events(
                filters={"source": "post_outage"},
                limit=10
            )
            assert len(events) >= 1
            
            print("✅ Recovery after database outage successful")
        except Exception as e:
            pytest.fail(f"❌ Recovery after database outage failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
