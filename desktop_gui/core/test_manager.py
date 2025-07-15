"""
DarkMa Trading Desktop GUI - Test Manager
========================================

Orchestrates all system tests and manages test execution lifecycle.
Provides centralized test management for Infrastructure, Backend API, and Trading components.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer
from .config import config_manager


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class TestType(Enum):
    """Test category types."""
    INFRASTRUCTURE = "infrastructure"
    BACKEND_API = "backend_api"
    WEBSOCKET = "websocket"
    LATENCY = "latency"
    CONCURRENT = "concurrent"
    BITGET_API = "bitget_api"
    DOCKER_SERVICES = "docker_services"


@dataclass
class TestResult:
    """Test execution result."""
    test_id: str
    test_name: str
    test_type: TestType
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration * 1000
    
    @property
    def is_completed(self) -> bool:
        """Check if test is completed."""
        return self.status in [TestStatus.PASSED, TestStatus.FAILED, 
                              TestStatus.WARNING, TestStatus.TIMEOUT, TestStatus.SKIPPED]


class TestManager(QObject):
    """Central test management system."""
    
    # Signals
    test_started = Signal(str, str)  # test_id, test_name
    test_completed = Signal(TestResult)
    test_cycle_started = Signal()
    test_cycle_completed = Signal(dict)  # summary stats
    status_changed = Signal(str)  # overall status: passed/warning/failed
    
    def __init__(self):
        super().__init__()
        
        # Test configuration
        self.test_timeout = config_manager.get("testing.timeout", 120)  # seconds
        self.max_concurrent_tests = config_manager.get("testing.max_concurrent", 5)
        
        # Test state
        self.current_tests: Dict[str, TestResult] = {}
        self.test_history: List[TestResult] = []
        self.last_cycle_results: Dict[str, TestResult] = {}
        self.overall_status = TestStatus.PENDING
        
        # Test runners
        self.active_runners: Dict[str, asyncio.Task] = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load test history from file
        self.load_test_history()
    
    def get_test_definitions(self) -> Dict[str, Dict]:
        """Get all available test definitions."""
        return {
            # Infrastructure Tests
            "docker_compose": {
                "name": "Docker Compose Services",
                "type": TestType.INFRASTRUCTURE,
                "command": "python test/01_infrastructure/docker_compose_test.py",
                "timeout": 60,
                "critical": True
            },
            "clickhouse": {
                "name": "ClickHouse Database",
                "type": TestType.INFRASTRUCTURE,
                "command": "python test/01_infrastructure/clickhouse_connection_test.py",
                "timeout": 30,
                "critical": True
            },
            
            # Backend API Tests
            "health_endpoints": {
                "name": "Health Endpoints",
                "type": TestType.BACKEND_API,
                "command": "bash test/02_backend_api/health_endpoints.sh",
                "timeout": 30,
                "critical": True
            },
            "websocket_core": {
                "name": "WebSocket Core",
                "type": TestType.WEBSOCKET,
                "command": "python test/02_backend_api/websocket_core_tests.py",
                "timeout": 60,
                "critical": True
            },
            "latency_tests": {
                "name": "Latency Performance",
                "type": TestType.LATENCY,
                "command": "python test/02_backend_api/latency_tests.py",
                "timeout": 90,
                "critical": True
            },
            "concurrent_connections": {
                "name": "Concurrent Connections",
                "type": TestType.CONCURRENT,
                "command": "python test/02_backend_api/concurrent_connections_test.py",
                "timeout": 120,
                "critical": True
            },
            
            # Bitget API Tests (to be implemented)
            "bitget_connectivity": {
                "name": "Bitget API Connectivity",
                "type": TestType.BITGET_API,
                "command": "python test/02_backend_api/bitget_api_tests.py",
                "timeout": 30,
                "critical": True
            },
            "bitget_latency": {
                "name": "Bitget API Latency",
                "type": TestType.BITGET_API,
                "command": "python test/02_backend_api/bitget_latency_test.py",
                "timeout": 30,
                "critical": True
            }
        }
    
    async def run_single_test(self, test_id: str) -> TestResult:
        """Run a single test."""
        test_definitions = self.get_test_definitions()
        
        if test_id not in test_definitions:
            raise ValueError(f"Unknown test: {test_id}")
        
        test_def = test_definitions[test_id]
        
        # Create test result
        result = TestResult(
            test_id=test_id,
            test_name=test_def["name"],
            test_type=test_def["type"],
            status=TestStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self.current_tests[test_id] = result
        self.test_started.emit(test_id, test_def["name"])
        
        try:
            self.logger.info(f"Starting test: {test_def['name']}")
            
            # Run test command
            start_time = time.time()
            
            # Simulate test execution (replace with actual subprocess call)
            process = await asyncio.create_subprocess_shell(
                test_def["command"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=test_def.get("timeout", self.test_timeout)
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Determine test result
                if process.returncode == 0:
                    result.status = TestStatus.PASSED
                    self.logger.info(f"Test passed: {test_def['name']} ({duration:.2f}s)")
                else:
                    result.status = TestStatus.FAILED
                    result.error_message = stderr.decode() if stderr else "Test failed with non-zero exit code"
                    self.logger.error(f"Test failed: {test_def['name']} - {result.error_message}")
                
                # Store output details
                result.details = {
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "exit_code": process.returncode,
                    "command": test_def["command"]
                }
                
            except asyncio.TimeoutError:
                result.status = TestStatus.TIMEOUT
                result.error_message = f"Test timed out after {test_def.get('timeout', self.test_timeout)} seconds"
                self.logger.error(f"Test timeout: {test_def['name']}")
                
                # Kill the process
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                
                duration = test_def.get("timeout", self.test_timeout)
                
        except Exception as e:
            result.status = TestStatus.FAILED
            result.error_message = str(e)
            duration = time.time() - start_time
            self.logger.error(f"Test error: {test_def['name']} - {e}")
        
        # Finalize result
        result.end_time = datetime.now()
        result.duration = duration
        
        # Update state
        self.current_tests.pop(test_id, None)
        self.last_cycle_results[test_id] = result
        self.test_history.append(result)
        
        # Emit completion signal
        self.test_completed.emit(result)
        
        return result
    
    async def run_test_cycle(self, test_ids: Optional[List[str]] = None) -> Dict[str, TestResult]:
        """Run a complete test cycle."""
        if test_ids is None:
            test_ids = list(self.get_test_definitions().keys())
        
        self.logger.info(f"Starting test cycle with {len(test_ids)} tests")
        self.test_cycle_started.emit()
        
        results = {}
        
        try:
            # Run tests (can be sequential or parallel based on config)
            if config_manager.get("testing.parallel_execution", False):
                # Parallel execution
                tasks = []
                for test_id in test_ids:
                    task = asyncio.create_task(self.run_single_test(test_id))
                    tasks.append((test_id, task))
                    self.active_runners[test_id] = task
                
                # Wait for all tests with timeout
                for test_id, task in tasks:
                    try:
                        result = await task
                        results[test_id] = result
                    except Exception as e:
                        self.logger.error(f"Test task error for {test_id}: {e}")
                    finally:
                        self.active_runners.pop(test_id, None)
            else:
                # Sequential execution
                for test_id in test_ids:
                    try:
                        result = await self.run_single_test(test_id)
                        results[test_id] = result
                    except Exception as e:
                        self.logger.error(f"Test execution error for {test_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Test cycle error: {e}")
        
        # Calculate overall status
        self.update_overall_status(results)
        
        # Create summary
        summary = self.create_test_summary(results)
        
        self.logger.info(f"Test cycle completed: {summary['passed']}/{summary['total']} passed")
        self.test_cycle_completed.emit(summary)
        
        # Save history
        self.save_test_history()
        
        return results
    
    def update_overall_status(self, results: Dict[str, TestResult]):
        """Update overall system status based on test results."""
        if not results:
            self.overall_status = TestStatus.PENDING
            self.status_changed.emit("pending")
            return
        
        # Count status types
        passed = sum(1 for r in results.values() if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results.values() if r.status in [TestStatus.FAILED, TestStatus.TIMEOUT])
        warnings = sum(1 for r in results.values() if r.status == TestStatus.WARNING)
        
        # Determine overall status
        if failed > 0:
            self.overall_status = TestStatus.FAILED
            status_str = "failed"
        elif warnings > 0:
            self.overall_status = TestStatus.WARNING
            status_str = "warning"
        elif passed == len(results):
            self.overall_status = TestStatus.PASSED
            status_str = "passed"
        else:
            self.overall_status = TestStatus.PENDING
            status_str = "pending"
        
        self.status_changed.emit(status_str)
    
    def create_test_summary(self, results: Dict[str, TestResult]) -> Dict[str, Any]:
        """Create test cycle summary."""
        total = len(results)
        passed = sum(1 for r in results.values() if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results.values() if r.status in [TestStatus.FAILED, TestStatus.TIMEOUT])
        warnings = sum(1 for r in results.values() if r.status == TestStatus.WARNING)
        skipped = sum(1 for r in results.values() if r.status == TestStatus.SKIPPED)
        
        # Calculate average duration
        completed_results = [r for r in results.values() if r.is_completed]
        avg_duration = sum(r.duration for r in completed_results) / len(completed_results) if completed_results else 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "skipped": skipped,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "avg_duration": avg_duration,
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.overall_status.value
        }
    
    def get_test_history(self, limit: Optional[int] = None, 
                        status_filter: Optional[TestStatus] = None,
                        test_type_filter: Optional[TestType] = None) -> List[TestResult]:
        """Get test history with optional filtering."""
        history = self.test_history.copy()
        
        # Apply filters
        if status_filter:
            history = [r for r in history if r.status == status_filter]
        
        if test_type_filter:
            history = [r for r in history if r.test_type == test_type_filter]
        
        # Sort by start time (newest first)
        history.sort(key=lambda r: r.start_time, reverse=True)
        
        # Apply limit
        if limit:
            history = history[:limit]
        
        return history
    
    def get_latest_results(self) -> Dict[str, TestResult]:
        """Get latest test cycle results."""
        return self.last_cycle_results.copy()
    
    def clear_history(self):
        """Clear test history."""
        self.test_history.clear()
        self.save_test_history()
    
    def save_test_history(self):
        """Save test history to file."""
        try:
            import json
            from pathlib import Path
            
            # Create data directory
            data_dir = Path.home() / ".darkma" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert history to serializable format
            history_data = []
            for result in self.test_history[-1000:]:  # Keep last 1000 results
                history_data.append({
                    "test_id": result.test_id,
                    "test_name": result.test_name,
                    "test_type": result.test_type.value,
                    "status": result.status.value,
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat() if result.end_time else None,
                    "duration": result.duration,
                    "error_message": result.error_message,
                    "details": result.details
                })
            
            # Save to file
            history_file = data_dir / "test_history.json"
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save test history: {e}")
    
    def load_test_history(self):
        """Load test history from file."""
        try:
            import json
            from pathlib import Path
            
            history_file = Path.home() / ".darkma" / "data" / "test_history.json"
            
            if not history_file.exists():
                return
            
            with open(history_file, 'r') as f:
                history_data = json.load(f)
            
            # Convert back to TestResult objects
            self.test_history = []
            for item in history_data:
                result = TestResult(
                    test_id=item["test_id"],
                    test_name=item["test_name"],
                    test_type=TestType(item["test_type"]),
                    status=TestStatus(item["status"]),
                    start_time=datetime.fromisoformat(item["start_time"]),
                    end_time=datetime.fromisoformat(item["end_time"]) if item["end_time"] else None,
                    duration=item["duration"],
                    error_message=item["error_message"],
                    details=item["details"] or {}
                )
                self.test_history.append(result)
                
        except Exception as e:
            self.logger.error(f"Failed to load test history: {e}")
    
    def cancel_running_tests(self):
        """Cancel all running tests."""
        for test_id, task in self.active_runners.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"Cancelled test: {test_id}")
        
        self.active_runners.clear()
        self.current_tests.clear()


# Global test manager instance
test_manager = TestManager()
