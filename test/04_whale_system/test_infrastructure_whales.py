"""
Infrastructure Tests for Whale Monitoring System
Tests ClickHouse connection, table existence, and schema validation
"""
import pytest
import asyncio
import os
from whales.config_whales import Config

class TestInfrastructure:
    
    def test_clickhouse_connection(self, whale_client):
        """Test ClickHouse database connection"""
        try:
            result = whale_client.query("SELECT 1")
            assert result.result_rows[0][0] == 1
            print("✅ ClickHouse connection successful")
        except Exception as e:
            pytest.fail(f"❌ ClickHouse connection failed: {e}")
    
    def test_whale_events_table_exists(self, whale_client):
        """Test whale_events table exists"""
        try:
            result = whale_client.query("SHOW TABLES FROM bitget LIKE 'whale_events'")
            assert len(result.result_rows) == 1
            assert result.result_rows[0][0] == 'whale_events'
            print("✅ whale_events table exists")
        except Exception as e:
            pytest.fail(f"❌ whale_events table check failed: {e}")
    
    def test_coin_config_table_exists(self, whale_client):
        """Test coin_config table exists"""
        try:
            result = whale_client.query("SHOW TABLES FROM bitget LIKE 'coin_config'")
            assert len(result.result_rows) == 1
            assert result.result_rows[0][0] == 'coin_config'
            print("✅ coin_config table exists")
        except Exception as e:
            pytest.fail(f"❌ coin_config table check failed: {e}")
    
    def test_whale_events_schema(self, whale_client):
        """Test whale_events table schema"""
        try:
            result = whale_client.query("DESCRIBE bitget.whale_events")
            columns = [row[0] for row in result.result_rows]
            
            required_columns = [
                'event_id', 'ts', 'chain', 'tx_hash', 'from_addr', 'to_addr',
                'token', 'symbol', 'amount', 'is_native', 'exchange', 'amount_usd',
                'from_exchange', 'from_country', 'from_city', 'to_exchange',
                'to_country', 'to_city', 'is_cross_border', 'source', 'created_at',
                'threshold_usd', 'coin_rank'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            assert len(missing_columns) == 0, f"Missing columns: {missing_columns}"
            assert len(columns) == 23, f"Expected 23 columns, got {len(columns)}"
            print("✅ whale_events schema validation passed")
        except Exception as e:
            pytest.fail(f"❌ whale_events schema validation failed: {e}")
    
    def test_coin_config_schema(self, whale_client):
        """Test coin_config table schema"""
        try:
            result = whale_client.query("DESCRIBE bitget.coin_config")
            columns = [row[0] for row in result.result_rows]
            
            required_columns = [
                'symbol', 'chain', 'contract_addr', 'coingecko_id', 'decimals',
                'threshold_usd', 'priority', 'active', 'last_updated'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            assert len(missing_columns) == 0, f"Missing columns: {missing_columns}"
            assert len(columns) == 9, f"Expected 9 columns, got {len(columns)}"
            print("✅ coin_config schema validation passed")
        except Exception as e:
            pytest.fail(f"❌ coin_config schema validation failed: {e}")
    
    def test_whale_events_partitioning(self, whale_client):
        """Test whale_events table partitioning"""
        try:
            result = whale_client.query("""
                SELECT partition_id, name, engine 
                FROM system.parts 
                WHERE database = 'bitget' AND table = 'whale_events'
                LIMIT 1
            """)
            # Should be empty initially, but engine should be ReplacingMergeTree
            result2 = whale_client.query("""
                SELECT engine_full 
                FROM system.tables 
                WHERE database = 'bitget' AND name = 'whale_events'
            """)
            assert len(result2.result_rows) == 1
            engine = result2.result_rows[0][0]
            assert 'ReplacingMergeTree' in engine
            print("✅ whale_events partitioning configuration correct")
        except Exception as e:
            pytest.fail(f"❌ whale_events partitioning check failed: {e}")
    
    def test_config_values(self):
        """Test configuration values"""
        try:
            # Test basic config values
            assert Config.CLICKHOUSE_HOST is not None
            assert Config.CLICKHOUSE_PORT == 8123
            assert isinstance(Config.COIN_CONFIG, dict)
            assert len(Config.COIN_CONFIG) >= 12  # Should have at least 12 coins
            assert isinstance(Config.CHAIN_CONFIG, dict)
            assert len(Config.CHAIN_CONFIG) == 3  # ethereum, binance, polygon
            
            # Test coin config structure
            for symbol, config in Config.COIN_CONFIG.items():
                assert 'threshold_usd' in config
                assert 'coingecko_id' in config
                assert 'priority' in config
                assert isinstance(config['threshold_usd'], (int, float))
                assert isinstance(config['priority'], int)
            
            print("✅ Configuration values validation passed")
        except Exception as e:
            pytest.fail(f"❌ Configuration validation failed: {e}")
    
    def test_environment_variables(self):
        """Test required environment variables"""
        try:
            # Check if at least one API key is set
            api_keys = [
                Config.ETHEREUM_API_KEY,
                Config.BSC_API_KEY,
                Config.POLYGON_API_KEY
            ]
            assert any(key for key in api_keys if key), "At least one API key must be set"
            
            # Check ClickHouse settings
            assert Config.CLICKHOUSE_HOST
            assert Config.CLICKHOUSE_PORT
            
            print("✅ Environment variables validation passed")
        except Exception as e:
            pytest.fail(f"❌ Environment variables validation failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
