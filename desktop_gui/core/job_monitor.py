"""
DarkMa Trading Desktop GUI - Job Monitor
=======================================

Monitors running trading jobs and their status:
- Whale Detection
- Elliott Wave Analysis
- Grid Trading
- Sentiment Analysis
- And other trading algorithms
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal, QTimer
from .config import config_manager


class JobStatus(Enum):
    """Job execution status."""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class JobInfo:
    """Information about a running job."""
    job_id: str
    name: str
    job_type: str
    status: JobStatus
    start_time: datetime
    last_update: datetime
    runtime_seconds: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    @property
    def runtime_formatted(self) -> str:
        """Get formatted runtime string."""
        if self.runtime_seconds < 60:
            return f"{self.runtime_seconds}s"
        elif self.runtime_seconds < 3600:
            minutes = self.runtime_seconds // 60
            return f"{minutes}min"
        else:
            hours = self.runtime_seconds // 3600
            minutes = (self.runtime_seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}h {minutes}min"
            else:
                return f"{hours}h"
    
    @property
    def status_color(self) -> str:
        """Get status indicator color."""
        if self.status == JobStatus.RUNNING:
            return "green"
        elif self.status == JobStatus.PAUSED:
            return "orange"
        elif self.status == JobStatus.ERROR:
            return "red"
        else:
            return "gray"


class JobMonitor(QObject):
    """Trading job monitoring system."""
    
    # Signals
    job_discovered = Signal(JobInfo)
    job_updated = Signal(JobInfo)
    job_removed = Signal(str)  # job_id
    status_changed = Signal(str, str)  # job_id, status
    jobs_refreshed = Signal(list)  # list of JobInfo
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.refresh_interval = config_manager.get("jobs.refresh_interval", 30)  # seconds
        self.backend_url = config_manager.get("backend.url", "http://localhost:8100")
        
        # State
        self.jobs: Dict[str, JobInfo] = {}
        self.is_monitoring = False
        
        # Timers
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_jobs)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Job Monitor initialized")
    
    def start_monitoring(self):
        """Start job monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.refresh_timer.start(self.refresh_interval * 1000)
        
        # Initial refresh (use sync method)
        self.refresh_jobs()
        
        self.logger.info(f"Job monitoring started (refresh interval: {self.refresh_interval}s)")
    
    def stop_monitoring(self):
        """Stop job monitoring."""
        self.is_monitoring = False
        self.refresh_timer.stop()
        
        self.logger.info("Job monitoring stopped")
    
    def set_refresh_interval(self, seconds: int):
        """Set refresh interval."""
        if seconds < 5 or seconds > 300:  # 5 seconds to 5 minutes
            raise ValueError("Refresh interval must be between 5 and 300 seconds")
        
        self.refresh_interval = seconds
        config_manager.set("jobs.refresh_interval", seconds)
        
        if self.is_monitoring:
            self.refresh_timer.start(self.refresh_interval * 1000)
        
        self.logger.info(f"Job refresh interval set to {seconds} seconds")
    
    def refresh_jobs(self):
        """Refresh job information (sync wrapper)."""
        try:
            # Use QTimer for non-blocking operation
            QTimer.singleShot(0, self._do_refresh_jobs)
        except Exception as e:
            self.logger.error(f"Error scheduling job refresh: {e}")
    
    def _do_refresh_jobs(self):
        """Internal job refresh method."""
        try:
            # For now, use mock data since async is problematic in GUI context
            jobs_data = self.get_mock_jobs()
            self._process_jobs_data(jobs_data)
        except Exception as e:
            self.logger.error(f"Error refreshing jobs: {e}")
    
    def _process_jobs_data(self, jobs_data: List[Dict[str, Any]]):
        """Process jobs data and update internal state."""
        try:
            # Update job information
            current_job_ids = set(self.jobs.keys())
            new_job_ids = set()
            
            for job_data in jobs_data:
                job_id = job_data["id"]
                new_job_ids.add(job_id)
                
                # Create or update job info
                if job_id in self.jobs:
                    # Update existing job
                    job_info = self.jobs[job_id]
                    old_status = job_info.status
                    
                    # Update fields
                    job_info.status = JobStatus(job_data["status"])
                    job_info.last_update = datetime.now()
                    job_info.runtime_seconds = job_data.get("runtime_seconds", 0)
                    job_info.cpu_usage = job_data.get("cpu_usage", 0.0)
                    job_info.memory_usage = job_data.get("memory_usage", 0.0)
                    job_info.error_message = job_data.get("error_message")
                    job_info.details = job_data.get("details", {})
                    
                    # Emit signals if status changed
                    if old_status != job_info.status:
                        self.status_changed.emit(job_id, job_info.status.value)
                    
                    self.job_updated.emit(job_info)
                    
                else:
                    # New job discovered
                    job_info = JobInfo(
                        job_id=job_id,
                        name=job_data["name"],
                        job_type=job_data.get("type", "unknown"),
                        status=JobStatus(job_data["status"]),
                        start_time=datetime.fromisoformat(job_data["start_time"]) if job_data.get("start_time") else datetime.now(),
                        last_update=datetime.now(),
                        runtime_seconds=job_data.get("runtime_seconds", 0),
                        cpu_usage=job_data.get("cpu_usage", 0.0),
                        memory_usage=job_data.get("memory_usage", 0.0),
                        error_message=job_data.get("error_message"),
                        details=job_data.get("details", {})
                    )
                    
                    self.jobs[job_id] = job_info
                    self.job_discovered.emit(job_info)
            
            # Remove jobs that are no longer present
            removed_jobs = current_job_ids - new_job_ids
            for job_id in removed_jobs:
                self.jobs.pop(job_id, None)
                self.job_removed.emit(job_id)
            
            # Emit refresh signal
            self.jobs_refreshed.emit(list(self.jobs.values()))
            
        except Exception as e:
            self.logger.error(f"Error processing jobs data: {e}")
    
    async def refresh_jobs_async(self):
        """Async job refresh."""
        try:
            # Get job information from backend
            jobs_data = await self.fetch_jobs_from_backend()
            
            # Update job information
            current_job_ids = set(self.jobs.keys())
            new_job_ids = set()
            
            for job_data in jobs_data:
                job_id = job_data["id"]
                new_job_ids.add(job_id)
                
                # Create or update job info
                if job_id in self.jobs:
                    # Update existing job
                    job_info = self.jobs[job_id]
                    old_status = job_info.status
                    
                    # Update fields
                    job_info.status = JobStatus(job_data["status"])
                    job_info.last_update = datetime.now()
                    job_info.runtime_seconds = job_data.get("runtime_seconds", 0)
                    job_info.cpu_usage = job_data.get("cpu_usage", 0.0)
                    job_info.memory_usage = job_data.get("memory_usage", 0.0)
                    job_info.error_message = job_data.get("error_message")
                    job_info.details = job_data.get("details", {})
                    
                    # Emit signals if status changed
                    if old_status != job_info.status:
                        self.status_changed.emit(job_id, job_info.status.value)
                    
                    self.job_updated.emit(job_info)
                    
                else:
                    # New job discovered
                    job_info = JobInfo(
                        job_id=job_id,
                        name=job_data["name"],
                        job_type=job_data.get("type", "unknown"),
                        status=JobStatus(job_data["status"]),
                        start_time=datetime.fromisoformat(job_data["start_time"]) if job_data.get("start_time") else datetime.now(),
                        last_update=datetime.now(),
                        runtime_seconds=job_data.get("runtime_seconds", 0),
                        cpu_usage=job_data.get("cpu_usage", 0.0),
                        memory_usage=job_data.get("memory_usage", 0.0),
                        error_message=job_data.get("error_message"),
                        details=job_data.get("details", {})
                    )
                    
                    self.jobs[job_id] = job_info
                    self.job_discovered.emit(job_info)
            
            # Remove jobs that are no longer present
            removed_jobs = current_job_ids - new_job_ids
            for job_id in removed_jobs:
                self.jobs.pop(job_id, None)
                self.job_removed.emit(job_id)
            
            # Emit refresh signal
            self.jobs_refreshed.emit(list(self.jobs.values()))
            
        except Exception as e:
            self.logger.error(f"Job refresh error: {e}")
    
    async def fetch_jobs_from_backend(self) -> List[Dict[str, Any]]:
        """Fetch job information from backend."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/jobs/status",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data.get("jobs", [])
                    else:
                        self.logger.warning(f"Jobs API returned status {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.debug(f"Failed to fetch jobs from backend: {e}")
            # Return mock data for development
            return self.get_mock_jobs()
    
    def get_mock_jobs(self) -> List[Dict[str, Any]]:
        """Get mock job data for development."""
        now = datetime.now()
        
        mock_jobs = [
            {
                "id": "whale_detection_001",
                "name": "Whale Detection",
                "type": "market_analysis",
                "status": "running",
                "start_time": (now - timedelta(hours=2, minutes=15)).isoformat(),
                "runtime_seconds": 8100,  # 2h 15min
                "cpu_usage": 14.2,
                "memory_usage": 412.0,
                "details": {
                    "symbol": "BTCUSDT",
                    "whale_threshold": 100,
                    "detected_whales": 5
                }
            },
            {
                "id": "elliott_wave_001",
                "name": "Elliott Wave Analysis",
                "type": "technical_analysis",
                "status": "running",
                "start_time": (now - timedelta(minutes=45)).isoformat(),
                "runtime_seconds": 2700,  # 45 min
                "cpu_usage": 8.7,
                "memory_usage": 287.0,
                "details": {
                    "symbol": "BTCUSDT",
                    "wave_degree": 3,
                    "pattern_confidence": 78.5
                }
            },
            {
                "id": "grid_trading_btcusdt_001",
                "name": "Grid Trading BTCUSDT",
                "type": "automated_trading",
                "status": "paused",
                "start_time": (now - timedelta(minutes=12)).isoformat(),
                "runtime_seconds": 720,  # 12 min
                "cpu_usage": 6.3,
                "memory_usage": 521.0,
                "error_message": "Market volatility exceeded threshold",
                "details": {
                    "symbol": "BTCUSDT",
                    "grid_levels": 20,
                    "total_orders": 15,
                    "filled_orders": 8,
                    "profit_usd": 45.67
                }
            },
            {
                "id": "sentiment_analysis_001",
                "name": "Sentiment Analysis",
                "type": "nlp_processing",
                "status": "stopped",
                "start_time": (now - timedelta(days=5)).isoformat(),
                "runtime_seconds": 0,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "details": {
                    "sources": ["twitter", "reddit", "news"],
                    "languages": ["en", "de"],
                    "last_analysis": "2024-01-15T10:30:00"
                }
            }
        ]
        
        return mock_jobs
    
    def get_jobs(self) -> List[JobInfo]:
        """Get all monitored jobs."""
        return list(self.jobs.values())
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get specific job by ID."""
        return self.jobs.get(job_id)
    
    def get_running_jobs(self) -> List[JobInfo]:
        """Get only running jobs."""
        return [job for job in self.jobs.values() if job.status == JobStatus.RUNNING]
    
    def get_jobs_by_status(self, status: JobStatus) -> List[JobInfo]:
        """Get jobs by status."""
        return [job for job in self.jobs.values() if job.status == status]
    
    def get_jobs_summary(self) -> Dict[str, Any]:
        """Get jobs summary statistics."""
        jobs = list(self.jobs.values())
        
        return {
            "total": len(jobs),
            "running": len([j for j in jobs if j.status == JobStatus.RUNNING]),
            "stopped": len([j for j in jobs if j.status == JobStatus.STOPPED]),
            "paused": len([j for j in jobs if j.status == JobStatus.PAUSED]),
            "error": len([j for j in jobs if j.status == JobStatus.ERROR]),
            "total_cpu_usage": sum(j.cpu_usage for j in jobs if j.status == JobStatus.RUNNING),
            "total_memory_usage": sum(j.memory_usage for j in jobs if j.status == JobStatus.RUNNING),
            "last_updated": datetime.now().isoformat()
        }
    
    async def start_job(self, job_id: str) -> bool:
        """Start a job."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/jobs/{job_id}/start",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        self.logger.info(f"Started job: {job_id}")
                        # Refresh jobs to get updated status
                        await self.refresh_jobs_async()
                        return True
                    else:
                        self.logger.error(f"Failed to start job {job_id}: status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error starting job {job_id}: {e}")
            return False
    
    async def stop_job(self, job_id: str) -> bool:
        """Stop a job."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/jobs/{job_id}/stop",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        self.logger.info(f"Stopped job: {job_id}")
                        # Refresh jobs to get updated status
                        await self.refresh_jobs_async()
                        return True
                    else:
                        self.logger.error(f"Failed to stop job {job_id}: status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error stopping job {job_id}: {e}")
            return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/jobs/{job_id}/pause",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        self.logger.info(f"Paused job: {job_id}")
                        # Refresh jobs to get updated status
                        await self.refresh_jobs_async()
                        return True
                    else:
                        self.logger.error(f"Failed to pause job {job_id}: status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def force_refresh(self):
        """Force immediate refresh of job status."""
        if self.is_monitoring:
            asyncio.create_task(self.refresh_jobs_async())


# Global job monitor instance
job_monitor = JobMonitor()
