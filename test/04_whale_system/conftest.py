"""
Pytest configuration for Whale System Tests
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
    container_name = "clickhouse_test"
    
    # Remove existing test container if it exists
    try:
        existing = docker_client.containers.get(container_name)
        existing.stop()
        existing.remove()
    except docker.errors.NotFound:
        pass
    
    # Start ClickHouse container
    container = docker_client.containers.run(
        "clickhouse/clickhouse-server:latest",
        name=container_name,
        ports={"8123/tcp": 8123, "9000/tcp": 9000},
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
            response = requests.get("http://localhost:8123/ping", timeout=2)
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
    
    # Read and execute schema
    schema_path = backend_path / "db" / "migrations" / "20250701_create_whale_tables.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Execute schema more robustly
    # First, create tables with simpler SQL
    whale_events_sql = """
    CREATE TABLE IF NOT EXISTS whale_events (
        event_id UUID DEFAULT generateUUIDv4(),
        ts DateTime,
        chain String,
        tx_hash String,
        from_addr String,
        to_addr String,
        token String,
        symbol String,
        amount Float64,
        is_native UInt8,
        exchange String,
        amount_usd Float64 DEFAULT 0.0,
        from_exchange String DEFAULT '',
        from_country String DEFAULT '',
        from_city String DEFAULT '',
        to_exchange String DEFAULT '',
        to_country String DEFAULT '',
        to_city String DEFAULT '',
        is_cross_border UInt8 DEFAULT 0,
        source String DEFAULT 'direct_collector',
        created_at DateTime DEFAULT now(),
        threshold_usd Float64 DEFAULT 0.0,
        coin_rank UInt16 DEFAULT 0
    )
    ENGINE = ReplacingMergeTree()
    ORDER BY (ts, chain, symbol)
    PARTITION BY toYYYYMM(ts)
    """
    
    coin_config_sql = """
    CREATE TABLE IF NOT EXISTS coin_config (
        symbol String,
        chain String,
        contract_addr String,
        coingecko_id String,
        decimals UInt8,
        threshold_usd Float64,
        priority UInt8,
        active UInt8 DEFAULT 1,
        last_updated DateTime DEFAULT now()
    )
    ENGINE = ReplacingMergeTree()
    ORDER BY (symbol, chain)
    """
    
    # Execute each table creation separately using exec_run with list args
    for table_name, sql in [("whale_events", whale_events_sql), ("coin_config", coin_config_sql)]:
        # Use list args to avoid shell escaping issues
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
    os.environ["CLICKHOUSE_PORT"] = "8123"
    os.environ["CLICKHOUSE_PASSWORD"] = ""
    os.environ["CLICKHOUSE_DB"] = "bitget"
    
    # Mock API keys for testing
    os.environ["ETHEREUM_API_KEY"] = "test_ethereum_key"
    os.environ["BSC_API_KEY"] = "test_bsc_key"
    os.environ["POLYGON_API_KEY"] = "test_polygon_key"
    
    yield
    
    # Cleanup environment variables
    for key in ["CLICKHOUSE_HOST", "CLICKHOUSE_PORT", "CLICKHOUSE_PASSWORD", "CLICKHOUSE_DB",
                "ETHEREUM_API_KEY", "BSC_API_KEY", "POLYGON_API_KEY"]:
        os.environ.pop(key, None)

@pytest.fixture
def whale_client(test_environment):
    """Get whale client for testing"""
    from db.clickhouse_whales import get_whale_client
    return get_whale_client()

@pytest.fixture
def reset_whale_client():
    """Reset whale client singleton for clean tests"""
    from db import clickhouse_whales
    # Reset singleton
    clickhouse_whales._whale_client_instance = None
    clickhouse_whales._whale_connection_count = 0
    
    yield
    
    # Reset again after test
    clickhouse_whales._whale_client_instance = None
    clickhouse_whales._whale_connection_count = 0

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
            client.command("TRUNCATE TABLE bitget.whale_events")
            client.command("TRUNCATE TABLE bitget.coin_config")
        except Exception:
            pass  # Ignore cleanup errors

# Auto-use fixtures for all tests
@pytest.fixture(autouse=True)
def auto_setup(test_environment, reset_whale_client):
    """Automatically set up test environment for all tests"""
    yield
