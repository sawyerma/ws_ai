#!/usr/bin/env python3
"""
DarkMa Trading System - ClickHouse Connection Tests
=================================================

Tests für ClickHouse Verbindung, Performance und Datenintegrität.
"""

import os
import sys
import time
import asyncio
import requests
from typing import Dict, List, Optional
import clickhouse_connect

# Test Configuration
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8124"))  # FIXED: Docker port 8124
CLICKHOUSE_HTTP_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8124"))  # FIXED: Docker port 8124
CLICKHOUSE_NATIVE_PORT = int(os.getenv("CLICKHOUSE_NATIVE_PORT", "9100"))  # FIXED: Docker port 9100
CONNECTION_TIMEOUT = 10  # seconds
QUERY_TIMEOUT = 30  # seconds
PERFORMANCE_THRESHOLD = 100  # milliseconds

class ClickHouseTest:
    """ClickHouse Connection Test Suite"""
    
    def __init__(self):
        self.client = None
        self.test_results = {}
        
    def run_all_tests(self) -> bool:
        """Run all ClickHouse tests"""
        print("🗄️ ClickHouse Connection Test Suite")
        print("=" * 50)
        
        tests = [
            ("HTTP Interface Check", self.test_http_interface),
            ("Native Connection", self.test_native_connection),
            ("Database Connectivity", self.test_database_connectivity),
            ("Basic Query Performance", self.test_query_performance),
            ("Data Insertion Test", self.test_data_insertion),
            ("Data Retrieval Test", self.test_data_retrieval),
            ("Concurrent Connections", self.test_concurrent_connections),
            ("Connection Pool Management", self.test_connection_pool),
            ("Error Handling", self.test_error_handling),
            ("System Tables Access", self.test_system_tables)
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                start_time = time.time()
                result = test_func()
                duration = time.time() - start_time
                
                self.test_results[test_name] = {
                    "status": "PASS" if result else "FAIL",
                    "duration": f"{duration:.2f}s"
                }
                
                if result:
                    print(f"✅ {test_name}: PASSED ({duration:.2f}s)")
                else:
                    print(f"❌ {test_name}: FAILED ({duration:.2f}s)")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                self.test_results[test_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
                all_passed = False
        
        self.cleanup()
        self.print_summary()
        return all_passed
    
    def test_http_interface(self) -> bool:
        """Test ClickHouse HTTP interface"""
        try:
            # Test ping endpoint
            response = requests.get(f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_HTTP_PORT}/ping", 
                                  timeout=CONNECTION_TIMEOUT)
            
            if response.status_code != 200:
                print(f"   Error: HTTP ping failed with status {response.status_code}")
                return False
            
            print(f"   HTTP ping: OK")
            
            # Test basic query via HTTP
            query = "SELECT version()"
            response = requests.get(
                f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_HTTP_PORT}/",
                params={"query": query},
                timeout=QUERY_TIMEOUT
            )
            
            if response.status_code == 200:
                version = response.text.strip()
                print(f"   ClickHouse Version: {version}")
                return True
            else:
                print(f"   Error: Query failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_native_connection(self) -> bool:
        """Test ClickHouse native connection"""
        try:
            # Use HTTP port for clickhouse_connect (it uses HTTP protocol internally)
            self.client = clickhouse_connect.get_client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_HTTP_PORT,  # Use HTTP port, not native port
                connect_timeout=CONNECTION_TIMEOUT,
                send_receive_timeout=QUERY_TIMEOUT
            )
            
            # Test basic query
            result = self.client.query("SELECT 1 as test")
            
            if result.result_rows[0][0] == 1:
                print(f"   Native connection: OK")
                return True
            else:
                print(f"   Error: Unexpected query result")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_database_connectivity(self) -> bool:
        """Test database connectivity and permissions"""
        try:
            if not self.client:
                self.test_native_connection()
            
            # Test database access
            databases = self.client.query("SHOW DATABASES").result_rows
            db_names = [row[0] for row in databases]
            
            print(f"   Available databases: {', '.join(db_names)}")
            
            # Test if we can access system database
            if 'system' not in db_names:
                print("   Error: Cannot access system database")
                return False
            
            # Test table creation permissions
            test_table = "test_connection_table"
            
            # Drop table if exists
            self.client.command(f"DROP TABLE IF EXISTS {test_table}")
            
            # Create test table
            create_sql = f"""
            CREATE TABLE {test_table} (
                id UInt64,
                timestamp DateTime,
                value Float64
            ) ENGINE = Memory
            """
            
            self.client.command(create_sql)
            
            # Verify table exists
            tables = self.client.query("SHOW TABLES").result_rows
            table_names = [row[0] for row in tables]
            
            if test_table in table_names:
                print(f"   Database connectivity: OK")
                print(f"   Table creation: OK")
                return True
            else:
                print(f"   Error: Table creation failed")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_query_performance(self) -> bool:
        """Test query performance benchmarks"""
        try:
            if not self.client:
                self.test_native_connection()
            
            queries = [
                ("Simple SELECT", "SELECT 1"),
                ("System Query", "SELECT name FROM system.tables LIMIT 10"),
                ("Aggregation", "SELECT count() FROM (SELECT * FROM system.numbers LIMIT 10000)"),
                ("Date Functions", "SELECT now(), today(), yesterday()")
            ]
            
            all_fast = True
            
            for query_name, query in queries:
                start_time = time.time()
                self.client.query(query)
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms < PERFORMANCE_THRESHOLD:
                    print(f"   {query_name}: {duration_ms:.2f}ms ✅")
                else:
                    print(f"   {query_name}: {duration_ms:.2f}ms ⚠️  (>threshold)")
                    all_fast = False
            
            return all_fast
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_data_insertion(self) -> bool:
        """Test data insertion capabilities"""
        try:
            if not self.client:
                self.test_native_connection()
            
            test_table = "test_insertion_table"
            
            # Create test table
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {test_table} (
                id UInt64,
                timestamp DateTime DEFAULT now(),
                symbol String,
                price Float64,
                volume Float64
            ) ENGINE = Memory
            """
            
            self.client.command(create_sql)
            
            # Insert test data
            from datetime import datetime
            test_data = [
                [1, datetime(2024, 1, 1, 12, 0, 0), "BTCUSDT", 45000.0, 1.5],
                [2, datetime(2024, 1, 1, 12, 1, 0), "ETHUSDT", 3000.0, 10.0],
                [3, datetime(2024, 1, 1, 12, 2, 0), "ADAUSDT", 0.5, 1000.0]
            ]
            
            self.client.insert(test_table, test_data, 
                             column_names=['id', 'timestamp', 'symbol', 'price', 'volume'])
            
            # Verify insertion
            count_result = self.client.query(f"SELECT count() FROM {test_table}")
            row_count = count_result.result_rows[0][0]
            
            if row_count == 3:
                print(f"   Data insertion: OK ({row_count} rows)")
                return True
            else:
                print(f"   Error: Expected 3 rows, got {row_count}")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_data_retrieval(self) -> bool:
        """Test data retrieval and query functionality"""
        try:
            if not self.client:
                self.test_native_connection()
            
            test_table = "test_insertion_table"
            
            # Test basic SELECT
            result = self.client.query(f"SELECT * FROM {test_table} ORDER BY id")
            
            if len(result.result_rows) != 3:
                print(f"   Error: Expected 3 rows, got {len(result.result_rows)}")
                return False
            
            # Test aggregation
            avg_result = self.client.query(f"SELECT avg(price) FROM {test_table}")
            avg_price = avg_result.result_rows[0][0]
            
            expected_avg = (45000.0 + 3000.0 + 0.5) / 3
            if abs(avg_price - expected_avg) < 0.01:
                print(f"   Data retrieval: OK")
                print(f"   Aggregation: OK (avg price: {avg_price:.2f})")
                return True
            else:
                print(f"   Error: Aggregation mismatch. Expected {expected_avg:.2f}, got {avg_price:.2f}")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_concurrent_connections(self) -> bool:
        """Test concurrent connection handling"""
        try:
            async def run_concurrent_queries():
                clients = []
                
                # Create multiple clients
                for i in range(5):
                    client = clickhouse_connect.get_client(
                        host=CLICKHOUSE_HOST,
                        port=CLICKHOUSE_HTTP_PORT,  # Use HTTP port
                        connect_timeout=CONNECTION_TIMEOUT
                    )
                    clients.append(client)
                
                # Run queries concurrently
                tasks = []
                for i, client in enumerate(clients):
                    query = f"SELECT {i} as client_id, count() FROM (SELECT * FROM system.numbers LIMIT 10000)"
                    task = asyncio.create_task(self._run_query(client, query))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check results
                success_count = sum(1 for r in results if not isinstance(r, Exception))
                
                # Close clients
                for client in clients:
                    client.close()
                
                return success_count == 5
            
            # Run async test
            result = asyncio.run(run_concurrent_queries())
            
            if result:
                print(f"   Concurrent connections: OK (5/5 successful)")
                return True
            else:
                print(f"   Error: Some concurrent connections failed")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _run_query(self, client, query):
        """Helper method for concurrent query execution"""
        try:
            result = client.query(query)
            return len(result.result_rows)
        except Exception as e:
            raise e
    
    def test_connection_pool(self) -> bool:
        """Test connection pool management"""
        try:
            # Test connection reuse
            if not self.client:
                self.test_native_connection()
            
            # Run multiple queries on same connection
            for i in range(10):
                result = self.client.query(f"SELECT {i} as iteration")
                if result.result_rows[0][0] != i:
                    print(f"   Error: Query {i} failed")
                    return False
            
            print(f"   Connection pool: OK (10 queries on same connection)")
            return True
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling and recovery"""
        try:
            if not self.client:
                self.test_native_connection()
            
            # Test invalid query
            try:
                self.client.query("SELECT invalid_column FROM non_existent_table")
                print(f"   Error: Invalid query should have failed")
                return False
            except Exception:
                print(f"   Invalid query handling: OK")
            
            # Test connection still works after error
            result = self.client.query("SELECT 1")
            if result.result_rows[0][0] == 1:
                print(f"   Connection recovery: OK")
                return True
            else:
                print(f"   Error: Connection not recovered after error")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_system_tables(self) -> bool:
        """Test access to system tables"""
        try:
            if not self.client:
                self.test_native_connection()
            
            system_queries = [
                ("System Tables", "SELECT name FROM system.tables WHERE database = 'system' LIMIT 5"),
                ("System Processes", "SELECT query FROM system.processes LIMIT 3"),
                ("System Settings", "SELECT name, value FROM system.settings WHERE name LIKE '%timeout%' LIMIT 3")
            ]
            
            for query_name, query in system_queries:
                result = self.client.query(query)
                if len(result.result_rows) > 0:
                    print(f"   {query_name}: OK ({len(result.result_rows)} rows)")
                else:
                    print(f"   {query_name}: Warning (no results)")
            
            return True
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def cleanup(self):
        """Cleanup test artifacts"""
        try:
            if self.client:
                # Drop test tables
                test_tables = ["test_connection_table", "test_insertion_table"]
                for table in test_tables:
                    try:
                        self.client.command(f"DROP TABLE IF EXISTS {table}")
                    except:
                        pass  # Ignore errors during cleanup
                
                self.client.close()
                
        except Exception:
            pass  # Ignore cleanup errors
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 ClickHouse Test Summary")
        print("=" * 50)
        
        passed = sum(1 for r in self.test_results.values() if r['status'] == 'PASS')
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            duration = result.get('duration', 'N/A')
            print(f"{status_icon} {test_name}: {result['status']} ({duration})")
        
        print(f"\nResult: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All ClickHouse tests PASSED!")
        else:
            print("⚠️  Some ClickHouse tests FAILED!")


def main():
    """Main test execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python clickhouse_connection_test.py")
        print("Tests ClickHouse connection and functionality for DarkMa Trading System")
        return
    
    test_suite = ClickHouseTest()
    success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
