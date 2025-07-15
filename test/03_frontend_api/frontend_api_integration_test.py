#!/usr/bin/env python3
"""
Frontend API Integration Test
Tests the complete Frontend -> Backend API integration
"""

import asyncio
import sys
import time
import subprocess
import requests
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class FrontendApiIntegrationTest:
    """Test Frontend-Backend API integration"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8100"
        self.frontend_url = "http://localhost:8180"
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": time.time()
        })
    
    def test_backend_endpoints(self):
        """Test all backend endpoints that frontend should use"""
        print("\n🔍 Testing Backend API Endpoints...")
        
        endpoints = [
            "/symbols",
            "/ticker", 
            "/settings",
            "/ohlc?symbol=BTCUSDT",
            "/trades?symbol=BTCUSDT",
            "/orderbook?symbol=BTCUSDT",
            "/health"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Backend {endpoint}", True, f"Status: {response.status_code}, Data: {type(data)}")
                else:
                    self.log_test(f"Backend {endpoint}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Backend {endpoint}", False, f"Error: {str(e)}")
    
    def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        print("\n🌐 Testing Frontend Accessibility...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_test("Frontend Accessibility", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Frontend Accessibility", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Accessibility", False, f"Error: {str(e)}")
            return False
    
    def test_symbols_api_integration(self):
        """Test symbols API specifically"""
        print("\n🔗 Testing Symbols API Integration...")
        
        try:
            # Test backend symbols endpoint
            response = requests.get(f"{self.backend_url}/symbols", timeout=10)
            if response.status_code != 200:
                self.log_test("Symbols API Backend", False, f"Status: {response.status_code}")
                return
            
            data = response.json()
            if not data.get("symbols"):
                self.log_test("Symbols API Backend", False, "No symbols in response")
                return
            
            symbols_count = len(data["symbols"])
            self.log_test("Symbols API Backend", True, f"Found {symbols_count} symbols")
            
            # Test that we have more than just mock data (should be hundreds of symbols)
            if symbols_count > 10:
                self.log_test("Symbols API Data Quality", True, f"{symbols_count} symbols (not just mock data)")
            else:
                self.log_test("Symbols API Data Quality", False, f"Only {symbols_count} symbols (possibly mock data)")
            
            # Test symbol structure (Bitget API structure)
            first_symbol = data["symbols"][0]
            required_fields = ["symbol", "baseCoin", "quoteCoin"]
            missing_fields = [field for field in required_fields if field not in first_symbol]
            
            if not missing_fields:
                self.log_test("Symbols API Structure", True, "All required fields present")
            else:
                self.log_test("Symbols API Structure", False, f"Missing fields: {missing_fields}")
                
        except Exception as e:
            self.log_test("Symbols API Integration", False, f"Error: {str(e)}")
    
    def test_ticker_api_integration(self):
        """Test ticker API specifically"""
        print("\n📊 Testing Ticker API Integration...")
        
        try:
            response = requests.get(f"{self.backend_url}/ticker", timeout=10)
            if response.status_code != 200:
                self.log_test("Ticker API Backend", False, f"Status: {response.status_code}")
                return
            
            data = response.json()
            if not isinstance(data, list):
                self.log_test("Ticker API Backend", False, "Response is not a list")
                return
            
            ticker_count = len(data)
            self.log_test("Ticker API Backend", True, f"Found {ticker_count} tickers")
            
            # Test ticker structure
            if ticker_count > 0:
                first_ticker = data[0]
                required_fields = ["symbol", "last", "changeRate", "market_type"]
                missing_fields = [field for field in required_fields if field not in first_ticker]
                
                if not missing_fields:
                    self.log_test("Ticker API Structure", True, "All required fields present")
                else:
                    self.log_test("Ticker API Structure", False, f"Missing fields: {missing_fields}")
            
        except Exception as e:
            self.log_test("Ticker API Integration", False, f"Error: {str(e)}")
    
    def test_settings_api_integration(self):
        """Test settings API specifically"""
        print("\n⚙️ Testing Settings API Integration...")
        
        try:
            # Test GET settings
            response = requests.get(f"{self.backend_url}/settings", timeout=10)
            if response.status_code == 200:
                data = response.json()
                settings_count = len(data) if isinstance(data, list) else 0
                self.log_test("Settings API GET", True, f"Found {settings_count} settings")
            else:
                self.log_test("Settings API GET", False, f"Status: {response.status_code}")
            
            # Test POST settings (with sample data)
            sample_setting = [{
                "symbol": "BTCUSDT",
                "market": "spot",
                "store_live": True,
                "load_history": False,
                "favorite": False,
                "db_resolution": 1,
                "chart_resolution": "1m"
            }]
            
            response = requests.put(
                f"{self.backend_url}/settings",
                json=sample_setting,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Settings API PUT", True, "Settings saved successfully")
            else:
                self.log_test("Settings API PUT", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Settings API Integration", False, f"Error: {str(e)}")
    
    def test_websocket_endpoints(self):
        """Test WebSocket endpoints"""
        print("\n🔌 Testing WebSocket Endpoints...")
        
        # We can't easily test WebSocket from requests, but we can check if the WS port is open
        try:
            import socket
            
            # Test WebSocket port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', 8100))
            sock.close()
            
            if result == 0:
                self.log_test("WebSocket Port", True, "Port 8100 is open")
            else:
                self.log_test("WebSocket Port", False, "Port 8100 is not accessible")
                
        except Exception as e:
            self.log_test("WebSocket Port", False, f"Error: {str(e)}")
    
    def test_cors_headers(self):
        """Test CORS headers for frontend integration"""
        print("\n🌍 Testing CORS Headers...")
        
        try:
            response = requests.get(f"{self.backend_url}/symbols", timeout=10)
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            }
            
            if any(cors_headers.values()):
                self.log_test("CORS Headers", True, f"CORS headers present: {cors_headers}")
            else:
                self.log_test("CORS Headers", False, "No CORS headers found")
                
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
    
    def test_response_times(self):
        """Test API response times"""
        print("\n⏱️ Testing API Response Times...")
        
        endpoints = [
            "/symbols",
            "/ticker",
            "/health"
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code == 200:
                    if response_time < 100:  # Less than 100ms
                        self.log_test(f"Response Time {endpoint}", True, f"{response_time:.2f}ms")
                    else:
                        self.log_test(f"Response Time {endpoint}", False, f"{response_time:.2f}ms (too slow)")
                else:
                    self.log_test(f"Response Time {endpoint}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Response Time {endpoint}", False, f"Error: {str(e)}")
    
    def test_data_consistency(self):
        """Test data consistency between endpoints"""
        print("\n🔍 Testing Data Consistency...")
        
        try:
            # Get symbols
            symbols_response = requests.get(f"{self.backend_url}/symbols", timeout=10)
            if symbols_response.status_code != 200:
                self.log_test("Data Consistency", False, "Could not fetch symbols")
                return
            
            symbols_data = symbols_response.json()
            symbols_list = symbols_data.get("symbols", [])
            
            # Get tickers
            ticker_response = requests.get(f"{self.backend_url}/ticker", timeout=10)
            if ticker_response.status_code != 200:
                self.log_test("Data Consistency", False, "Could not fetch tickers")
                return
            
            tickers_data = ticker_response.json()
            
            # Check if symbols and tickers have overlapping data
            symbol_set = set(s["symbol"] for s in symbols_list)
            ticker_set = set(t["symbol"] for t in tickers_data)
            
            overlap = symbol_set.intersection(ticker_set)
            overlap_percentage = len(overlap) / len(symbol_set) * 100 if symbol_set else 0
            
            if overlap_percentage > 50:  # At least 50% overlap
                self.log_test("Data Consistency", True, f"{overlap_percentage:.1f}% symbol/ticker overlap")
            else:
                self.log_test("Data Consistency", False, f"Only {overlap_percentage:.1f}% symbol/ticker overlap")
                
        except Exception as e:
            self.log_test("Data Consistency", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Frontend API Integration Tests...")
        print("=" * 60)
        
        # Test backend endpoints
        self.test_backend_endpoints()
        
        # Test frontend accessibility
        self.test_frontend_accessibility()
        
        # Test specific API integrations
        self.test_symbols_api_integration()
        self.test_ticker_api_integration()
        self.test_settings_api_integration()
        
        # Test WebSocket endpoints
        self.test_websocket_endpoints()
        
        # Test CORS headers
        self.test_cors_headers()
        
        # Test response times
        self.test_response_times()
        
        # Test data consistency
        self.test_data_consistency()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 FRONTEND API INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n💡 RECOMMENDATIONS:")
        
        if failed_tests == 0:
            print("  ✅ All tests passed! Frontend-Backend integration is working correctly.")
        else:
            print(f"  ⚠️  {failed_tests} tests failed. Check the following:")
            print("  1. Ensure backend is running on http://localhost:8100")
            print("  2. Ensure frontend is running on http://localhost:8180")
            print("  3. Check that all API endpoints are properly implemented")
            print("  4. Verify CORS headers are set correctly")
            print("  5. Check that real data (not mock data) is being served")
        
        return failed_tests == 0


def main():
    """Main function"""
    test_runner = FrontendApiIntegrationTest()
    success = test_runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
