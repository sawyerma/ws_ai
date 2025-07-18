"""
Frontend Data Tests for Whale Monitoring System
Tests data availability and formatting for frontend consumption
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from db.clickhouse_whales import (
    get_clickhouse_client,
    insert_whale_event,
    get_whale_events
)
from whales.config_whales import Config

class TestFrontendDataWhales:
    
    @pytest.fixture
    def clickhouse_client(self):
        """Get ClickHouse client for testing"""
        return get_clickhouse_client()
    
    @pytest.fixture
    def sample_whale_events(self):
        """Create sample whale events for testing"""
        events = []
        base_time = datetime.now()
        
        # Create diverse whale events
        for i in range(20):
            events.append({
                "ts": base_time - timedelta(hours=i),
                "chain": ["ethereum", "binance", "polygon"][i % 3],
                "tx_hash": f"0x{uuid.uuid4().hex}",
                "from_addr": f"0x{'1' * 40}",
                "to_addr": f"0x{'2' * 40}",
                "token": "",
                "symbol": ["ETH", "BNB", "MATIC", "BTC", "USDT"][i % 5],
                "amount": 1000.0 + i * 100,
                "is_native": 1,
                "exchange": ["Binance", "Coinbase", "Bitget", ""][i % 4],
                "amount_usd": 2500000.0 + i * 250000,
                "from_exchange": ["Binance", "Coinbase", "Bitget", ""][i % 4],
                "from_country": ["Malta", "USA", "Singapore", "Germany"][i % 4],
                "from_city": ["Valletta", "San Francisco", "Singapore", "Berlin"][i % 4],
                "to_exchange": ["Coinbase", "Binance", "Bitget", ""][i % 4],
                "to_country": ["USA", "Malta", "Singapore", "Germany"][i % 4],
                "to_city": ["San Francisco", "Valletta", "Singapore", "Berlin"][i % 4],
                "is_cross_border": 1 if i % 2 == 0 else 0,
                "source": "frontend_test",
                "threshold_usd": 1000000.0,
                "coin_rank": (i % 3) + 1
            })
        
        return events
    
    @pytest.mark.asyncio
    async def test_whale_events_basic_retrieval(self, sample_whale_events):
        """Test basic whale events retrieval for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events[:5]:
                await insert_whale_event(event)
            
            # Retrieve events
            events = await get_whale_events(limit=10)
            
            assert isinstance(events, list)
            assert len(events) >= 5
            
            # Check event structure for frontend
            if events:
                event = events[0]
                required_fields = [
                    "tx_hash", "chain", "symbol", "amount", "amount_usd",
                    "from_addr", "to_addr", "ts", "is_cross_border",
                    "from_country", "to_country", "exchange"
                ]
                
                for field in required_fields:
                    assert field in event, f"Missing field: {field}"
                
                # Check data types
                assert isinstance(event["amount_usd"], (int, float))
                assert isinstance(event["amount"], (int, float))
                assert isinstance(event["is_cross_border"], int)
                
            print("✅ Basic whale events retrieval successful")
        except Exception as e:
            pytest.fail(f"❌ Basic whale events retrieval failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_pagination(self, sample_whale_events):
        """Test pagination for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            # Test pagination
            page_size = 5
            total_pages = 4
            
            all_events = []
            for page in range(total_pages):
                offset = page * page_size
                events = await get_whale_events(limit=page_size, offset=offset)
                
                assert isinstance(events, list)
                assert len(events) <= page_size
                
                all_events.extend(events)
            
            # Check for unique events (no duplicates)
            tx_hashes = [e["tx_hash"] for e in all_events]
            assert len(tx_hashes) == len(set(tx_hashes))
            
            print(f"✅ Pagination successful - Retrieved {len(all_events)} unique events")
        except Exception as e:
            pytest.fail(f"❌ Pagination failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_filtering(self, sample_whale_events):
        """Test filtering options for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            # Test chain filtering
            eth_events = await get_whale_events(
                filters={"chain": "ethereum"},
                limit=10
            )
            for event in eth_events:
                assert event["chain"] == "ethereum"
            
            # Test symbol filtering
            btc_events = await get_whale_events(
                filters={"symbol": "BTC"},
                limit=10
            )
            for event in btc_events:
                assert event["symbol"] == "BTC"
            
            # Test cross-border filtering
            cross_border_events = await get_whale_events(
                filters={"is_cross_border": 1},
                limit=10
            )
            for event in cross_border_events:
                assert event["is_cross_border"] == 1
            
            # Test amount filtering
            high_value_events = await get_whale_events(
                filters={"min_amount_usd": 5000000.0},
                limit=10
            )
            for event in high_value_events:
                assert float(event["amount_usd"]) >= 5000000.0
            
            print("✅ Filtering options successful")
        except Exception as e:
            pytest.fail(f"❌ Filtering options failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_time_range(self, sample_whale_events):
        """Test time range filtering for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            # Test last 24 hours
            now = datetime.now()
            last_24h = await get_whale_events(
                filters={
                    "start_time": now - timedelta(hours=24),
                    "end_time": now
                },
                limit=50
            )
            
            for event in last_24h:
                event_time = datetime.fromisoformat(event["ts"].replace('Z', '+00:00'))
                assert event_time >= now - timedelta(hours=24)
            
            # Test last 7 days
            last_7d = await get_whale_events(
                filters={
                    "start_time": now - timedelta(days=7),
                    "end_time": now
                },
                limit=50
            )
            
            assert len(last_7d) >= len(last_24h)
            
            print("✅ Time range filtering successful")
        except Exception as e:
            pytest.fail(f"❌ Time range filtering failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_sorting(self, sample_whale_events):
        """Test sorting options for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            # Test sorting by amount (descending)
            events_by_amount = await get_whale_events(
                order_by="amount_usd",
                order_direction="desc",
                limit=10
            )
            
            if len(events_by_amount) > 1:
                for i in range(len(events_by_amount) - 1):
                    current_amount = float(events_by_amount[i]["amount_usd"])
                    next_amount = float(events_by_amount[i + 1]["amount_usd"])
                    assert current_amount >= next_amount
            
            # Test sorting by time (descending - most recent first)
            events_by_time = await get_whale_events(
                order_by="ts",
                order_direction="desc",
                limit=10
            )
            
            if len(events_by_time) > 1:
                for i in range(len(events_by_time) - 1):
                    current_time = datetime.fromisoformat(events_by_time[i]["ts"].replace('Z', '+00:00'))
                    next_time = datetime.fromisoformat(events_by_time[i + 1]["ts"].replace('Z', '+00:00'))
                    assert current_time >= next_time
            
            print("✅ Sorting options successful")
        except Exception as e:
            pytest.fail(f"❌ Sorting options failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_aggregation(self, sample_whale_events):
        """Test aggregation data for frontend charts"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            client = get_clickhouse_client()
            
            # Test volume by chain
            chain_volumes = client.query("""
                SELECT chain, SUM(amount_usd) as total_volume, COUNT(*) as event_count
                FROM bitget.whale_events
                WHERE source = 'frontend_test'
                GROUP BY chain
                ORDER BY total_volume DESC
            """)
            
            assert len(chain_volumes.result_rows) > 0
            for row in chain_volumes.result_rows:
                assert row[0] in ["ethereum", "binance", "polygon"]
                assert isinstance(row[1], (int, float))
                assert isinstance(row[2], int)
            
            # Test volume by symbol
            symbol_volumes = client.query("""
                SELECT symbol, SUM(amount_usd) as total_volume, COUNT(*) as event_count
                FROM bitget.whale_events
                WHERE source = 'frontend_test'
                GROUP BY symbol
                ORDER BY total_volume DESC
            """)
            
            assert len(symbol_volumes.result_rows) > 0
            
            # Test hourly volume
            hourly_volumes = client.query("""
                SELECT toHour(ts) as hour, SUM(amount_usd) as total_volume
                FROM bitget.whale_events
                WHERE source = 'frontend_test'
                GROUP BY hour
                ORDER BY hour
            """)
            
            assert len(hourly_volumes.result_rows) > 0
            
            print("✅ Aggregation data successful")
        except Exception as e:
            pytest.fail(f"❌ Aggregation data failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_country_analysis(self, sample_whale_events):
        """Test country-based analysis for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            client = get_clickhouse_client()
            
            # Test top countries by volume
            country_volumes = client.query("""
                SELECT from_country, SUM(amount_usd) as total_volume
                FROM bitget.whale_events
                WHERE source = 'frontend_test' AND from_country != 'Unknown'
                GROUP BY from_country
                ORDER BY total_volume DESC
            """)
            
            assert len(country_volumes.result_rows) > 0
            for row in country_volumes.result_rows:
                assert row[0] in ["Malta", "USA", "Singapore", "Germany"]
                assert isinstance(row[1], (int, float))
            
            # Test cross-border flows
            cross_border_flows = client.query("""
                SELECT from_country, to_country, SUM(amount_usd) as flow_volume
                FROM bitget.whale_events
                WHERE source = 'frontend_test' AND is_cross_border = 1
                GROUP BY from_country, to_country
                ORDER BY flow_volume DESC
            """)
            
            assert len(cross_border_flows.result_rows) > 0
            
            print("✅ Country analysis successful")
        except Exception as e:
            pytest.fail(f"❌ Country analysis failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_exchange_analysis(self, sample_whale_events):
        """Test exchange-based analysis for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            client = get_clickhouse_client()
            
            # Test top exchanges by volume
            exchange_volumes = client.query("""
                SELECT from_exchange, SUM(amount_usd) as total_volume
                FROM bitget.whale_events
                WHERE source = 'frontend_test' AND from_exchange != ''
                GROUP BY from_exchange
                ORDER BY total_volume DESC
            """)
            
            assert len(exchange_volumes.result_rows) > 0
            for row in exchange_volumes.result_rows:
                assert row[0] in ["Binance", "Coinbase", "Bitget"]
                assert isinstance(row[1], (int, float))
            
            # Test exchange flows
            exchange_flows = client.query("""
                SELECT from_exchange, to_exchange, SUM(amount_usd) as flow_volume
                FROM bitget.whale_events
                WHERE source = 'frontend_test' 
                AND from_exchange != '' AND to_exchange != ''
                GROUP BY from_exchange, to_exchange
                ORDER BY flow_volume DESC
            """)
            
            print("✅ Exchange analysis successful")
        except Exception as e:
            pytest.fail(f"❌ Exchange analysis failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_json_format(self, sample_whale_events):
        """Test JSON format compatibility for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events[:3]:
                await insert_whale_event(event)
            
            # Retrieve events
            events = await get_whale_events(limit=3)
            
            # Test JSON serialization
            import json
            
            for event in events:
                # Should be JSON serializable
                json_str = json.dumps(event, default=str)
                assert isinstance(json_str, str)
                
                # Should be JSON deserializable
                parsed_event = json.loads(json_str)
                assert isinstance(parsed_event, dict)
                
                # Check required fields are present
                required_fields = [
                    "tx_hash", "chain", "symbol", "amount_usd", "ts"
                ]
                for field in required_fields:
                    assert field in parsed_event
            
            print("✅ JSON format compatibility successful")
        except Exception as e:
            pytest.fail(f"❌ JSON format compatibility failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_performance(self, sample_whale_events):
        """Test query performance for frontend"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            import time
            
            # Test query performance
            start_time = time.time()
            events = await get_whale_events(limit=20)
            end_time = time.time()
            
            query_time = end_time - start_time
            assert query_time < 2.0  # Should be under 2 seconds
            
            # Test filtered query performance
            start_time = time.time()
            filtered_events = await get_whale_events(
                filters={"chain": "ethereum", "min_amount_usd": 1000000.0},
                limit=10
            )
            end_time = time.time()
            
            filtered_query_time = end_time - start_time
            assert filtered_query_time < 3.0  # Should be under 3 seconds
            
            print(f"✅ Query performance successful - Basic: {query_time:.3f}s, Filtered: {filtered_query_time:.3f}s")
        except Exception as e:
            pytest.fail(f"❌ Query performance failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_real_time_updates(self, sample_whale_events):
        """Test real-time update capabilities for frontend"""
        try:
            # Insert initial events
            for event in sample_whale_events[:5]:
                await insert_whale_event(event)
            
            # Get initial count
            initial_events = await get_whale_events(limit=100)
            initial_count = len(initial_events)
            
            # Insert new event
            new_event = sample_whale_events[0].copy()
            new_event["tx_hash"] = f"0x{uuid.uuid4().hex}"
            new_event["ts"] = datetime.now()
            new_event["source"] = "real_time_test"
            
            await insert_whale_event(new_event)
            
            # Get updated count
            updated_events = await get_whale_events(limit=100)
            updated_count = len(updated_events)
            
            # Should have one more event
            assert updated_count > initial_count
            
            # Find the new event
            new_events = [e for e in updated_events if e["source"] == "real_time_test"]
            assert len(new_events) >= 1
            
            print("✅ Real-time updates successful")
        except Exception as e:
            pytest.fail(f"❌ Real-time updates failed: {e}")
    
    @pytest.mark.asyncio
    async def test_whale_events_statistics(self, sample_whale_events):
        """Test statistics calculation for frontend dashboard"""
        try:
            # Insert test events
            for event in sample_whale_events:
                await insert_whale_event(event)
            
            client = get_clickhouse_client()
            
            # Test basic statistics
            stats = client.query("""
                SELECT 
                    COUNT(*) as total_events,
                    SUM(amount_usd) as total_volume,
                    AVG(amount_usd) as avg_volume,
                    MAX(amount_usd) as max_volume,
                    MIN(amount_usd) as min_volume
                FROM bitget.whale_events
                WHERE source = 'frontend_test'
            """)
            
            assert len(stats.result_rows) == 1
            row = stats.result_rows[0]
            
            assert row[0] > 0  # total_events
            assert row[1] > 0  # total_volume
            assert row[2] > 0  # avg_volume
            assert row[3] > 0  # max_volume
            assert row[4] > 0  # min_volume
            
            # Test time-based statistics
            time_stats = client.query("""
                SELECT 
                    toDate(ts) as date,
                    COUNT(*) as daily_events,
                    SUM(amount_usd) as daily_volume
                FROM bitget.whale_events
                WHERE source = 'frontend_test'
                GROUP BY date
                ORDER BY date DESC
            """)
            
            assert len(time_stats.result_rows) > 0
            
            print("✅ Statistics calculation successful")
        except Exception as e:
            pytest.fail(f"❌ Statistics calculation failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
