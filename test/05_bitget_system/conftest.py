"""
Pytest configuration for Bitget System Tests
Automatically sets up and tears down test infrastructure
"""
import pytest
import docker
import time
import os
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

@pytest.fixture(scope="session")
def docker_client():
    """Get Docker client for managing containers"""
    return docker.from_env()

@pytest.fixture(scope="session") 
def clickhouse_container(docker_client):
    """
    Start ClickHouse container for testing
    Automatically sets up database and tables
    """
    container_name = "clickhouse_bitget_test"
    
    # Remove existing test container if it exists
    try:
        existing = docker_client.containers.get(container_name)
        existing.stop()
        existing.remove()
    except docker.errors.NotFound:
        pass
    
    # Start ClickHouse container
    container = docker_client.containers.run(
        "clickhouse/clickhouse-server:23.8",
        name=container_name,
        ports={"8123/tcp": 8125, "9000/tcp": 9002},
        detach=True,
        environment={
            "CLICKHOUSE_DB": "bitget",
            "CLICKHOUSE_USER": "default",
            "CLICKHOUSE_PASSWORD": "",
            "CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT": "1"
        },
        remove=True
    )
    
    # Wait for ClickHouse to be ready
    print("🔄 Waiting for ClickHouse to start...")
    
    # Phase 1: Wait for CLI interface
    max_retries = 30
    for i in range(max_retries):
        try:
            result = container.exec_run("clickhouse-client --query 'SELECT 1'")
            if result.exit_code == 0:
                print("✅ ClickHouse CLI interface ready")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        container.stop()
        pytest.fail("ClickHouse CLI failed to start within 30 seconds")
    
    # Phase 2: Wait for HTTP interface
    print("🔄 Waiting for HTTP interface...")
    import requests
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8125/ping", timeout=2)
            if response.status_code == 200:
                print("✅ ClickHouse HTTP interface ready")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        container.stop()
        pytest.fail("ClickHouse HTTP interface failed to start within 30 seconds")
    
    # Phase 3: Additional stability wait
    print("🔄 Waiting for stability...")
    time.sleep(3)
    
    # Create database and tables
    print("🔄 Setting up database schema...")
    
    # Create database
    container.exec_run("clickhouse-client --query 'CREATE DATABASE IF NOT EXISTS bitget'")
    
    # Create Bitget tables
    coin_settings_sql = """
    CREATE TABLE IF NOT EXISTS bitget.coin_settings (
        symbol           LowCardinality(String),
        market           LowCardinality(String),
        store_live       UInt8 DEFAULT 1,
        load_history     UInt8 DEFAULT 1,
        history_until    Nullable(DateTime64(3, 'UTC')),
        favorite         UInt8 DEFAULT 0,
        db_resolutions   Array(UInt16) DEFAULT [60, 300, 900],
        chart_resolution UInt16 DEFAULT 60,
        updated_at       DateTime64(3, 'UTC') DEFAULT now64(3),
        _version UInt64 DEFAULT toUnixTimestamp64Nano(now64(9))
    )
    ENGINE = ReplacingMergeTree(_version)
    ORDER BY (symbol, market)
    PRIMARY KEY (symbol, market)
    SETTINGS index_granularity = 128
    """
    
    trades_sql = """
    CREATE TABLE IF NOT EXISTS bitget.trades (
        trade_id String,
        symbol   LowCardinality(String),
        market   LowCardinality(String),
        price    Float64 CODEC(Gorilla, LZ4),
        size     Float32 CODEC(Gorilla, LZ4),
        side     Enum8('buy' = 1, 'sell' = 2),
        ts       DateTime64(3, 'UTC') CODEC(Delta, LZ4),
        _shard_key UInt32 DEFAULT cityHash64(trade_id)
    )
    ENGINE = ReplacingMergeTree()
    ORDER BY (symbol, market, toStartOfMinute(ts), trade_id)
    PARTITION BY toYYYYMM(ts)
    TTL toDateTime(ts) + INTERVAL 6 MONTH
    SETTINGS index_granularity = 1024, min_bytes_for_wide_part = 10000000
    """
    
    bars_sql = """
    CREATE TABLE IF NOT EXISTS bitget.bars (
        symbol     LowCardinality(String) CODEC(ZSTD(1)),
        market     LowCardinality(String) CODEC(ZSTD(1)),
        resolution UInt16 CODEC(T64, LZ4),
        open       Float32 CODEC(Gorilla, ZSTD(1)),
        high       Float32 CODEC(Gorilla, ZSTD(1)),
        low        Float32 CODEC(Gorilla, ZSTD(1)),
        close      Float32 CODEC(Gorilla, ZSTD(1)),
        volume     Float64 CODEC(DoubleDelta, ZSTD(1)),
        trades     UInt32 CODEC(Delta, ZSTD(1)),
        ts         DateTime64(3, 'UTC') CODEC(Delta, LZ4),
        _resolution_minutes UInt16 MATERIALIZED resolution / 60
    )
    ENGINE = ReplacingMergeTree()
    ORDER BY (symbol, market, resolution, ts)
    PARTITION BY (symbol, toYYYYMM(ts))
    TTL toDateTime(ts) + INTERVAL 2 YEAR
    SETTINGS index_granularity = 256, allow_nullable_key = 1
    """
    
    # Execute each table creation separately
    for table_name, sql in [("coin_settings", coin_settings_sql), ("trades", trades_sql), ("bars", bars_sql)]:
        result = container.exec_run([
            "clickhouse-client", 
            "--database", "bitget", 
            "--query", sql
        ])
        if result.exit_code == 0:
            print(f"✅ Created table: {table_name}")
        else:
            print(f"⚠️  Warning: Failed to create table {table_name}: {result.output.decode()}")
    
    print("✅ ClickHouse test environment ready")
    
    yield container
    
    # Cleanup
    print("🔄 Cleaning up ClickHouse container...")
    container.stop()

