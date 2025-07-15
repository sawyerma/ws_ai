#!/usr/bin/env python3
"""
🚀 DarkMa Trading System - Start All Integration Test
====================================================

Comprehensive test suite for the intelligent "Start All" system including:
- Desktop GUI functionality  
- Service protection mechanisms
- ClickHouse database connectivity
- Backend API health
- Frontend dashboard
- Service detection and port monitoring
- Intelligence Start All button functionality

Run: python test/06_system_integration/start_all_system_test.py
"""

import os
import sys
import time
import subprocess
import requests
import socket
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class SystemIntegrationTest:
    """Comprehensive system integration test suite."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        self.project_root = Path(__file__).parent.parent.parent
        
        # Service definitions matching the Start All implementation
        self.critical_services = {
            "clickhouse-bolt": {
                "name": "ClickHouse Database",
                "ports": [8124, 9100],  # HTTP, Native
                "health_url": "http://localhost:8124/ping",
                "critical": True,
                "reason": "Speichert Live-Marktdaten permanent"
            },
            "backend_api": {
                "name": "Backend API (Data Collection)", 
                "ports": [8000, 8100],  # Standalone, Docker
                "health_url": "http://localhost:8000/health",
                "critical": True,
                "reason": "Sammelt Live-Marktdaten kontinuierlich"
            },
            "frontend": {
                "name": "Frontend Dashboard",
                "ports": [8080],
                "health_url": "http://localhost:8080",
                "critical": False,
                "reason": "User Interface"
            },
            "desktop_gui": {
                "name": "Desktop GUI",
                "process_name": "python",
                "script_path": "desktop_gui/main.py",
                "critical": False,
                "reason": "System Management Interface"
            }
        }
        
        self.mock_ki_services = [
            "whale_detection_001",
            "elliott_wave_001", 
            "grid_trading_btcusdt_001"
        ]
    
    def print_header(self):
        """Print test suite header."""
        print("🚀 DarkMa Trading System - Start All Integration Test")
        print("=" * 60)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project Root: {self.project_root}")
        print()
    
    def print_test_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """Print individual test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name:<40} ({duration:.2f}s)")
        if details:
            print(f"     {details}")
        self.test_results[test_name] = {
            "success": success,
            "duration": duration,
            "details": details
        }
    
    def check_port_open(self, host: str, port: int, timeout: float = 3.0) -> bool:
        """Check if a port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def check_http_health(self, url: str, timeout: float = 5.0) -> Tuple[bool, str]:
        """Check HTTP endpoint health."""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code in [200, 201]:
                return True, f"HTTP {response.status_code}"
            else:
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except requests.exceptions.Timeout:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def check_process_running(self, process_name: str, script_path: str = None) -> bool:
        """Check if a process is running."""
        try:
            if script_path:
                cmd = ["pgrep", "-f", f"{process_name}.*{script_path}"]
            else:
                cmd = ["pgrep", process_name]
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False
    
    def check_docker_container(self, container_name: str) -> Tuple[bool, str]:
        """Check Docker container status."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Status}}"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                status = result.stdout.decode().strip()
                if status and "Up" in status:
                    if "healthy" in status:
                        return True, "Running (healthy)"
                    else:
                        return True, "Running"
                else:
                    return False, "Not running"
            return False, "Docker command failed"
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_docker_services(self):
        """Test Docker services status."""
        print("\n🐳 Testing Docker Services")
        print("-" * 30)
        
        start_time = time.time()
        
        # Test Docker daemon
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, timeout=10)
            docker_running = result.returncode == 0
        except Exception:
            docker_running = False
        
        if not docker_running:
            self.print_test_result("Docker Daemon", False, time.time() - start_time, "Docker not running")
            return
        
        self.print_test_result("Docker Daemon", True, time.time() - start_time)
        
        # Test ClickHouse container
        start_time = time.time()
        container_running, status = self.check_docker_container("clickhouse-bolt")
        self.print_test_result("ClickHouse Container", container_running, time.time() - start_time, status)
    
    def test_service_ports(self):
        """Test all service ports."""
        print("\n🔌 Testing Service Ports")
        print("-" * 25)
        
        for service_id, config in self.critical_services.items():
            if "ports" not in config:
                continue
                
            for port in config["ports"]:
                start_time = time.time()
                port_open = self.check_port_open("localhost", port)
                status = "Open" if port_open else "Closed"
                self.print_test_result(f"{config['name']} Port {port}", port_open, time.time() - start_time, status)
    
    def test_service_health(self):
        """Test service health endpoints."""
        print("\n🏥 Testing Service Health")
        print("-" * 26)
        
        for service_id, config in self.critical_services.items():
            if "health_url" not in config:
                continue
                
            start_time = time.time()
            healthy, details = self.check_http_health(config["health_url"])
            self.print_test_result(f"{config['name']} Health", healthy, time.time() - start_time, details)
    
    def test_process_monitoring(self):
        """Test running processes."""
        print("\n🔍 Testing Running Processes")
        print("-" * 29)
        
        # Test Desktop GUI process
        start_time = time.time()
        gui_running = self.check_process_running("python", "desktop_gui/main.py")
        self.print_test_result("Desktop GUI Process", gui_running, time.time() - start_time)
        
        # Test Backend process
        start_time = time.time()
        backend_running = self.check_process_running("uvicorn", "core.main:app")
        self.print_test_result("Backend Process", backend_running, time.time() - start_time)
    
    def test_service_protection_logic(self):
        """Test service protection logic."""
        print("\n🔒 Testing Service Protection Logic")
        print("-" * 35)
        
        start_time = time.time()
        
        # Test critical service detection
        protected_services = []
        
        for service_id, config in self.critical_services.items():
            if not config.get("critical", False):
                continue
                
            service_running = False
            
            # Check ports
            if "ports" in config:
                for port in config["ports"]:
                    if self.check_port_open("localhost", port):
                        service_running = True
                        break
            
            # Check processes
            if "process_name" in config and "script_path" in config:
                if self.check_process_running(config["process_name"], config["script_path"]):
                    service_running = True
            
            if service_running:
                protected_services.append({
                    "id": service_id,
                    "name": config["name"],
                    "reason": config["reason"],
                    "protected": True
                })
        
        protection_working = len(protected_services) > 0
        details = f"Protected {len(protected_services)} critical services"
        
        self.print_test_result("Service Protection Detection", protection_working, time.time() - start_time, details)
        
        # Print protected services
        for service in protected_services:
            print(f"     🔒 {service['name']} - {service['reason']}")
    
    def test_start_all_prerequisites(self):
        """Test Start All system prerequisites."""
        print("\n🚀 Testing Start All Prerequisites")
        print("-" * 34)
        
        # Test system tray module import
        start_time = time.time()
        try:
            sys.path.append(str(self.project_root / "desktop_gui"))
            from desktop_gui.core.system_tray import StartAllWorker, EnhancedSystemTrayManager
            import_success = True
            details = "Module imports successful"
        except Exception as e:
            import_success = False
            details = f"Import error: {e}"
        
        self.print_test_result("Start All Module Import", import_success, time.time() - start_time, details)
        
        # Test Start All worker initialization
        if import_success:
            start_time = time.time()
            try:
                worker = StartAllWorker()
                worker_init = True
                details = "StartAllWorker initialized"
            except Exception as e:
                worker_init = False
                details = f"Worker init error: {e}"
            
            self.print_test_result("Start All Worker Init", worker_init, time.time() - start_time, details)
    
    def test_intelligent_service_detection(self):
        """Test intelligent service detection logic."""
        print("\n🧠 Testing Intelligent Service Detection")
        print("-" * 39)
        
        start_time = time.time()
        
        detected_services = {}
        
        # ClickHouse detection
        if self.check_port_open("localhost", 8124):
            detected_services["clickhouse"] = "Port 8124 (docker-compose port)"
        elif self.check_port_open("localhost", 8123):
            detected_services["clickhouse"] = "Port 8123 (standard port)"
        
        # Backend detection  
        if self.check_port_open("localhost", 8000):
            detected_services["backend"] = "Port 8000 (standalone)"
        elif self.check_port_open("localhost", 8100):
            detected_services["backend"] = "Port 8100 (docker)"
        
        # Frontend detection
        if self.check_port_open("localhost", 8080):
            detected_services["frontend"] = "Port 8080"
        elif self.check_port_open("localhost", 8180):
            detected_services["frontend"] = "Port 8180 (docker)"
        
        detection_working = len(detected_services) >= 2  # At least 2 services detected
        details = f"Detected {len(detected_services)} services: {', '.join(detected_services.keys())}"
        
        self.print_test_result("Intelligent Detection", detection_working, time.time() - start_time, details)
        
        for service, details in detected_services.items():
            print(f"     🎯 {service}: {details}")
    
    def test_system_integration(self):
        """Test overall system integration."""
        print("\n🌐 Testing System Integration")
        print("-" * 28)
        
        start_time = time.time()
        
        # Count functional services
        functional_services = 0
        total_services = len(self.critical_services)
        
        for service_id, config in self.critical_services.items():
            service_functional = False
            
            # Check ports
            if "ports" in config:
                for port in config["ports"]:
                    if self.check_port_open("localhost", port):
                        service_functional = True
                        break
            
            # Check health endpoints
            if "health_url" in config:
                healthy, _ = self.check_http_health(config["health_url"])
                if healthy:
                    service_functional = True
            
            # Check processes
            if "process_name" in config and "script_path" in config:
                if self.check_process_running(config["process_name"], config["script_path"]):
                    service_functional = True
            
            if service_functional:
                functional_services += 1
        
        integration_score = (functional_services / total_services) * 100
        integration_success = integration_score >= 50  # At least 50% functional
        
        details = f"{functional_services}/{total_services} services functional ({integration_score:.1f}%)"
        
        self.print_test_result("System Integration Score", integration_success, time.time() - start_time, details)
    
    def run_all_tests(self):
        """Run complete test suite."""
        self.print_header()
        
        # Core infrastructure tests
        self.test_docker_services()
        self.test_service_ports()
        self.test_service_health()
        self.test_process_monitoring()
        
        # Start All system tests
        self.test_service_protection_logic()
        self.test_start_all_prerequisites()
        self.test_intelligent_service_detection()
        
        # Integration test
        self.test_system_integration()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_duration = sum(result["duration"] for result in self.test_results.values())
        
        print(f"✅ Passed:       {passed_tests:2d}/{total_tests}")
        print(f"❌ Failed:       {failed_tests:2d}/{total_tests}")
        print(f"📈 Success Rate: {success_rate:5.1f}%")
        print(f"⏱️  Total Time:   {total_duration:5.2f}s")
        print(f"🏁 Completed:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Service status overview
        print("\n🔍 Service Status Overview:")
        print("-" * 30)
        
        clickhouse_port = self.check_port_open("localhost", 8124)
        backend_port = self.check_port_open("localhost", 8000) or self.check_port_open("localhost", 8100)
        frontend_port = self.check_port_open("localhost", 8080)
        
        print(f"🗄️  ClickHouse:  {'🟢 Running' if clickhouse_port else '🔴 Stopped'}")
        print(f"⚙️  Backend:     {'🟢 Running' if backend_port else '🔴 Stopped'}")
        print(f"🌐 Frontend:    {'🟢 Running' if frontend_port else '🔴 Stopped'}")
        
        # Overall system status
        if success_rate >= 80:
            status_emoji = "🚀"
            status_text = "Ready to Trade!"
        elif success_rate >= 60:
            status_emoji = "⚠️"
            status_text = "Partially Functional"
        else:
            status_emoji = "❌"
            status_text = "System Issues Detected"
        
        print(f"\n{status_emoji} Overall Status: {status_text}")
        
        if failed_tests > 0:
            print(f"\n⚠️  Failed Tests:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    print(f"   ❌ {test_name}: {result['details']}")
        
        print("\n" + "=" * 60)


def main():
    """Main test execution."""
    try:
        # Change to project directory
        project_root = Path(__file__).parent.parent.parent
        os.chdir(project_root)
        
        # Run tests
        test_suite = SystemIntegrationTest()
        test_suite.run_all_tests()
        
        # Exit with proper code
        total_tests = len(test_suite.test_results)
        passed_tests = sum(1 for result in test_suite.test_results.values() if result["success"])
        
        if passed_tests == total_tests:
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
