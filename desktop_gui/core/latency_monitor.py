"""
DarkMa Trading Desktop GUI - Latency Monitor
============================================

Real-time latency monitoring for trading-critical components:
- Bitget API latency (order execution speed)
- Grid Trading latency (algorithm response time)
- WebSocket latency (real-time update speed)
"""

import asyncio
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal, QTimer
from .config import config_manager


class LatencyLevel(Enum):
    """Latency performance levels."""
    EXCELLENT = "excellent"  # < 20ms
    GOOD = "good"           # 20-50ms
    WARNING = "warning"     # 50-100ms
    CRITICAL = "critical"   # > 100ms
    UNAVAILABLE = "unavailable"


@dataclass
class LatencyMeasurement:
    """Single latency measurement."""
    component: str
    latency_ms: float
    timestamp: datetime
    success: bool = True
    error_message: Optional[str] = None
    
    @property
    def level(self) -> LatencyLevel:
        """Get performance level based on latency."""
        if not self.success:
            return LatencyLevel.UNAVAILABLE
        
        if self.latency_ms < 20:
            return LatencyLevel.EXCELLENT
        elif self.latency_ms < 50:
            return LatencyLevel.GOOD
        elif self.latency_ms < 100:
            return LatencyLevel.WARNING
        else:
            return LatencyLevel.CRITICAL


@dataclass
class LatencyStats:
    """Latency statistics for a component."""
    component: str
    current_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    level: LatencyLevel
    measurement_count: int
    last_updated: datetime
    uptime_percentage: float = 100.0


