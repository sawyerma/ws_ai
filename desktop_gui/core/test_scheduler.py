"""
DarkMa Trading Desktop GUI - Test Scheduler
==========================================

Automated test execution scheduler that runs system tests at regular intervals.
Provides configurable test cycles and boot-time test validation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from PySide6.QtCore import QObject, Signal, QTimer
from .config import config_manager
from .test_manager import test_manager, TestStatus


class TestScheduler(QObject):
    """Automated test execution scheduler."""
    
    # Signals
    boot_tests_started = Signal()
    boot_tests_completed = Signal(bool)  # success
    scheduled_tests_started = Signal()
    scheduled_tests_completed = Signal(dict)  # summary
    next_test_time_changed = Signal(datetime)  # next scheduled test time
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.test_interval_minutes = config_manager.get("testing.interval_minutes", 10)
        self.boot_tests_enabled = config_manager.get("testing.boot_tests_enabled", True)
        self.auto_tests_enabled = config_manager.get("testing.auto_tests_enabled", True)
        
        # State
        self.last_test_time: Optional[datetime] = None
        self.next_test_time: Optional[datetime] = None
        self.boot_tests_completed = False
        self.is_testing = False
        
        # Timers
        self.scheduler_timer = QTimer()
        self.scheduler_timer.timeout.connect(self.check_scheduled_tests)
        self.scheduler_timer.start(30000)  # Check every 30 seconds
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Connect to test manager
        test_manager.test_cycle_completed.connect(self.on_test_cycle_completed)
        test_manager.status_changed.connect(self.on_test_status_changed)
        
        # Initialize next test time
        self.update_next_test_time()
        
        self.logger.info("Test Scheduler initialized")
    
    def set_test_interval(self, minutes: int):
        """Set test interval in minutes."""
        if minutes < 1 or minutes > 1440:  # Max 24 hours
            raise ValueError("Test interval must be between 1 and 1440 minutes")
        
        self.test_interval_minutes = minutes
        config_manager.set("testing.interval_minutes", minutes)
        
        self.update_next_test_time()
        self.logger.info(f"Test interval set to {minutes} minutes")
    
    def enable_auto_tests(self, enabled: bool):
        """Enable or disable automatic tests."""
        self.auto_tests_enabled = enabled
        config_manager.set("testing.auto_tests_enabled", enabled)
        
        if enabled:
            self.update_next_test_time()
        else:
            self.next_test_time = None
            self.next_test_time_changed.emit(datetime.now())
        
        self.logger.info(f"Auto tests {'enabled' if enabled else 'disabled'}")
    
    def enable_boot_tests(self, enabled: bool):
        """Enable or disable boot tests."""
        self.boot_tests_enabled = enabled
        config_manager.set("testing.boot_tests_enabled", enabled)
        
        self.logger.info(f"Boot tests {'enabled' if enabled else 'disabled'}")
    
    def update_next_test_time(self):
        """Update next scheduled test time."""
        if not self.auto_tests_enabled:
            self.next_test_time = None
            return
        
        if self.last_test_time:
            self.next_test_time = self.last_test_time + timedelta(minutes=self.test_interval_minutes)
        else:
            # First test after startup
            self.next_test_time = datetime.now() + timedelta(minutes=self.test_interval_minutes)
        
        self.next_test_time_changed.emit(self.next_test_time)
        self.logger.debug(f"Next test scheduled for: {self.next_test_time}")
    
    def check_scheduled_tests(self):
        """Check if it's time to run scheduled tests."""
        if not self.auto_tests_enabled or self.is_testing:
            return
        
        if not self.next_test_time:
            self.update_next_test_time()
            return
        
        now = datetime.now()
        
        # Check if it's time for the next test
        if now >= self.next_test_time:
            self.logger.info("Starting scheduled test cycle")
            asyncio.create_task(self.run_scheduled_tests())
    
    async def run_boot_tests(self) -> bool:
        """Run boot-time validation tests."""
        if not self.boot_tests_enabled:
            self.logger.info("Boot tests disabled, skipping")
            return True
        
        self.logger.info("Starting boot tests")
        self.boot_tests_started.emit()
        
        try:
            # Run critical tests only for boot
            critical_tests = [
                "docker_compose",
                "clickhouse", 
                "health_endpoints",
                "websocket_core"
            ]
            
            results = await test_manager.run_test_cycle(critical_tests)
            
            # Check if all critical tests passed
            success = all(
                result.status == TestStatus.PASSED 
                for result in results.values()
            )
            
            if success:
                self.logger.info("Boot tests completed successfully")
                self.boot_tests_completed = True
                self.last_test_time = datetime.now()
                self.update_next_test_time()
            else:
                failed_tests = [
                    result.test_name for result in results.values() 
                    if result.status != TestStatus.PASSED
                ]
                self.logger.error(f"Boot tests failed: {', '.join(failed_tests)}")
            
            self.boot_tests_completed.emit(success)
            return success
            
        except Exception as e:
            self.logger.error(f"Boot tests error: {e}")
            self.boot_tests_completed.emit(False)
            return False
    
    async def run_scheduled_tests(self):
        """Run scheduled test cycle."""
        if self.is_testing:
            self.logger.warning("Test cycle already running, skipping scheduled tests")
            return
        
        self.is_testing = True
        self.scheduled_tests_started.emit()
        
        try:
            self.logger.info("Starting scheduled test cycle")
            
            # Run all available tests
            results = await test_manager.run_test_cycle()
            
            # Update timing
            self.last_test_time = datetime.now()
            self.update_next_test_time()
            
            # Create summary
            summary = test_manager.create_test_summary(results)
            summary["test_type"] = "scheduled"
            summary["next_test_time"] = self.next_test_time.isoformat() if self.next_test_time else None
            
            self.scheduled_tests_completed.emit(summary)
            
            self.logger.info(f"Scheduled tests completed: {summary['passed']}/{summary['total']} passed")
            
        except Exception as e:
            self.logger.error(f"Scheduled tests error: {e}")
            
        finally:
            self.is_testing = False
    
    async def run_manual_tests(self, test_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run tests manually (triggered by user)."""
        if self.is_testing:
            self.logger.warning("Test cycle already running")
            return {}
        
        self.is_testing = True
        
        try:
            self.logger.info("Starting manual test cycle")
            
            results = await test_manager.run_test_cycle(test_ids)
            
            # Update last test time only if it was a full test cycle
            if not test_ids:
                self.last_test_time = datetime.now()
                self.update_next_test_time()
            
            summary = test_manager.create_test_summary(results)
            summary["test_type"] = "manual"
            
            self.logger.info(f"Manual tests completed: {summary['passed']}/{summary['total']} passed")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Manual tests error: {e}")
            return {}
            
        finally:
            self.is_testing = False
    
    def on_test_cycle_completed(self, summary: dict):
        """Handle test cycle completion."""
        # Log test cycle results
        status = summary.get("overall_status", "unknown")
        passed = summary.get("passed", 0)
        total = summary.get("total", 0)
        
        self.logger.info(f"Test cycle completed - Status: {status}, Passed: {passed}/{total}")
    
    def on_test_status_changed(self, status: str):
        """Handle overall test status change."""
        self.logger.info(f"Overall test status changed to: {status}")
    
    def get_time_until_next_test(self) -> Optional[timedelta]:
        """Get time remaining until next test."""
        if not self.next_test_time or not self.auto_tests_enabled:
            return None
        
        now = datetime.now()
        if now >= self.next_test_time:
            return timedelta(0)
        
        return self.next_test_time - now
    
    def get_time_since_last_test(self) -> Optional[timedelta]:
        """Get time since last test."""
        if not self.last_test_time:
            return None
        
        return datetime.now() - self.last_test_time
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get scheduler status summary."""
        time_until_next = self.get_time_until_next_test()
        time_since_last = self.get_time_since_last_test()
        
        return {
            "auto_tests_enabled": self.auto_tests_enabled,
            "boot_tests_enabled": self.boot_tests_enabled,
            "boot_tests_completed": self.boot_tests_completed,
            "test_interval_minutes": self.test_interval_minutes,
            "is_testing": self.is_testing,
            "last_test_time": self.last_test_time.isoformat() if self.last_test_time else None,
            "next_test_time": self.next_test_time.isoformat() if self.next_test_time else None,
            "time_until_next_minutes": time_until_next.total_seconds() / 60 if time_until_next else None,
            "time_since_last_minutes": time_since_last.total_seconds() / 60 if time_since_last else None,
            "overall_status": test_manager.overall_status.value
        }
    
    def force_next_test(self):
        """Force the next test to run immediately."""
        if self.is_testing:
            self.logger.warning("Cannot force test - already running")
            return
        
        self.logger.info("Forcing next test cycle")
        self.next_test_time = datetime.now()
        asyncio.create_task(self.run_scheduled_tests())
    
    def reset_test_schedule(self):
        """Reset test schedule to start fresh."""
        self.last_test_time = None
        self.update_next_test_time()
        self.logger.info("Test schedule reset")
    
    def stop_scheduler(self):
        """Stop the test scheduler."""
        self.scheduler_timer.stop()
        self.auto_tests_enabled = False
        self.logger.info("Test scheduler stopped")
    
    def start_scheduler(self):
        """Start the test scheduler."""
        if not self.scheduler_timer.isActive():
            self.scheduler_timer.start(30000)
        self.auto_tests_enabled = True
        self.update_next_test_time()
        self.logger.info("Test scheduler started")


# Global test scheduler instance
test_scheduler = TestScheduler()
