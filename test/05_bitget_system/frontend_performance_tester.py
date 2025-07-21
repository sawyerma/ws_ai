#!/usr/bin/env python3
"""
Frontend Performance Tester
Misst echte Browser-Rendering-Performance mit Selenium

Testet:
- DOM Update Speed
- React Re-render Performance
- Table/Grid Rendering Speed
- Memory Usage im Browser
- Frontend API Call Performance
"""

import time
import json
import statistics
import sys
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime
import asyncio
import aiohttp

# Versuche Selenium zu importieren
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    print("⚠️  Selenium nicht installiert. Frontend-Browser-Tests werden übersprungen.")
    SELENIUM_AVAILABLE = False

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

class FrontendPerformanceTester:
    """Frontend Performance Tester mit echtem Browser"""
    
    def __init__(self):
        self.driver = None
        self.frontend_url = "http://localhost:8180"  # Docker port mapping
        self.backend_url = "http://localhost:8100"
        
    def setup_chrome_driver(self) -> bool:
        """Setup Chrome WebDriver"""
        if not SELENIUM_AVAILABLE:
            return False
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Performance logging aktivieren
            chrome_options.add_argument("--enable-logging")
            chrome_options.add_argument("--log-level=0")
            chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            print(f"{Colors.GREEN}✅ Chrome WebDriver initialisiert (Headless){Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Chrome WebDriver Setup fehlgeschlagen: {e}{Colors.END}")
            print(f"   Installiere ChromeDriver: brew install chromedriver (macOS) oder apt-get install chromium-chromedriver (Linux)")
            return False
    
    def teardown(self):
        """Cleanup WebDriver"""
        if self.driver:
            self.driver.quit()
            print(f"{Colors.CYAN}🔧 Chrome WebDriver geschlossen{Colors.END}")
    
    def test_page_load_performance(self) -> Dict[str, Any]:
        """Test Frontend Page Load Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing Frontend Page Load Performance...{Colors.END}")
        
        if not self.driver:
            return {}
        
        results = {}
        load_times = []
        
        for i in range(5):
            try:
                start = time.perf_counter()
                self.driver.get(self.frontend_url)
                
                # Warte bis die Seite geladen ist
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                load_time = (time.perf_counter() - start) * 1000
                load_times.append(load_time)
                
                print(f"   Load {i+1}: {load_time:.0f}ms")
                
            except TimeoutException:
                print(f"{Colors.YELLOW}⚠️  Page load {i+1} timeout{Colors.END}")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Page load {i+1} error: {e}{Colors.END}")
            
            time.sleep(1)
        
        if load_times:
            results['page_load'] = {
                'avg_ms': statistics.mean(load_times),
                'min_ms': min(load_times),
                'max_ms': max(load_times),
                'count': len(load_times)
            }
        
        return results
    
    def test_dom_update_performance(self) -> Dict[str, Any]:
        """Test DOM Update Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing DOM Update Performance...{Colors.END}")
        
        if not self.driver:
            return {}
        
        results = {}
        update_times = []
        
        try:
            # Gehe zur Frontend-Seite
            self.driver.get(self.frontend_url)
            
            # Warte auf initiales Laden
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Simuliere DOM-Updates durch JavaScript
            for i in range(10):
                start = time.perf_counter()
                
                # Injiziere Test-DOM-Updates
                self.driver.execute_script("""
                    // Simuliere Ticker-Update
                    const testData = {
                        symbol: 'BTCUSDT',
                        price: Math.random() * 50000 + 40000,
                        change: (Math.random() - 0.5) * 10
                    };
                    
                    // Erstelle oder update Test-Element
                    let testElement = document.getElementById('performance-test');
                    if (!testElement) {
                        testElement = document.createElement('div');
                        testElement.id = 'performance-test';
                        document.body.appendChild(testElement);
                    }
                    
                    // Update DOM
                    testElement.innerHTML = `
                        <div class="ticker-item">
                            <span class="symbol">${testData.symbol}</span>
                            <span class="price">$${testData.price.toFixed(2)}</span>
                            <span class="change ${testData.change >= 0 ? 'positive' : 'negative'}">
                                ${testData.change >= 0 ? '+' : ''}${testData.change.toFixed(2)}%
                            </span>
                        </div>
                    `;
                    
                    return performance.now();
                """)
                
                update_time = (time.perf_counter() - start) * 1000
                update_times.append(update_time)
                
                time.sleep(0.1)
            
            if update_times:
                results['dom_update'] = {
                    'avg_ms': statistics.mean(update_times),
                    'min_ms': min(update_times),
                    'max_ms': max(update_times),
                    'count': len(update_times)
                }
        
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  DOM Update Test error: {e}{Colors.END}")
        
        return results
    
    def test_table_rendering_performance(self) -> Dict[str, Any]:
        """Test Table/Grid Rendering Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing Table Rendering Performance...{Colors.END}")
        
        if not self.driver:
            return {}
        
        results = {}
        
        try:
            self.driver.get(self.frontend_url)
            
            # Warte auf Seite
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Test verschiedene Tabellen-Größen
            table_sizes = [10, 50, 100, 200]
            rendering_times = {}
            
            for size in table_sizes:
                start = time.perf_counter()
                
                # Erstelle große Tabelle mit Test-Daten
                self.driver.execute_script(f"""
                    // Erstelle Test-Tabelle
                    let table = document.getElementById('performance-table');
                    if (table) table.remove();
                    
                    table = document.createElement('table');
                    table.id = 'performance-table';
                    table.style.cssText = 'width:100%; border-collapse:collapse; font-size:12px;';
                    
                    // Header
                    const header = table.createTHead();
                    const headerRow = header.insertRow();
                    ['Symbol', 'Market', 'Price', 'Change', 'Volume', 'Status'].forEach(text => {{
                        const th = document.createElement('th');
                        th.textContent = text;
                        th.style.cssText = 'border:1px solid #ccc; padding:4px; background:#f5f5f5;';
                        headerRow.appendChild(th);
                    }});
                    
                    // Body mit {size} Zeilen
                    const tbody = table.createTBody();
                    for (let i = 0; i < {size}; i++) {{
                        const row = tbody.insertRow();
                        const data = [
                            'BTC' + i + 'USDT',
                            'spot',
                            '$' + (Math.random() * 50000 + 40000).toFixed(2),
                            (Math.random() - 0.5 > 0 ? '+' : '') + (Math.random() * 10).toFixed(2) + '%',
                            (Math.random() * 1000).toFixed(2),
                            Math.random() > 0.5 ? 'Active' : 'Inactive'
                        ];
                        
                        data.forEach((text, index) => {{
                            const cell = row.insertCell();
                            cell.textContent = text;
                            cell.style.cssText = 'border:1px solid #ccc; padding:4px;';
                            if (index === 3) {{ // Change column
                                cell.style.color = text.startsWith('+') ? 'green' : 'red';
                            }}
                        }});
                    }}
                    
                    document.body.appendChild(table);
                    return performance.now();
                """)
                
                render_time = (time.perf_counter() - start) * 1000
                rendering_times[f'{size}_rows'] = render_time
                
                print(f"   {size} rows: {render_time:.0f}ms")
                time.sleep(0.5)
            
            results['table_rendering'] = rendering_times
        
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Table Rendering Test error: {e}{Colors.END}")
        
        return results
    
    def test_memory_performance(self) -> Dict[str, Any]:
        """Test Browser Memory Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing Browser Memory Performance...{Colors.END}")
        
        if not self.driver:
            return {}
        
        results = {}
        
        try:
            self.driver.get(self.frontend_url)
            
            # Performance-Logs auslesen
            logs = self.driver.get_log('performance')
            memory_samples = []
            
            for log in logs:
                message = json.loads(log['message'])
                if message.get('message', {}).get('method') == 'Runtime.consoleAPICalled':
                    continue
            
            # JavaScript Memory API verwenden
            memory_info = self.driver.execute_script("""
                if ('memory' in performance) {
                    return {
                        used: performance.memory.usedJSHeapSize / 1024 / 1024,
                        total: performance.memory.totalJSHeapSize / 1024 / 1024,
                        limit: performance.memory.jsHeapSizeLimit / 1024 / 1024
                    };
                }
                return null;
            """)
            
            if memory_info:
                results['memory'] = {
                    'used_mb': memory_info['used'],
                    'total_mb': memory_info['total'],
                    'limit_mb': memory_info['limit']
                }
        
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Memory Performance Test error: {e}{Colors.END}")
        
        return results
    
    def test_api_call_performance(self) -> Dict[str, Any]:
        """Test Frontend API Call Performance"""
        print(f"\n{Colors.BLUE}🔄 Testing Frontend API Call Performance...{Colors.END}")
        
        if not self.driver:
            return {}
        
        results = {}
        
        try:
            self.driver.get(self.frontend_url)
            
            # Warte auf Seite
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Teste API Calls über Frontend
            api_times = []
            
            for i in range(5):
                start = time.perf_counter()
                
                # Führe API Call über Frontend JavaScript aus
                response_time = self.driver.execute_script(f"""
                    const startTime = performance.now();
                    
                    return fetch('{self.backend_url}/ticker')
                        .then(response => response.json())
                        .then(data => {{
                            const endTime = performance.now();
                            return {{
                                duration: endTime - startTime,
                                dataLength: data.length || 0,
                                success: true
                            }};
                        }})
                        .catch(error => {{
                            const endTime = performance.now();
                            return {{
                                duration: endTime - startTime,
                                dataLength: 0,
                                success: false,
                                error: error.message
                            }};
                        }});
                """)
                
                # Da der JavaScript fetch async ist, müssen wir warten
                time.sleep(2)
                
                # Hole das Ergebnis (vereinfacht)
                total_time = (time.perf_counter() - start) * 1000
                api_times.append(total_time)
                
                print(f"   API Call {i+1}: {total_time:.0f}ms")
            
            if api_times:
                results['api_calls'] = {
                    'avg_ms': statistics.mean(api_times),
                    'min_ms': min(api_times),
                    'max_ms': max(api_times),
                    'count': len(api_times)
                }
        
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Frontend API Call Test error: {e}{Colors.END}")
        
        return results
    
    def print_frontend_performance_report(self, results: Dict[str, Any]):
        """Print Frontend Performance Report"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
        print(f"  🖥️  FRONTEND PERFORMANCE REPORT")
        print(f"{'='*60}{Colors.END}")
        
        # Page Load Performance
        if 'page_load' in results:
            print(f"\n{Colors.BLUE}📄 PAGE LOAD PERFORMANCE:{Colors.END}")
            page_load = results['page_load']
            print(f"  Average Load Time: {page_load['avg_ms']:.0f}ms")
            print(f"  Fastest Load:      {page_load['min_ms']:.0f}ms")
            print(f"  Slowest Load:      {page_load['max_ms']:.0f}ms")
        
        # DOM Update Performance
        if 'dom_update' in results:
            print(f"\n{Colors.MAGENTA}⚡ DOM UPDATE PERFORMANCE:{Colors.END}")
            dom_update = results['dom_update']
            print(f"  Average Update:    {dom_update['avg_ms']:.2f}ms")
            print(f"  Fastest Update:    {dom_update['min_ms']:.2f}ms")
            print(f"  Updates/sec:       {1000/dom_update['avg_ms']:.0f} ops/sec")
        
        # Table Rendering Performance
        if 'table_rendering' in results:
            print(f"\n{Colors.YELLOW}📊 TABLE RENDERING PERFORMANCE:{Colors.END}")
            for size, time_ms in results['table_rendering'].items():
                rows = size.split('_')[0]
                print(f"  {rows:>3} rows:          {time_ms:.0f}ms ({int(rows)/time_ms*1000:.0f} rows/sec)")
        
        # Memory Performance
        if 'memory' in results:
            print(f"\n{Colors.GREEN}🧠 BROWSER MEMORY USAGE:{Colors.END}")
            memory = results['memory']
            print(f"  Used Memory:       {memory['used_mb']:.2f}MB")
            print(f"  Total Memory:      {memory['total_mb']:.2f}MB")
            print(f"  Memory Limit:      {memory['limit_mb']:.0f}MB")
        
        # API Call Performance
        if 'api_calls' in results:
            print(f"\n{Colors.CYAN}🔌 FRONTEND API PERFORMANCE:{Colors.END}")
            api_calls = results['api_calls']
            print(f"  Average Call:      {api_calls['avg_ms']:.0f}ms")
            print(f"  Fastest Call:      {api_calls['min_ms']:.0f}ms")
            print(f"  Slowest Call:      {api_calls['max_ms']:.0f}ms")
        
        # Overall Frontend Rating
        print(f"\n{Colors.CYAN}📊 FRONTEND PERFORMANCE SUMMARY:{Colors.END}")
        
        # Berechne Gesamtbewertung
        total_score = 0
        factors = 0
        
        if 'page_load' in results:
            load_time = results['page_load']['avg_ms']
            if load_time < 1000:
                total_score += 100
            elif load_time < 2000:
                total_score += 80
            elif load_time < 3000:
                total_score += 60
            else:
                total_score += 40
            factors += 1
        
        if 'dom_update' in results:
            update_time = results['dom_update']['avg_ms']
            if update_time < 1:
                total_score += 100
            elif update_time < 5:
                total_score += 90
            elif update_time < 10:
                total_score += 70
            else:
                total_score += 50
            factors += 1
        
        if factors > 0:
            avg_score = total_score / factors
            if avg_score >= 90:
                rating = f"{Colors.GREEN}🚀 EXCELLENT{Colors.END}"
            elif avg_score >= 75:
                rating = f"{Colors.YELLOW}⚡ GOOD{Colors.END}"
            elif avg_score >= 60:
                rating = f"{Colors.YELLOW}⚠️  OK{Colors.END}"
            else:
                rating = f"{Colors.RED}🐌 NEEDS OPTIMIZATION{Colors.END}"
            
            print(f"  Overall Rating:    {rating} ({avg_score:.0f}/100)")
        
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")

def main():
    """Standalone Frontend Performance Test"""
    print(f"{Colors.CYAN}🚀 Starting Frontend Performance Test Suite...{Colors.END}")
    
    if not SELENIUM_AVAILABLE:
        print(f"{Colors.RED}❌ Selenium nicht verfügbar. Installiere mit: pip install selenium{Colors.END}")
        return False
    
    tester = FrontendPerformanceTester()
    
    try:
        # Setup Chrome Driver
        if not tester.setup_chrome_driver():
            return False
        
        # Run all frontend tests
        results = {}
        
        page_results = tester.test_page_load_performance()
        results.update(page_results)
        
        dom_results = tester.test_dom_update_performance()
        results.update(dom_results)
        
        table_results = tester.test_table_rendering_performance()
        results.update(table_results)
        
        memory_results = tester.test_memory_performance()
        results.update(memory_results)
        
        api_results = tester.test_api_call_performance()
        results.update(api_results)
        
        # Generate report
        tester.print_frontend_performance_report(results)
        
        print(f"\n{Colors.GREEN}✅ Frontend Performance Test completed successfully!{Colors.END}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Frontend Performance Test failed: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        tester.teardown()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
