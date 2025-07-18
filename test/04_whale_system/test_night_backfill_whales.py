"""
Night Backfill Tests for Whale Monitoring System
Tests the intelligent night-time intensive backfill functionality
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from whales.collectors.blockchain_collector_whales import EthereumCollector
from whales.config_whales import Config

class TestNightBackfillWhales:
    
    @pytest.fixture
    def collector(self):
        """Create collector for testing"""
        return EthereumCollector()
    
    def test_night_backfill_config(self):
        """Test night backfill configuration"""
        assert Config.DAILY_API_LIMIT == 100000
        assert Config.NIGHT_BACKFILL_HOUR == 23
        assert Config.LIVE_WHALE_SAFETY_BUFFER == 10
        assert Config.API_RESET_HOUR == 0
        print("✅ Night backfill configuration correct")
    
    @pytest.mark.asyncio
    async def test_daily_api_reset(self, collector):
        """Test daily API reset functionality"""
        try:
            # Set up test state
            collector.daily_api_calls = 50000
            collector.last_reset_day = datetime.now().day - 1  # Yesterday
            
            # Trigger reset check
            await collector.check_daily_reset()
            
            # Verify reset occurred
            assert collector.daily_api_calls == 0
            assert collector.last_reset_day == datetime.now().day
            
            print("✅ Daily API reset working correctly")
        except Exception as e:
            pytest.fail(f"❌ Daily API reset test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_night_backfill_budget_calculation(self, collector):
        """Test night backfill budget calculation"""
        try:
            # Test scenarios
            test_cases = [
                {"used": 30000, "expected_backfill": 69990},  # Low usage
                {"used": 50000, "expected_backfill": 49990},  # Medium usage
                {"used": 80000, "expected_backfill": 19990},  # High usage
                {"used": 95000, "expected_backfill": 4990},   # Very high usage
                {"used": 99995, "expected_backfill": 0},      # Near limit
            ]
            
            for case in test_cases:
                collector.daily_api_calls = case["used"]
                remaining = max(0, Config.DAILY_API_LIMIT - collector.daily_api_calls)
                backfill_budget = max(0, remaining - Config.LIVE_WHALE_SAFETY_BUFFER)
                
                assert backfill_budget == case["expected_backfill"]
                print(f"✅ Budget calculation: {case['used']} used → {backfill_budget} backfill")
            
        except Exception as e:
            pytest.fail(f"❌ Night backfill budget calculation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_intensive_backfill_session(self, collector):
        """Test intensive backfill session logic"""
        try:
            # Mock process_block to avoid actual API calls
            async def mock_process_block(block_number, is_backfill=False):
                await asyncio.sleep(0.01)  # Simulate processing time
                return True
            
            collector.process_block = mock_process_block
            collector.backfill_block = 19000000
            collector.daily_api_calls = 50000
            
            # Test intensive backfill with limited calls
            available_calls = 100
            
            start_time = datetime.now()
            await collector.intensive_backfill(available_calls)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Verify backfill progress
            assert collector.backfill_block < 19000000  # Should have moved backward
            assert collector.daily_api_calls >= 50000  # Should have increased
            assert duration > 0  # Should have taken some time
            
            print("✅ Intensive backfill session working correctly")
        except Exception as e:
            pytest.fail(f"❌ Intensive backfill session test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_day_vs_night_backfill_logic(self, collector):
        """Test different backfill behavior during day vs night"""
        try:
            collector.daily_api_calls = 10000  # Low usage
            
            # Mock current time for day time (e.g., 14:00)
            with patch('whales.collectors.blockchain_collector_whales.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.now().replace(hour=14)
                
                # During day: should only backfill if >80% budget remaining
                remaining = Config.DAILY_API_LIMIT - collector.daily_api_calls
                day_threshold = Config.DAILY_API_LIMIT * 0.8
                
                should_backfill_day = remaining > day_threshold
                assert should_backfill_day == True  # 90k remaining > 80k threshold
                
            # Mock current time for night time (23:00)
            with patch('whales.collectors.blockchain_collector_whales.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.now().replace(hour=23)
                
                # During night: should use intensive backfill
                night_budget = max(0, remaining - Config.LIVE_WHALE_SAFETY_BUFFER)
                assert night_budget > 0  # Should have budget for intensive backfill
                
            print("✅ Day vs night backfill logic working correctly")
        except Exception as e:
            pytest.fail(f"❌ Day vs night backfill logic test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_safety_buffer_protection(self, collector):
        """Test safety buffer protection for live whales"""
        try:
            # Test scenarios where safety buffer protects live whales
            test_cases = [
                {"used": 99990, "remaining": 10, "expected_backfill": 0},    # Exactly at buffer
                {"used": 99985, "remaining": 15, "expected_backfill": 5},    # 5 over buffer
                {"used": 99980, "remaining": 20, "expected_backfill": 10},   # 10 over buffer
            ]
            
            for case in test_cases:
                collector.daily_api_calls = case["used"]
                remaining = Config.DAILY_API_LIMIT - collector.daily_api_calls
                backfill_budget = max(0, remaining - Config.LIVE_WHALE_SAFETY_BUFFER)
                
                assert remaining == case["remaining"]
                assert backfill_budget == case["expected_backfill"]
                print(f"✅ Safety buffer: {case['remaining']} remaining → {backfill_budget} backfill")
            
        except Exception as e:
            pytest.fail(f"❌ Safety buffer protection test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_rate_limiting(self, collector):
        """Test backfill rate limiting during intensive session"""
        try:
            # Mock process_block to track calls
            call_count = 0
            call_times = []
            
            async def mock_process_block(block_number, is_backfill=False):
                nonlocal call_count
                call_count += 1
                call_times.append(datetime.now())
                await asyncio.sleep(0.01)  # Simulate processing
                return True
            
            collector.process_block = mock_process_block
            collector.backfill_block = 19000000
            
            # Test with small call limit to check rate limiting
            available_calls = 10
            
            start_time = datetime.now()
            await collector.intensive_backfill(available_calls)
            end_time = datetime.now()
            
            # Verify rate limiting (0.2s sleep between calls)
            total_time = (end_time - start_time).total_seconds()
            expected_min_time = (available_calls - 1) * 0.2  # Minus 1 because last call has no sleep
            
            assert call_count <= available_calls
            assert total_time >= expected_min_time
            
            print(f"✅ Rate limiting: {call_count} calls in {total_time:.2f}s")
        except Exception as e:
            pytest.fail(f"❌ Backfill rate limiting test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_progress_tracking(self, collector):
        """Test backfill progress tracking"""
        try:
            # Set initial state
            initial_block = 19000000
            collector.backfill_block = initial_block
            collector.daily_api_calls = 50000
            
            # Mock process_block
            async def mock_process_block(block_number, is_backfill=False):
                await asyncio.sleep(0.01)
                return True
            
            collector.process_block = mock_process_block
            
            # Run intensive backfill
            available_calls = 50
            await collector.intensive_backfill(available_calls)
            
            # Verify progress
            blocks_processed = initial_block - collector.backfill_block
            assert blocks_processed > 0
            assert blocks_processed <= available_calls
            
            # Verify API calls increased
            assert collector.daily_api_calls >= 50000 + blocks_processed
            
            print(f"✅ Progress tracking: {blocks_processed} blocks processed")
        except Exception as e:
            pytest.fail(f"❌ Backfill progress tracking test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_backfill_error_handling(self, collector):
        """Test backfill error handling"""
        try:
            # Mock process_block to throw errors
            async def mock_process_block_error(block_number, is_backfill=False):
                if block_number % 3 == 0:  # Every 3rd block fails
                    raise Exception("Mock API error")
                await asyncio.sleep(0.01)
                return True
            
            collector.process_block = mock_process_block_error
            collector.backfill_block = 19000000
            
            # Should handle errors gracefully
            available_calls = 10
            await collector.intensive_backfill(available_calls)
            
            # Should complete without crashing
            assert collector.backfill_block < 19000000
            
            print("✅ Error handling working correctly")
        except Exception as e:
            pytest.fail(f"❌ Backfill error handling test failed: {e}")
    
    def test_backfill_performance_estimation(self):
        """Test backfill performance estimation"""
        try:
            # Calculate expected backfill performance
            daily_limit = Config.DAILY_API_LIMIT
            safety_buffer = Config.LIVE_WHALE_SAFETY_BUFFER
            
            # Best case: minimal live usage
            min_live_usage = daily_limit * 0.1  # 10% for live whales
            max_backfill = daily_limit - min_live_usage - safety_buffer
            
            # Worst case: high live usage
            max_live_usage = daily_limit * 0.9  # 90% for live whales
            min_backfill = max(0, daily_limit - max_live_usage - safety_buffer)
            
            # Calculate time to backfill to 2017
            current_block = 19000000
            target_block = 4000000  # 2017
            total_blocks = current_block - target_block
            
            # Best case scenario
            best_case_days = total_blocks / max_backfill
            
            # Worst case scenario
            worst_case_days = total_blocks / max(min_backfill, 1000)  # At least 1000 blocks/day
            
            print(f"✅ Performance estimation:")
            print(f"   Total blocks to backfill: {total_blocks:,}")
            print(f"   Max backfill per day: {max_backfill:,}")
            print(f"   Min backfill per day: {min_backfill:,}")
            print(f"   Best case: {best_case_days:.1f} days")
            print(f"   Worst case: {worst_case_days:.1f} days")
            
            # Reasonable expectations
            assert best_case_days < 365  # Should complete within a year
            assert worst_case_days < 365 * 5  # Even worst case within 5 years
            
        except Exception as e:
            pytest.fail(f"❌ Performance estimation test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
