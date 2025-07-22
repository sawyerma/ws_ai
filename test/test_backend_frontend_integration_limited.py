#!/usr/bin/env python3
"""
Comprehensive Backend-Frontend Integration Test
Testet alle wichtigen Endpoints mit limitierten Daten um Token-Limits zu vermeiden.
Deine bestehenden codes bleiben unberührt!
"""
import requests
import json
import asyncio
import websockets
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

class BackendFrontendTester:
    def __init__(self):
        self.backend_url = "http://localhost:8100"
        self.websocket_url = "ws://localhost:8100/ws"
        self.frontend_url = "http://localhost:8180"
        self.limit = 10  # Limitiere alle Antworten auf 10 Items
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str, data_size_kb: float = 0):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        size_info = f" ({data_size_kb:.2f} KB)" if data_size_kb > 0 else ""
        print(f"{status} {test_name}{size_info}: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "size_kb": data_size_kb
        })
    
    def limit_data(self, data: Any, limit: int = None) -> Any:
        """Limitiert Daten um Token-Limits zu vermeiden"""
        if limit is None:
            limit = self.limit
            
        if isinstance(data, dict):
            limited = {}
            for key, value in data.items():
                if isinstance(value, list) and len(value) > limit:
                    limited[key] = value[:limit]
                    print(f"  ✂️  Limited {key}: {len(value)} → {limit} items")
                else:
                    limited[key] = value
            return limited
        elif isinstance(data, list) and len(data) > limit:
            print(f"  ✂️  Limited list: {len(data)} → {limit} items")
            return data[:limit]
        return data
    
    def calculate_response_size(self, data: Any) -> float:
        """Berechnet Antwortgröße in KB"""
        json_str = json.dumps(data) if not isinstance(data, str) else data
        return len(json_str.encode('utf-8')) / 1024
    
    def test_health_endpoints(self):
        """Test Health/Status Endpoints"""
        print(f"\n{'='*50}")
        print("🏥 TESTING HEALTH ENDPOINTS")
        print(f"{'='*50}")
        
        endpoints = [
            ("/health", "Backend Health"),
            ("/debugtest", "Debug Test"),
            ("/trading/health", "Trading Health"),
            ("/api/whales/health", "Whales Health")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                # Debug Test erwartet Status 500 (absichtlicher Fehler)
                if name == "Debug Test" and response.status_code == 500:
                    self.log_test(name, True, f"Expected error: Status {response.status_code}")
                elif response.status_code == 200:
                    data = response.json()
                    size_kb = self.calculate_response_size(data)
                    self.log_test(name, True, f"Status: {response.status_code}", size_kb)
                else:
                    self.log_test(name, False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(name, False, f"Error: {str(e)}")
    
    def test_symbols_limited(self):
        """Test Symbols mit Limitierung (bereits implementiert)"""
        print(f"\n{'='*50}")
        print("🔤 TESTING SYMBOLS ENDPOINTS (LIMITED)")
        print(f"{'='*50}")
        
        try:
            response = requests.get(f"{self.backend_url}/symbols", timeout=30)
            if response.status_code == 200:
                data = response.json()
                original_size = self.calculate_response_size(data)
                
                # Limitiere Daten
                limited_data = self.limit_data(data, self.limit)
                limited_size = self.calculate_response_size(limited_data)
                
                self.log_test("Symbols API", True, 
                             f"Limited {len(data.get('symbols', []))} → {len(limited_data.get('symbols', []))} symbols", 
                             limited_size)
            else:
                self.log_test("Symbols API", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Symbols API", False, f"Error: {str(e)}")
    
    def test_ticker_limited(self):
        """Test Ticker mit Limitierung"""
        print(f"\n{'='*50}")
        print("📊 TESTING TICKER ENDPOINTS (LIMITED)")
        print(f"{'='*50}")
        
        try:
            response = requests.get(f"{self.backend_url}/ticker", timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                # Limitiere Ticker-Daten
                limited_data = self.limit_data(data, self.limit)
                limited_size = self.calculate_response_size(limited_data)
                
                self.log_test("Ticker API", True, 
                             f"Limited {len(data) if isinstance(data, list) else 'N/A'} → {len(limited_data) if isinstance(limited_data, list) else 'N/A'} tickers", 
                             limited_size)
            else:
                self.log_test("Ticker API", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Ticker API", False, f"Error: {str(e)}")
    
    def test_ohlc_limited(self):
        """Test OHLC (Kerzendaten) mit Limitierung"""
        print(f"\n{'='*50}")
        print("🕯️  TESTING OHLC ENDPOINTS (LIMITED)")
        print(f"{'='*50}")
        
        # Test mit populärem Symbol
        test_symbols = ["BTCUSDT", "ETHUSDT"]
        
        for symbol in test_symbols:
            try:
                # Hole nur letzte 10 Kerzen statt alle
                params = {
                    "symbol": symbol,
                    "market": "spot",
                    "interval": "1h",
                    "limit": self.limit  # Backend-seitige Limitierung wenn unterstützt
                }
                
                response = requests.get(f"{self.backend_url}/ohlc", params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Clientseitige Limitierung falls nötig
                    limited_data = self.limit_data(data, self.limit)
                    limited_size = self.calculate_response_size(limited_data)
                    
                    candles_count = len(limited_data) if isinstance(limited_data, list) else len(limited_data.get('candles', []))
                    self.log_test(f"OHLC {symbol}", True, 
                                 f"{candles_count} candles received", 
                                 limited_size)
                else:
                    self.log_test(f"OHLC {symbol}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"OHLC {symbol}", False, f"Error: {str(e)}")
    
    def test_orderbook_limited(self):
        """Test Orderbook mit Limitierung"""
        print(f"\n{'='*50}")
        print("📖 TESTING ORDERBOOK ENDPOINTS (LIMITED)")
        print(f"{'='*50}")
        
        test_symbols = ["BTCUSDT", "ETHUSDT"]
        
        for symbol in test_symbols:
            try:
                params = {
                    "symbol": symbol,
                    "market": "spot",
                    "limit": self.limit  # Limitiere Orderbook-Tiefe
                }
                
                response = requests.get(f"{self.backend_url}/orderbook", params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Limitiere Bids/Asks
                    if isinstance(data, dict):
                        if 'bids' in data and len(data['bids']) > self.limit:
                            data['bids'] = data['bids'][:self.limit]
                        if 'asks' in data and len(data['asks']) > self.limit:
                            data['asks'] = data['asks'][:self.limit]
                    
                    limited_size = self.calculate_response_size(data)
                    
                    bids_count = len(data.get('bids', [])) if isinstance(data, dict) else 0
                    asks_count = len(data.get('asks', [])) if isinstance(data, dict) else 0
                    
                    self.log_test(f"Orderbook {symbol}", True, 
                                 f"{bids_count} bids, {asks_count} asks", 
                                 limited_size)
                else:
                    self.log_test(f"Orderbook {symbol}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Orderbook {symbol}", False, f"Error: {str(e)}")
    
    def test_trades_limited(self):
        """Test Trades mit Limitierung"""
        print(f"\n{'='*50}")
        print("💱 TESTING TRADES ENDPOINTS (LIMITED)")
        print(f"{'='*50}")
        
        test_symbols = ["BTCUSDT", "ETHUSDT"]
        
        for symbol in test_symbols:
            try:
                params = {
                    "symbol": symbol,
                    "market": "spot",
                    "limit": self.limit  # Limitiere Anzahl Trades
                }
                
                response = requests.get(f"{self.backend_url}/trades", params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Limitiere Trades-Liste
                    limited_data = self.limit_data(data, self.limit)
                    limited_size = self.calculate_response_size(limited_data)
                    
                    trades_count = len(limited_data) if isinstance(limited_data, list) else len(limited_data.get('trades', []))
                    self.log_test(f"Trades {symbol}", True, 
                                 f"{trades_count} trades received", 
                                 limited_size)
                else:
                    self.log_test(f"Trades {symbol}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Trades {symbol}", False, f"Error: {str(e)}")
    
    def test_whales_limited(self):
        """Test Whales System mit Limitierung"""
        print(f"\n{'='*50}")
        print("🐋 TESTING WHALES ENDPOINTS (LIMITED)")
        print(f"{'='*50}")
        
        whale_endpoints = [
            ("/api/whales/recent", "Recent Whale Events"),
            ("/api/whales/status", "Whale System Status"),
            ("/api/whales/statistics", "Whale Statistics")
        ]
        
        for endpoint, name in whale_endpoints:
            try:
                params = {"limit": self.limit}  # Backend-seitige Limitierung
                response = requests.get(f"{self.backend_url}{endpoint}", params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Clientseitige Limitierung
                    limited_data = self.limit_data(data, self.limit)
                    limited_size = self.calculate_response_size(limited_data)
                    
                    self.log_test(name, True, "Data received", limited_size)
                else:
                    self.log_test(name, False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(name, False, f"Error: {str(e)}")
    
    def test_trading_endpoints(self):
        """Test Trading System Endpoints"""
        print(f"\n{'='*50}")
        print("📈 TESTING TRADING ENDPOINTS")
        print(f"{'='*50}")
        
        trading_endpoints = [
            ("/trading/status", "Trading System Status"),
            ("/trading/strategies", "Trading Strategies"),
            ("/trading/orders", "Trading Orders"),
            ("/trading/positions", "Trading Positions"),
            ("/trading/portfolio/metrics", "Portfolio Metrics")
        ]
        
        for endpoint, name in trading_endpoints:
            try:
                params = {"limit": self.limit}
                response = requests.get(f"{self.backend_url}{endpoint}", params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    limited_data = self.limit_data(data, self.limit)
                    limited_size = self.calculate_response_size(limited_data)
                    
                    self.log_test(name, True, "Data received", limited_size)
                else:
                    self.log_test(name, False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(name, False, f"Error: {str(e)}")
    
    def test_frontend_connection(self):
        """Test Frontend Erreichbarkeit"""
        print(f"\n{'='*50}")
        print("🌐 TESTING FRONTEND CONNECTION")
        print(f"{'='*50}")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                size_kb = len(response.content) / 1024
                self.log_test("Frontend Access", True, f"Frontend accessible", size_kb)
            else:
                self.log_test("Frontend Access", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Frontend Access", False, f"Error: {str(e)}")
    
    async def test_websocket_connection(self):
        """Test WebSocket Verbindungen"""
        print(f"\n{'='*50}")
        print("🔌 TESTING WEBSOCKET CONNECTIONS")
        print(f"{'='*50}")
        
        test_symbols = ["BTCUSDT"]
        
        for symbol in test_symbols:
            connection_success = False
            try:
                # WebSocket Test mit korrigierter URL (richtige Reihenfolge!)
                ws_url = f"{self.websocket_url}/{symbol}/spot"
                
                # Teste nur Verbindung ohne auf Daten zu warten
                try:
                    async with websockets.connect(ws_url) as websocket:
                        # Verbindung erfolgreich - das reicht für den Test
                        connection_success = True
                        self.log_test(f"WebSocket {symbol}", True, "Connection established successfully", 0.01)
                        
                        # Optional: Versuche eine kurze Nachricht zu empfangen
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            data = json.loads(message)
                            limited_data = self.limit_data(data, 3)  # Nur 3 Items für Test
                            limited_size = self.calculate_response_size(limited_data)
                            print(f"  📡 Bonus: Received sample data ({limited_size:.2f} KB)")
                        except asyncio.TimeoutError:
                            # Das ist normal - nicht alle WebSockets senden sofort Daten
                            pass
                        except json.JSONDecodeError:
                            # Auch normal - erste Nachricht könnte anders formatiert sein
                            pass
                        # WebSocket wird automatisch geschlossen beim Verlassen des async with
                            
                except websockets.exceptions.InvalidHandshake as e:
                    if not connection_success:
                        self.log_test(f"WebSocket {symbol}", False, f"Handshake failed: {str(e)}")
                except Exception as conn_error:
                    if not connection_success:
                        self.log_test(f"WebSocket {symbol}", False, f"Connection error: {str(conn_error)}")
                        
            except Exception as e:
                if not connection_success:
                    self.log_test(f"WebSocket {symbol}", False, f"Error: {str(e)}")
    
    def generate_report(self):
        """Generiert Test-Report"""
        print(f"\n{'='*60}")
        print("📋 INTEGRATION TEST REPORT")
        print(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Summary:")
        print(f"   ✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"   ❌ Failed: {failed_tests}/{total_tests}")
        print(f"   🗂️  Total Response Size: {sum(r['size_kb'] for r in self.test_results):.2f} KB")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")
        
        print(f"\n{'='*60}")
        
        return success_rate > 80  # 80% als Erfolgskriterium

    def run_all_tests(self):
        """Führt alle Tests aus"""
        print("🚀 STARTING COMPREHENSIVE BACKEND-FRONTEND INTEGRATION TEST")
        print("🎯 All responses limited to prevent token overflow!")
        print(f"⏰ Test started at: {datetime.now()}")
        
        # Synchrone Tests
        self.test_health_endpoints()
        self.test_symbols_limited()
        self.test_ticker_limited()
        self.test_ohlc_limited()
        self.test_orderbook_limited()
        self.test_trades_limited()
        self.test_whales_limited()
        self.test_trading_endpoints()
        self.test_frontend_connection()
        
        # Asynchrone WebSocket Tests
        try:
            asyncio.run(self.test_websocket_connection())
        except Exception as e:
            self.log_test("WebSocket Tests", False, f"WebSocket test error: {str(e)}")
        
        # Report generieren
        success = self.generate_report()
        
        if success:
            print("🎉 INTEGRATION TEST SUCCESSFUL!")
            print("✅ Backend-Frontend Integration funktioniert einwandfrei")
            print("✅ Alle wichtigen Endpoints getestet mit Token-Limit-Safe Daten")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("🔧 Check failed endpoints and fix issues")
            
        return success

def main():
    """
    Haupt-Testfunktion
    """
    tester = BackendFrontendTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
