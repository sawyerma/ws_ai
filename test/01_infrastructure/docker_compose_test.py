#!/usr/bin/env python3
"""
DarkMa Trading System - Docker Compose Tests
===========================================

Tests für Docker Services Health Check und Container Orchestration.
"""

import os
import sys
import time
import docker
import requests
import subprocess
from typing import Dict, List, Optional

# Test Configuration
DOCKER_COMPOSE_FILE = "../../docker-compose.yml"
REQUIRED_SERVICES = ["clickhouse", "backend"]
HEALTH_CHECK_TIMEOUT = 60  # seconds
SERVICE_STARTUP_TIMEOUT = 120  # seconds

class DockerComposeTest:
    """Docker Compose Test Suite"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.project_name = "darkma-trading"
        self.test_results = {}
        
    def run_all_tests(self) -> bool:
        """Run all Docker Compose tests"""
        print("🐳 Docker Compose Test Suite")
        print("=" * 50)
        
        tests = [
            ("Docker Engine Check", self.test_docker_engine),
            ("Docker Compose File", self.test_compose_file_exists),
            ("Services Startup", self.test_services_startup),
            ("Network Connectivity", self.test_network_connectivity),
            ("Resource Usage", self.test_resource_usage),
            ("Health Checks", self.test_health_checks),
            ("Service Dependencies", self.test_service_dependencies),
            ("Cleanup Test", self.test_cleanup)
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
        
        self.print_summary()
        return all_passed
    
    def test_docker_engine(self) -> bool:
        """Test Docker Engine availability"""
        try:
            self.client.ping()
            version = self.client.version()
            print(f"   Docker Version: {version['Version']}")
            return True
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_compose_file_exists(self) -> bool:
        """Test Docker Compose file exists and is valid"""
        compose_path = os.path.join(os.path.dirname(__file__), DOCKER_COMPOSE_FILE)
        
        if not os.path.exists(compose_path):
            print(f"   Error: Docker Compose file not found: {compose_path}")
            return False
        
        # Validate compose file
        try:
            result = subprocess.run(
                ["docker-compose", "-f", compose_path, "config"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(compose_path)
            )
            
            if result.returncode != 0:
                print(f"   Error: Invalid compose file: {result.stderr}")
                return False
                
            print(f"   Docker Compose file valid: {compose_path}")
            return True
            
        except Exception as e:
            print(f"   Error validating compose file: {e}")
            return False
    
    def test_services_startup(self) -> bool:
        """Test services startup within timeout"""
        compose_path = os.path.join(os.path.dirname(__file__), DOCKER_COMPOSE_FILE)
        
        try:
            # Start services
            print("   Starting Docker Compose services...")
            result = subprocess.run(
                ["docker-compose", "-f", compose_path, "up", "-d"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(compose_path)
            )
            
            if result.returncode != 0:
                print(f"   Error starting services: {result.stderr}")
                return False
            
            # Wait for services to be ready
            start_time = time.time()
            while time.time() - start_time < SERVICE_STARTUP_TIMEOUT:
                all_running = True
                
                for service in REQUIRED_SERVICES:
                    try:
                        containers = self.client.containers.list(
                            filters={"label": f"com.docker.compose.service={service}"}
                        )
                        
                        if not containers or containers[0].status != "running":
                            all_running = False
                            break
                            
                    except Exception:
                        all_running = False
                        break
                
                if all_running:
                    duration = time.time() - start_time
                    print(f"   All services started in {duration:.2f}s")
                    return True
                
                time.sleep(2)
            
            print(f"   Timeout: Services did not start within {SERVICE_STARTUP_TIMEOUT}s")
            return False
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_network_connectivity(self) -> bool:
        """Test network connectivity between services"""
        try:
            # Get backend container
            backend_containers = self.client.containers.list(
                filters={"label": "com.docker.compose.service=backend"}
            )
            
            if not backend_containers:
                print("   Error: Backend container not found")
                return False
            
            backend_container = backend_containers[0]
            
            # Test internal network connectivity to ClickHouse
            result = backend_container.exec_run("ping -c 1 clickhouse")
            
            if result.exit_code == 0:
                print("   Internal network connectivity: OK")
                return True
            else:
                print("   Error: Internal network connectivity failed")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_resource_usage(self) -> bool:
        """Test resource usage is within acceptable limits"""
        try:
            total_cpu = 0
            total_memory = 0
            
            for service in REQUIRED_SERVICES:
                containers = self.client.containers.list(
                    filters={"label": f"com.docker.compose.service={service}"}
                )
                
                if containers:
                    container = containers[0]
                    stats = container.stats(stream=False)
                    
                    # Calculate CPU percentage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                               stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                  stats['precpu_stats']['system_cpu_usage']
                    
                    if system_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * 100
                        total_cpu += cpu_percent
                    
                    # Memory usage
                    memory_usage = stats['memory_stats']['usage'] / (1024 * 1024)  # MB
                    total_memory += memory_usage
                    
                    print(f"   {service}: CPU {cpu_percent:.1f}%, Memory {memory_usage:.1f}MB")
            
            # Check if within limits (adjust as needed)
            if total_cpu < 200 and total_memory < 2048:  # 200% CPU, 2GB RAM
                print(f"   Total resource usage: CPU {total_cpu:.1f}%, Memory {total_memory:.1f}MB")
                return True
            else:
                print(f"   Warning: High resource usage - CPU {total_cpu:.1f}%, Memory {total_memory:.1f}MB")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_health_checks(self) -> bool:
        """Test health endpoints of services"""
        health_endpoints = {
            "backend": "http://localhost:8100/health",
            "clickhouse": "http://localhost:8123/ping"
        }
        
        for service, endpoint in health_endpoints.items():
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    print(f"   {service} health check: OK")
                else:
                    print(f"   {service} health check: FAILED (HTTP {response.status_code})")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"   {service} health check: ERROR - {e}")
                return False
        
        return True
    
    def test_service_dependencies(self) -> bool:
        """Test service dependency order"""
        try:
            # ClickHouse should be ready before Backend
            clickhouse_containers = self.client.containers.list(
                filters={"label": "com.docker.compose.service=clickhouse"}
            )
            
            backend_containers = self.client.containers.list(
                filters={"label": "com.docker.compose.service=backend"}
            )
            
            if not clickhouse_containers or not backend_containers:
                print("   Error: Required containers not found")
                return False
            
            # Check if backend can connect to ClickHouse
            backend_container = backend_containers[0]
            result = backend_container.exec_run(
                "python -c \"import requests; print(requests.get('http://clickhouse:8123/ping').status_code)\""
            )
            
            if result.exit_code == 0 and b"200" in result.output:
                print("   Service dependencies: OK")
                return True
            else:
                print("   Error: Backend cannot connect to ClickHouse")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def test_cleanup(self) -> bool:
        """Test cleanup of services"""
        compose_path = os.path.join(os.path.dirname(__file__), DOCKER_COMPOSE_FILE)
        
        try:
            result = subprocess.run(
                ["docker-compose", "-f", compose_path, "down"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(compose_path)
            )
            
            if result.returncode == 0:
                print("   Services cleanup: OK")
                return True
            else:
                print(f"   Error during cleanup: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for r in self.test_results.values() if r['status'] == 'PASS')
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            duration = result.get('duration', 'N/A')
            print(f"{status_icon} {test_name}: {result['status']} ({duration})")
        
        print(f"\nResult: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Docker Compose tests PASSED!")
        else:
            print("⚠️  Some Docker Compose tests FAILED!")


def main():
    """Main test execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python docker_compose_test.py")
        print("Tests Docker Compose services for DarkMa Trading System")
        return
    
    test_suite = DockerComposeTest()
    success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
