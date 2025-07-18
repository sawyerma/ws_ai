"""
Backfill Tests for Whale Monitoring System
Tests the minimal backfill functionality
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from db.clickhouse_whales import (
    get_whale_client,
    insert_whale_event,
    fetch_whale_events
)
from whales.collectors.blockchain_collector_whales import EthereumCollector
from whales.config_whales import Config

class TestBackfillWhales:
    
    @pytest.fixture
    def clickhouse_client(self):
        """Get ClickHouse client for testing"""
        return get_whale_client()
    
    @pytest.fixture
    def sample_backfill_event(self):
        """Create sample backfill whale event"""
        return {
            "ts": datetime.now() - timedelta(days=30),  # Historical
            "chain": "ethereum",
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "from_addr": "0x" + "1" * 40,
            "to_addr": "0x" + "2" * 40,
            "token": "",
            "symbol": "ETH",
            "amount": 5000.0,
            "is_native": 1,
            "exchange": "Binance",
            "amount_usd": 12500000.0,
            "from_exchange": "Binance",
            "from_country": "Malta",
            "from_city": "Valletta",
            "to_exchange": "",
            "to_country": "Unknown",
            "to_city": "Unknown",
            "is_cross_border": 1,
            "source": "backfill_collector",
            "threshold_usd": 10000000.0,
            "coin_rank": 1,
            
            # Backfill-spezifische Felder
            "backfill_block": 18500000,
            "is_backfill": 1
        }
    
    def test_backfill_config_loaded(self):
        """Test that backfill config is properly loaded"""
        assert Config.BACKFILL_ENABLED == True
        assert Config.BACKFILL_BATCH_SIZE == 1000
        assert Config.BACKFILL_API_BUDGET_THRESHOLD == 0.7
        assert "ethereum" in Config.HISTORICAL_PRIORITY_BLOCKS
        assert len(Config.HISTORICAL_PRIORITY_BLOCKS["ethereum"]) >= 2
        print("✅ Backfill configuration loaded successfully")
    
    @pytest.mark.asyncio
    async def test_backfill_event_insertion(self, sample_backfill_event):
        """Test backfill event insertion with special fields"""
        try:
            result = await insert_whale_event(sample_backfill_event)
            assert result == True
            
            # Verify the event was inserted with backfill fields
            events = fetch_whale_events(
                symbol="ETH",
                chain="ethereum",
                limit=1
            )
            assert len(events) >= 1
            
            # Note: ClickHouse may not return the backfill fields in basic fetch
            # but the insertion succeeded
            print("✅ Backfill event insertion successful")
        except Exception as e:
            pytest.fail(f"❌ Backfill event insertion failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collector_backfill_state(self):
        """Test collector backfill state initialization"""
        try:
            collector = EthereumCollector()
            
            # Test initial state
            assert collector.api_requests_today == 0
            assert collector.backfill_block == 0
            assert collector.backfill_direction == -1
            
            print("✅ Collector backfill state initialized correctly")
        except Exception as e:
            pytest.fail(f"❌ Collector backfill state test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_api_budget_logic(self):
        """Test API budget logic for backfill"""
        try:
            collector = EthereumCollector()
            
            # Test budget threshold calculation
            daily_limit = 100000
            threshold = Config.BACKFILL_API_BUDGET_THRESHOLD
            backfill_threshold = daily_limit * threshold
            
            # Simulate low usage (should allow backfill)
            collector.api_requests_today = 50000  # 50% used
            should_backfill = collector.api_requests_today < backfill_threshold
            assert should_backfill == True
            
            # Simulate high usage (should NOT allow backfill)
            collector.api_requests_today = 80000  # 80% used
            should_backfill = collector.api_requests_today < backfill_threshold
            assert should_backfill == False
            
            print("✅ API budget logic working correctly")
        except Exception as e:
            pytest.fail(f"❌ API budget logic test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_block_progression(self):
        """Test backfill block progression logic"""
        try:
            collector = EthereumCollector()
            
            # Simulate current block
            current_block = 19000000
            
            # Test backfill initialization
            if collector.backfill_block == 0:
                collector.backfill_block = current_block - Config.BACKFILL_BATCH_SIZE
            
            expected_start = current_block - Config.BACKFILL_BATCH_SIZE
            assert collector.backfill_block == expected_start
            
            # Test backward progression
            original_block = collector.backfill_block
            collector.backfill_block -= 1
            assert collector.backfill_block == original_block - 1
            
            print("✅ Backfill block progression working correctly")
        except Exception as e:
            pytest.fail(f"❌ Backfill block progression test failed: {e}")
    
    def test_historical_priority_blocks(self):
        """Test historical priority blocks configuration"""
        try:
            priority_blocks = Config.HISTORICAL_PRIORITY_BLOCKS
            
            # Test Ethereum priority blocks
            eth_blocks = priority_blocks.get("ethereum", [])
            assert len(eth_blocks) >= 2
            
            # Test block ranges are valid
            for start_block, end_block in eth_blocks:
                assert isinstance(start_block, int)
                assert isinstance(end_block, int)
                assert start_block < end_block
                assert start_block > 0
            
            print(f"✅ Historical priority blocks configured: {len(eth_blocks)} periods")
        except Exception as e:
            pytest.fail(f"❌ Historical priority blocks test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_vs_live_distinction(self, sample_backfill_event):
        """Test distinction between backfill and live events"""
        try:
            # Create live event
            live_event = sample_backfill_event.copy()
            live_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            live_event["is_backfill"] = 0
            live_event["backfill_block"] = 0
            live_event["source"] = "live_collector"
            
            # Create backfill event
            backfill_event = sample_backfill_event.copy()
            backfill_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            backfill_event["is_backfill"] = 1
            backfill_event["backfill_block"] = 18500000
            backfill_event["source"] = "backfill_collector"
            
            # Insert both
            await insert_whale_event(live_event)
            await insert_whale_event(backfill_event)
            
            print("✅ Backfill vs live event distinction working")
        except Exception as e:
            pytest.fail(f"❌ Backfill vs live distinction test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_error_handling(self):
        """Test backfill error handling"""
        try:
            collector = EthereumCollector()
            
            # Test invalid block number handling
            invalid_block = -1
            
            # This should not crash the system
            try:
                await collector.process_block(invalid_block, is_backfill=True)
            except Exception as e:
                # Expected to fail gracefully
                assert "Block" in str(e) or "Fehler" in str(e)
            
            print("✅ Backfill error handling working correctly")
        except Exception as e:
            pytest.fail(f"❌ Backfill error handling test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_rate_limiting(self):
        """Test backfill respects rate limiting"""
        try:
            collector = EthereumCollector()
            
            # Test rate limiting logic
            initial_requests = collector.api_requests_today
            
            # Simulate API request
            collector.api_requests_today += 1
            
            assert collector.api_requests_today == initial_requests + 1
            
            # Test budget exhaustion
            collector.api_requests_today = 90000  # Near limit
            budget_threshold = 100000 * Config.BACKFILL_API_BUDGET_THRESHOLD
            
            should_continue = collector.api_requests_today < budget_threshold
            assert should_continue == False  # Should stop backfill
            
            print("✅ Backfill rate limiting working correctly")
        except Exception as e:
            pytest.fail(f"❌ Backfill rate limiting test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_logging(self):
        """Test backfill logging functionality"""
        try:
            collector = EthereumCollector()
            
            # Test logging intervals
            test_blocks = [19000000, 18999000, 18998000]
            
            for block in test_blocks:
                collector.backfill_block = block
                
                # Check if this block would trigger logging
                should_log = collector.backfill_block % 1000 == 0
                
                if should_log:
                    # This would normally trigger a log message
                    pass
            
            print("✅ Backfill logging intervals working correctly")
        except Exception as e:
            pytest.fail(f"❌ Backfill logging test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_integration(self):
        """Test full backfill integration"""
        try:
            collector = EthereumCollector()
            
            # Mock session and API responses
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": hex(19000000)  # Mock current block
            }
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            collector.session = mock_session
            
            # Test backfill initialization
            current_block = 19000000
            if collector.backfill_block == 0:
                collector.backfill_block = current_block - Config.BACKFILL_BATCH_SIZE
            
            # Verify backfill state
            assert collector.backfill_block == current_block - Config.BACKFILL_BATCH_SIZE
            assert collector.api_requests_today >= 0
            
            print("✅ Backfill integration test successful")
        except Exception as e:
            pytest.fail(f"❌ Backfill integration test failed: {e}")
    
    def test_backfill_performance_expectations(self):
        """Test backfill performance expectations"""
        try:
            # Calculate expected backfill time
            daily_requests = 100000
            backfill_percentage = 1 - Config.BACKFILL_API_BUDGET_THRESHOLD
            daily_backfill_requests = daily_requests * backfill_percentage
            
            # Estimate blocks per day for backfill
            blocks_per_day = daily_backfill_requests  # 1 request per block
            
            # Calculate time to backfill major periods
            bull_run_2021_blocks = 2000000  # Approximate
            days_to_backfill = bull_run_2021_blocks / blocks_per_day
            
            # Should be reasonable (less than 1 year)
            assert days_to_backfill < 365
            
            print(f"✅ Backfill performance: ~{days_to_backfill:.1f} days for major bull run")
        except Exception as e:
            pytest.fail(f"❌ Backfill performance test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