class LatencyMonitor(QObject):
    """Real-time latency monitoring system."""
    
    # Signals
    measurement_updated = Signal(str, LatencyMeasurement)  # component, measurement
    stats_updated = Signal(str, LatencyStats)  # component, stats
    level_changed = Signal(str, str)  # component, level
    alert_triggered = Signal(str, str, float)  # component, alert_type, value
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.measurement_interval = config_manager.get("latency.measurement_interval", 30)  # seconds
        self.history_retention_hours = config_manager.get("latency.history_retention_hours", 24)
        self.alert_thresholds = {
            "warning": config_manager.get("latency.warning_threshold", 50),
            "critical": config_manager.get("latency.critical_threshold", 100)
        }
        
        # State
        self.measurements: Dict[str, List[LatencyMeasurement]] = {
            "bitget_api": [],
            "grid_trading": [],
            "websocket": []
        }
        self.current_stats: Dict[str, LatencyStats] = {}
        self.is_monitoring = False
        
        # Timers
        self.measurement_timer = QTimer()
        self.measurement_timer.timeout.connect(self.run_measurements)
        
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_measurements)
        self.cleanup_timer.start(3600000)  # Cleanup every hour
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Latency Monitor initialized")
    
    def start_monitoring(self):
        """Start latency monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.measurement_timer.start(self.measurement_interval * 1000)
        
        self.logger.info(f"Latency monitoring started (interval: {self.measurement_interval}s)")
    
    def stop_monitoring(self):
        """Stop latency monitoring."""
        self.is_monitoring = False
        self.measurement_timer.stop()
        
        self.logger.info("Latency monitoring stopped")
    
    def set_measurement_interval(self, seconds: int):
        """Set measurement interval."""
        if seconds < 5 or seconds > 300:  # 5 seconds to 5 minutes
            raise ValueError("Measurement interval must be between 5 and 300 seconds")
        
        self.measurement_interval = seconds
        config_manager.set("latency.measurement_interval", seconds)
        
        if self.is_monitoring:
            self.measurement_timer.start(self.measurement_interval * 1000)
        
        self.logger.info(f"Measurement interval set to {seconds} seconds")
    
    def run_measurements(self):
        """Run all latency measurements."""
        asyncio.create_task(self._async_measurements())
    
    async def _async_measurements(self):
        """Run async latency measurements."""
        try:
            # Run measurements concurrently
            tasks = [
                self.measure_bitget_api(),
                self.measure_grid_trading(),
                self.measure_websocket()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            components = ["bitget_api", "grid_trading", "websocket"]
            for component, result in zip(components, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Measurement error for {component}: {result}")
                    # Record failed measurement
                    measurement = LatencyMeasurement(
                        component=component,
                        latency_ms=0,
                        timestamp=datetime.now(),
                        success=False,
                        error_message=str(result)
                    )
                    self.record_measurement(measurement)
                else:
                    self.record_measurement(result)
            
        except Exception as e:
            self.logger.error(f"Measurement cycle error: {e}")
    
    async def measure_bitget_api(self) -> LatencyMeasurement:
        """Measure Bitget API latency."""
        try:
            start_time = time.time()
            
            # Make a lightweight API call to Bitget
            import aiohttp
            backend_url = config_manager.get("backend.url", "http://localhost:8100")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{backend_url}/api/exchanges/bitget/ping",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    await response.text()
                    
                    if response.status == 200:
                        latency_ms = (time.time() - start_time) * 1000
                        return LatencyMeasurement(
                            component="bitget_api",
                            latency_ms=latency_ms,
                            timestamp=datetime.now(),
                            success=True
                        )
                    else:
                        raise Exception(f"API returned status {response.status}")
                        
        except Exception as e:
            return LatencyMeasurement(
                component="bitget_api",
                latency_ms=0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    async def measure_grid_trading(self) -> LatencyMeasurement:
        """Measure Grid Trading algorithm latency."""
        try:
            start_time = time.time()
            
            # Call grid trading performance endpoint
            import aiohttp
            backend_url = config_manager.get("backend.url", "http://localhost:8100")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{backend_url}/api/trading/grid/performance",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    await response.text()
                    
                    if response.status == 200:
                        latency_ms = (time.time() - start_time) * 1000
                        return LatencyMeasurement(
                            component="grid_trading",
                            latency_ms=latency_ms,
                            timestamp=datetime.now(),
                            success=True
                        )
                    else:
                        raise Exception(f"Grid trading API returned status {response.status}")
                        
        except Exception as e:
            return LatencyMeasurement(
                component="grid_trading",
                latency_ms=0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    async def measure_websocket(self) -> LatencyMeasurement:
        """Measure WebSocket latency."""
        try:
            start_time = time.time()
            
            # Test WebSocket ping-pong
            import websockets
            backend_ws_url = config_manager.get("backend.ws_url", "ws://localhost:8100/ws")
            
            async with websockets.connect(backend_ws_url) as websocket:
                # Send ping
                await websocket.send('{"type": "ping"}')
                
                # Wait for pong
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                latency_ms = (time.time() - start_time) * 1000
                
                return LatencyMeasurement(
                    component="websocket",
                    latency_ms=latency_ms,
                    timestamp=datetime.now(),
                    success=True
                )
                
        except Exception as e:
            return LatencyMeasurement(
                component="websocket",
                latency_ms=0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    def record_measurement(self, measurement: LatencyMeasurement):
        """Record a latency measurement."""
        component = measurement.component
        
        # Add to measurements
        if component not in self.measurements:
            self.measurements[component] = []
        
        self.measurements[component].append(measurement)
        
        # Update statistics
        self.update_stats(component)
        
        # Emit signals
        self.measurement_updated.emit(component, measurement)
        
        # Check for alerts
        self.check_alerts(measurement)
    
    def update_stats(self, component: str):
        """Update statistics for a component."""
        measurements = self.measurements.get(component, [])
        if not measurements:
            return
        
        # Filter recent successful measurements (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_measurements = [
            m for m in measurements 
            if m.timestamp >= cutoff_time and m.success
        ]
        
        if not recent_measurements:
            # No recent successful measurements
            stats = LatencyStats(
                component=component,
                current_ms=0,
                avg_ms=0,
                min_ms=0,
                max_ms=0,
                level=LatencyLevel.UNAVAILABLE,
                measurement_count=0,
                last_updated=datetime.now(),
                uptime_percentage=0.0
            )
        else:
            # Calculate statistics
            latencies = [m.latency_ms for m in recent_measurements]
            current_latency = measurements[-1].latency_ms if measurements[-1].success else 0
            
            # Calculate uptime
            total_recent = len([m for m in measurements if m.timestamp >= cutoff_time])
            successful_recent = len(recent_measurements)
            uptime_percentage = (successful_recent / total_recent * 100) if total_recent > 0 else 0
            
            stats = LatencyStats(
                component=component,
                current_ms=current_latency,
                avg_ms=statistics.mean(latencies),
                min_ms=min(latencies),
                max_ms=max(latencies),
                level=measurements[-1].level,
                measurement_count=len(recent_measurements),
                last_updated=datetime.now(),
                uptime_percentage=uptime_percentage
            )
        
        # Check if level changed
        old_level = self.current_stats.get(component, {}).get("level")
        if old_level != stats.level:
            self.level_changed.emit(component, stats.level.value)
        
        self.current_stats[component] = stats
        self.stats_updated.emit(component, stats)
    
    def check_alerts(self, measurement: LatencyMeasurement):
        """Check if measurement triggers any alerts."""
        if not measurement.success:
            self.alert_triggered.emit(
                measurement.component, 
                "unavailable", 
                0
            )
            return
        
        # Check thresholds
        if measurement.latency_ms >= self.alert_thresholds["critical"]:
            self.alert_triggered.emit(
                measurement.component,
                "critical",
                measurement.latency_ms
            )
        elif measurement.latency_ms >= self.alert_thresholds["warning"]:
            self.alert_triggered.emit(
                measurement.component,
                "warning", 
                measurement.latency_ms
            )
    
    def get_current_stats(self) -> Dict[str, LatencyStats]:
        """Get current latency statistics."""
        return self.current_stats.copy()
    
    def get_component_stats(self, component: str) -> Optional[LatencyStats]:
        """Get statistics for a specific component."""
        return self.current_stats.get(component)
    
    def get_measurement_history(self, component: str, hours: int = 1) -> List[LatencyMeasurement]:
        """Get measurement history for a component."""
        if component not in self.measurements:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            m for m in self.measurements[component]
            if m.timestamp >= cutoff_time
        ]
    
    def cleanup_old_measurements(self):
        """Clean up old measurements."""
        cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)
        
        for component in self.measurements:
            old_count = len(self.measurements[component])
            self.measurements[component] = [
                m for m in self.measurements[component]
                if m.timestamp >= cutoff_time
            ]
            new_count = len(self.measurements[component])
            
            if old_count != new_count:
                self.logger.debug(f"Cleaned up {old_count - new_count} old measurements for {component}")
    
    def get_overall_status(self) -> LatencyLevel:
        """Get overall latency status."""
        if not self.current_stats:
            return LatencyLevel.UNAVAILABLE
        
        # Find worst level among all components
        levels = [stats.level for stats in self.current_stats.values()]
        
        if LatencyLevel.CRITICAL in levels:
            return LatencyLevel.CRITICAL
        elif LatencyLevel.WARNING in levels:
            return LatencyLevel.WARNING
        elif LatencyLevel.UNAVAILABLE in levels:
            return LatencyLevel.UNAVAILABLE
        elif LatencyLevel.GOOD in levels:
            return LatencyLevel.GOOD
        else:
            return LatencyLevel.EXCELLENT
    
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        return {
            "is_monitoring": self.is_monitoring,
            "measurement_interval": self.measurement_interval,
            "components": {
                component: {
                    "current_ms": stats.current_ms,
                    "level": stats.level.value,
                    "uptime_percentage": stats.uptime_percentage,
                    "last_updated": stats.last_updated.isoformat()
                }
                for component, stats in self.current_stats.items()
            },
            "overall_status": self.get_overall_status().value,
            "alert_thresholds": self.alert_thresholds
        }


# Global latency monitor instance
latency_monitor = LatencyMonitor()
