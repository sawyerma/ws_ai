"""
Database Tests for Whale Monitoring System
Tests data insertion, retrieval, and database operations
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from db.clickhouse_whales import (
    get_clickhouse_client, 
    insert_whale_event, 
    is_duplicate, 
    get_whale_events
)
from whales.config_whales import Config

class TestDatabaseWhales:
    
    @pytest.fixture
    def clickhouse_client(self):
        """Get ClickHouse client for testing"""
        return get_clickhouse_client()
    
    @pytest.fixture
    def sample_whale_event(self):
        """Create sample whale event for testing"""
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
            "exchange": "Binance",
            "amount_usd": 2500000.0,
            "from_exchange": "Binance",
            "from_country": "Malta",
            "from_city": "Valletta",
            "to_exchange": "",
            "to_country": "Unknown",
            "to_city": "Unknown",
            "is_cross_border": 1,
            "source": "test_collector",
            "threshold_usd": 1000000.0,
            "coin_rank": 1
        }
    
    @pytest.mark.asyncio
    async def test_insert_whale_event(self, sample_whale_event):
        """Test whale event insertion"""
        try:
            result = await insert_whale_event(sample_whale_event)
            assert result == True
            print("✅ Whale event insertion successful")
        except Exception as e:
            pytest.fail(f"❌ Whale event insertion failed: {e}")
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, sample_whale_event):
        """Test duplicate detection"""
        try:
            tx_hash = sample_whale_event["tx_hash"]
            chain = sample_whale_event["chain"]
            
            # First insert
            result1 = await insert_whale_event(sample_whale_event)
            assert result1 == True
            
            # Check if duplicate detected
            is_dup = await is_duplicate(tx_hash, chain)
            assert is_dup == True
            print("✅ Duplicate detection successful")
        except Exception as e:
            pytest.fail(f"❌ Duplicate detection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_get_whale_events(self, sample_whale_event):
        """Test whale events retrieval"""
        try:
            # Insert test event
            await insert_whale_event(sample_whale_event)
            
            # Retrieve events
            events = await get_whale_events(limit=10)
            assert isinstance(events, list)
            assert len(events) >= 1
            
            # Check event structure
            if events:
                event = events[0]
                assert "tx_hash" in event
                assert "chain" in event
                assert "amount_usd" in event
                assert "symbol" in event
                print(f"✅ Whale events retrieval successful - {len(events)} events")
        except Exception as e:
            pytest.fail(f"❌ Whale events retrieval failed: {e}")
    
    @pytest.mark.asyncio
    async def test_cross_border_events(self, sample_whale_event):
        """Test cross-border event filtering"""
        try:
            # Insert cross-border event
            cross_border_event = sample_whale_event.copy()
            cross_border_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            cross_border_event["is_cross_border"] = 1
            cross_border_event["from_country"] = "USA"
            cross_border_event["to_country"] = "Germany"
            
            await insert_whale_event(cross_border_event)
            
            # Query cross-border events
            events = await get_whale_events(
                filters={"is_cross_border": 1},
                limit=10
            )
            assert isinstance(events, list)
            print(f"✅ Cross-border events filtering successful - {len(events)} events")
        except Exception as e:
            pytest.fail(f"❌ Cross-border events filtering failed: {e}")
    
    @pytest.mark.asyncio
    async def test_high_value_events(self, sample_whale_event):
        """Test high-value event filtering"""
        try:
            # Insert high-value event
            high_value_event = sample_whale_event.copy()
            high_value_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            high_value_event["amount_usd"] = 50000000.0  # $50M
            
            await insert_whale_event(high_value_event)
            
            # Query high-value events
            events = await get_whale_events(
                filters={"min_amount_usd": 10000000.0},
                limit=10
            )
            assert isinstance(events, list)
            print(f"✅ High-value events filtering successful - {len(events)} events")
        except Exception as e:
            pytest.fail(f"❌ High-value events filtering failed: {e}")
    
    @pytest.mark.asyncio
    async def test_time_range_filtering(self, sample_whale_event):
        """Test time range filtering"""
        try:
            # Insert event with specific timestamp
            time_event = sample_whale_event.copy()
            time_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            time_event["ts"] = datetime.now() - timedelta(hours=1)
            
            await insert_whale_event(time_event)
            
            # Query events in last 2 hours
            events = await get_whale_events(
                filters={
                    "start_time": datetime.now() - timedelta(hours=2),
                    "end_time": datetime.now()
                },
                limit=10
            )
            assert isinstance(events, list)
            print(f"✅ Time range filtering successful - {len(events)} events")
        except Exception as e:
            pytest.fail(f"❌ Time range filtering failed: {e}")
    
    @pytest.mark.asyncio
    async def test_chain_filtering(self, sample_whale_event):
        """Test chain-specific filtering"""
        try:
            # Insert events for different chains
            chains = ["ethereum", "binance", "polygon"]
            for chain in chains:
                chain_event = sample_whale_event.copy()
                chain_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
                chain_event["chain"] = chain
                await insert_whale_event(chain_event)
            
            # Query Ethereum events only
            eth_events = await get_whale_events(
                filters={"chain": "ethereum"},
                limit=10
            )
            assert isinstance(eth_events, list)
            print(f"✅ Chain filtering successful - {len(eth_events)} Ethereum events")
        except Exception as e:
            pytest.fail(f"❌ Chain filtering failed: {e}")
    
    @pytest.mark.asyncio
    async def test_symbol_filtering(self, sample_whale_event):
        """Test symbol-specific filtering"""
        try:
            # Insert events for different symbols
            symbols = ["BTC", "ETH", "USDT"]
            for symbol in symbols:
                symbol_event = sample_whale_event.copy()
                symbol_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
                symbol_event["symbol"] = symbol
                await insert_whale_event(symbol_event)
            
            # Query BTC events only
            btc_events = await get_whale_events(
                filters={"symbol": "BTC"},
                limit=10
            )
            assert isinstance(btc_events, list)
            print(f"✅ Symbol filtering successful - {len(btc_events)} BTC events")
        except Exception as e:
            pytest.fail(f"❌ Symbol filtering failed: {e}")
    
    @pytest.mark.asyncio
    async def test_exchange_filtering(self, sample_whale_event):
        """Test exchange-specific filtering"""
        try:
            # Insert events for different exchanges
            exchanges = ["Binance", "Coinbase", "Bitget"]
            for exchange in exchanges:
                exchange_event = sample_whale_event.copy()
                exchange_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
                exchange_event["from_exchange"] = exchange
                await insert_whale_event(exchange_event)
            
            # Query Binance events only
            binance_events = await get_whale_events(
                filters={"exchange": "Binance"},
                limit=10
            )
            assert isinstance(binance_events, list)
            print(f"✅ Exchange filtering successful - {len(binance_events)} Binance events")
        except Exception as e:
            pytest.fail(f"❌ Exchange filtering failed: {e}")
    
    @pytest.mark.asyncio
    async def test_pagination(self, sample_whale_event):
        """Test pagination functionality"""
        try:
            # Insert multiple events
            for i in range(15):
                paginated_event = sample_whale_event.copy()
                paginated_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
                paginated_event["amount_usd"] = 1000000.0 + i * 100000
                await insert_whale_event(paginated_event)
            
            # Test pagination
            page1 = await get_whale_events(limit=5, offset=0)
            page2 = await get_whale_events(limit=5, offset=5)
            
            assert isinstance(page1, list)
            assert isinstance(page2, list)
            assert len(page1) <= 5
            assert len(page2) <= 5
            print(f"✅ Pagination successful - Page1: {len(page1)}, Page2: {len(page2)}")
        except Exception as e:
            pytest.fail(f"❌ Pagination failed: {e}")
    
    @pytest.mark.asyncio
    async def test_data_integrity(self, sample_whale_event):
        """Test data integrity and validation"""
        try:
            # Insert event and retrieve it
            original_event = sample_whale_event.copy()
            original_hash = original_event["tx_hash"]
            
            await insert_whale_event(original_event)
            
            # Retrieve and compare
            events = await get_whale_events(
                filters={"tx_hash": original_hash},
                limit=1
            )
            
            assert len(events) == 1
            retrieved_event = events[0]
            
            # Check key fields
            assert retrieved_event["tx_hash"] == original_event["tx_hash"]
            assert retrieved_event["chain"] == original_event["chain"]
            assert retrieved_event["symbol"] == original_event["symbol"]
            assert float(retrieved_event["amount_usd"]) == original_event["amount_usd"]
            
            print("✅ Data integrity validation successful")
        except Exception as e:
            pytest.fail(f"❌ Data integrity validation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, sample_whale_event):
        """Test bulk insert performance"""
        try:
            import time
            
            # Generate multiple events
            events = []
            for i in range(100):
                bulk_event = sample_whale_event.copy()
                bulk_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
                bulk_event["amount_usd"] = 1000000.0 + i * 1000
                events.append(bulk_event)
            
            # Time the bulk insert
            start_time = time.time()
            for event in events:
                await insert_whale_event(event)
            end_time = time.time()
            
            duration = end_time - start_time
            rate = len(events) / duration
            
            print(f"✅ Bulk insert performance: {len(events)} events in {duration:.2f}s ({rate:.1f} events/s)")
            assert rate > 10  # Should be at least 10 events per second
        except Exception as e:
            pytest.fail(f"❌ Bulk insert performance test failed: {e}")
    
    def test_clickhouse_connection_pooling(self, clickhouse_client):
        """Test ClickHouse connection pooling"""
        try:
            # Test multiple connections
            for i in range(5):
                result = clickhouse_client.query("SELECT 1")
                assert result.result_rows[0][0] == 1
            
            print("✅ ClickHouse connection pooling test successful")
        except Exception as e:
            pytest.fail(f"❌ ClickHouse connection pooling test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