@pytest.fixture(scope="session")
def test_environment(clickhouse_container):
    """
    Set up complete test environment
    Sets environment variables for testing
    """
    # Set test environment variables
    os.environ["CLICKHOUSE_HOST"] = "localhost"
    os.environ["CLICKHOUSE_PORT"] = "8125"
    os.environ["CLICKHOUSE_PASSWORD"] = ""
    os.environ["CLICKHOUSE_DB"] = "bitget"
    
    # Mock API keys for testing
    os.environ["BITGET_API_KEY"] = "test_api_key"
    os.environ["BITGET_SECRET_KEY"] = "test_secret_key"
    os.environ["BITGET_PASSPHRASE"] = "test_passphrase"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6380"
    
    yield
    
    # Cleanup environment variables
    for key in ["CLICKHOUSE_HOST", "CLICKHOUSE_PORT", "CLICKHOUSE_PASSWORD", "CLICKHOUSE_DB",
                "BITGET_API_KEY", "BITGET_SECRET_KEY", "BITGET_PASSPHRASE", "REDIS_HOST", "REDIS_PORT"]:
        os.environ.pop(key, None)

@pytest.fixture
def bitget_client(test_environment):
    """Get Bitget client for testing"""
    from market.bitget.services.bitget_rest import BitgetRestAPI
    return BitgetRestAPI()

@pytest.fixture
def reset_bitget_client():
    """Reset Bitget client singleton for clean tests"""
    # Reset any singletons if they exist
    yield

class TestInfrastructure:
    """Base class for infrastructure management in tests"""
    
    @staticmethod
    def wait_for_service(host, port, timeout=30):
        """Wait for a service to be available"""
        import socket
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False
    
    @staticmethod
    def cleanup_test_data(client):
        """Clean up test data from database"""
        try:
            client.command("TRUNCATE TABLE bitget.coin_settings")
            client.command("TRUNCATE TABLE bitget.trades")
            client.command("TRUNCATE TABLE bitget.bars")
        except Exception:
            pass  # Ignore cleanup errors

# Auto-use fixtures for all tests
@pytest.fixture(autouse=True)
def auto_setup(test_environment, reset_bitget_client):
    """Automatically set up test environment for all tests"""
    yield
