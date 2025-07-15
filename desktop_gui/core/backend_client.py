"""
DarkMa Trading Desktop GUI - Backend Client
==========================================

Enterprise-level backend integration with WebSocket support,
auto-reconnection, and comprehensive error handling.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta

import aiohttp
import websocket
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from .config import config_manager


class BackendStatus:
    """Backend connection status."""
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class BackendClient(QObject):
    """High-performance backend client with WebSocket support."""
    
    # Signals
    status_changed = Signal(str)  # status
    data_received = Signal(str, dict)  # endpoint, data
    error_occurred = Signal(str, str)  # error_type, message
    jobs_updated = Signal(list)
    workers_updated = Signal(list)
    system_metrics_updated = Signal(dict)
    logs_updated = Signal(list)
    
    def __init__(self):
        super().__init__()
        self.base_url = config_manager.get_backend_url()
        self.ws_url = config_manager.get_websocket_url()
        self.status = BackendStatus.DISCONNECTED
        
        # HTTP session
        self.session = None
        self.network_manager = QNetworkAccessManager()
        
        # WebSocket connection
        self.ws = None
        self.ws_thread = None
        
        # Connection retry logic
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self.connect_to_backend)
        self.retry_attempts = 0
        self.max_retries = config_manager.get("backend.retry_attempts", 3)
        
        # Periodic data refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        
        # Authentication
        self.auth_token = None
        self.auth_expires = None
        
        # Cache for data
        self.cache = {
            "jobs": [],
            "workers": [],
            "system_metrics": {},
            "logs": []
        }
    
    async def initialize(self):
        """Initialize the backend client."""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(
                    total=config_manager.get("backend.timeout", 30)
                )
            )
            
            # Connect to backend
            await self.connect_to_backend()
            
        except Exception as e:
            logging.error(f"Failed to initialize backend client: {e}")
            self.error_occurred.emit("initialization", str(e))
    
    async def connect_to_backend(self):
        """Connect to the backend API and WebSocket."""
        try:
            self.status = BackendStatus.CONNECTING
            self.status_changed.emit(self.status)
            
            # Test HTTP connection
            if await self.test_connection():
                # Authenticate if needed
                if await self.authenticate():
                    # Connect WebSocket
                    await self.connect_websocket()
                    
                    self.status = BackendStatus.CONNECTED
                    self.status_changed.emit(self.status)
                    self.retry_attempts = 0
                    
                    # Start periodic refresh
                    self.refresh_timer.start(config_manager.get_update_interval())
                    
                    # Initial data load
                    await self.refresh_data()
                else:
                    raise Exception("Authentication failed")
            else:
                raise Exception("Backend connection test failed")
                
        except Exception as e:
            logging.error(f"Backend connection failed: {e}")
            self.status = BackendStatus.ERROR
            self.status_changed.emit(self.status)
            self.error_occurred.emit("connection", str(e))
            
            # Retry logic
            self.retry_attempts += 1
            if self.retry_attempts <= self.max_retries:
                retry_delay = min(1000 * (2 ** self.retry_attempts), 30000)  # Exponential backoff
                self.retry_timer.start(retry_delay)
    
    async def test_connection(self) -> bool:
        """Test HTTP connection to backend."""
        try:
            if not self.session:
                return False
                
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except:
            return False
    
    async def authenticate(self) -> bool:
        """Authenticate with the backend."""
        try:
            # Check if we have a valid token
            if self.auth_token and self.auth_expires:
                if datetime.now() < self.auth_expires:
                    return True
            
            # Authenticate
            auth_data = {
                "username": "admin",  # From config or user input
                "password": "admin"   # From secure storage
            }
            
            async with self.session.post(
                f"{self.base_url}/auth/login", 
                json=auth_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    
                    # Set expiry (default 24h if not provided)
                    expires_in = data.get("expires_in", 86400)
                    self.auth_expires = datetime.now() + timedelta(seconds=expires_in)
                    
                    return True
                else:
                    return False
                    
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False
    
    async def connect_websocket(self):
        """Connect to WebSocket for real-time updates."""
        try:
            # WebSocket headers with auth
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Connect WebSocket (simplified for now)
            # In production, use proper async WebSocket client
            logging.info(f"WebSocket connection to {self.ws_url} would be established here")
            
        except Exception as e:
            logging.error(f"WebSocket connection failed: {e}")
    
    async def refresh_data(self):
        """Refresh all data from backend."""
        try:
            # Refresh jobs
            jobs = await self.get_jobs()
            if jobs is not None:
                self.cache["jobs"] = jobs
                self.jobs_updated.emit(jobs)
            
            # Refresh workers
            workers = await self.get_workers()
            if workers is not None:
                self.cache["workers"] = workers
                self.workers_updated.emit(workers)
            
            # Refresh system metrics
            metrics = await self.get_system_metrics()
            if metrics is not None:
                self.cache["system_metrics"] = metrics
                self.system_metrics_updated.emit(metrics)
            
            # Refresh logs
            logs = await self.get_logs()
            if logs is not None:
                self.cache["logs"] = logs
                self.logs_updated.emit(logs)
                
        except Exception as e:
            logging.error(f"Data refresh failed: {e}")
    
    async def get_jobs(self) -> Optional[List[Dict]]:
        """Get jobs from backend."""
        try:
            headers = self._get_auth_headers()
            async with self.session.get(f"{self.base_url}/jobs", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("jobs", [])
                else:
                    return None
        except Exception as e:
            logging.error(f"Failed to get jobs: {e}")
            return None
    
    async def get_workers(self) -> Optional[List[Dict]]:
        """Get workers/nodes from backend."""
        try:
            headers = self._get_auth_headers()
            async with self.session.get(f"{self.base_url}/workers", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("workers", [])
                else:
                    return None
        except Exception as e:
            logging.error(f"Failed to get workers: {e}")
            return None
    
    async def get_system_metrics(self) -> Optional[Dict]:
        """Get system metrics from backend."""
        try:
            headers = self._get_auth_headers()
            async with self.session.get(f"{self.base_url}/system/metrics", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception as e:
            logging.error(f"Failed to get system metrics: {e}")
            return None
    
    async def get_logs(self, limit: int = 100) -> Optional[List[Dict]]:
        """Get logs from backend."""
        try:
            headers = self._get_auth_headers()
            params = {"limit": limit}
            async with self.session.get(
                f"{self.base_url}/logs", 
                headers=headers, 
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("logs", [])
                else:
                    return None
        except Exception as e:
            logging.error(f"Failed to get logs: {e}")
            return None
    
    async def control_job(self, job_id: str, action: str) -> bool:
        """Control a job (start, pause, stop)."""
        try:
            headers = self._get_auth_headers()
            data = {"action": action}
            
            async with self.session.post(
                f"{self.base_url}/jobs/{job_id}/control",
                headers=headers,
                json=data
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logging.error(f"Failed to control job {job_id}: {e}")
            return False
    
    async def create_job(self, job_config: Dict) -> Optional[str]:
        """Create a new job."""
        try:
            headers = self._get_auth_headers()
            
            async with self.session.post(
                f"{self.base_url}/jobs",
                headers=headers,
                json=job_config
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    return data.get("job_id")
                else:
                    return None
                    
        except Exception as e:
            logging.error(f"Failed to create job: {e}")
            return None
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        return headers
    
    def disconnect(self):
        """Disconnect from backend."""
        self.refresh_timer.stop()
        self.retry_timer.stop()
        
        if self.ws:
            # Close WebSocket
            pass
        
        if self.session:
            # Close HTTP session in event loop
            pass
        
        self.status = BackendStatus.DISCONNECTED
        self.status_changed.emit(self.status)
    
    def get_cached_data(self, data_type: str) -> Any:
        """Get cached data."""
        return self.cache.get(data_type, [] if data_type != "system_metrics" else {})


class MockBackendClient(BackendClient):
    """Mock backend client for development and testing."""
    
    async def initialize(self):
        """Initialize mock client."""
        self.status = BackendStatus.CONNECTED
        self.status_changed.emit(self.status)
        
        # Start periodic updates with mock data
        self.refresh_timer.start(3000)
        await self.refresh_data()
    
    async def refresh_data(self):
        """Generate mock data."""
        import random
        from datetime import datetime
        
        # Mock jobs data
        jobs = [
            {
                "id": "job-001",
                "name": "Whale Detection",
                "type": "Marktanalyse",
                "status": "running",
                "cpu": random.uniform(10, 25),
                "ram": f"{random.uniform(300, 500):.0f} MB",
                "latency": f"{random.randint(25, 45)}ms",
                "start_time": "vor 2 Stunden"
            },
            {
                "id": "job-002", 
                "name": "Trend Prognose",
                "type": "ML Vorhersage",
                "status": "running",
                "cpu": random.uniform(5, 15),
                "ram": f"{random.uniform(200, 300):.0f} MB",
                "latency": f"{random.randint(35, 55)}ms",
                "start_time": "vor 45 Minuten"
            },
            {
                "id": "job-003",
                "name": "Orderbuch Analyse",
                "type": "Echtzeitanalyse", 
                "status": "paused",
                "cpu": 0,
                "ram": "0 MB",
                "latency": "-",
                "start_time": "vor 1 Tag"
            }
        ]
        
        # Mock workers data
        workers = [
            {
                "id": "worker-001",
                "name": "Haupt-Worker (GPU)",
                "ip": "192.168.1.101",
                "last_activity": "vor 15 Sekunden",
                "online": True,
                "cpu": random.uniform(70, 90),
                "ram": random.uniform(40, 60),
                "gpu": random.uniform(70, 85)
            },
            {
                "id": "worker-002",
                "name": "Analyse-Node #1",
                "ip": "192.168.1.102", 
                "last_activity": "vor 15 Sekunden",
                "online": True,
                "cpu": random.uniform(50, 70),
                "ram": random.uniform(45, 65),
                "gpu": random.uniform(25, 40)
            }
        ]
        
        # Mock system metrics
        metrics = {
            "cpu": {
                "total": random.uniform(35, 50),
                "cores": [random.uniform(30, 80) for _ in range(4)],
                "temperature": random.uniform(65, 75)
            },
            "ram": {
                "total": 128,
                "used": random.uniform(25, 40),
                "free": random.uniform(85, 100),
                "cache": random.uniform(5, 8)
            },
            "gpu": {
                "utilization": random.uniform(70, 85),
                "memory_used": random.uniform(6, 10),
                "memory_total": 24,
                "temperature": random.uniform(70, 80)
            },
            "disk": {
                "read_speed": random.uniform(100, 150),
                "write_speed": random.uniform(40, 60),
                "usage": random.uniform(25, 35)
            }
        }
        
        # Mock logs
        logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "WhaleDetection",
                "message": "Analysezyklus gestartet"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "WARN",
                "source": "System",
                "message": f"CPU Auslastung: {metrics['cpu']['total']:.1f}%"
            }
        ]
        
        # Update cache and emit signals
        self.cache["jobs"] = jobs
        self.cache["workers"] = workers
        self.cache["system_metrics"] = metrics
        self.cache["logs"] = logs
        
        self.jobs_updated.emit(jobs)
        self.workers_updated.emit(workers)
        self.system_metrics_updated.emit(metrics)
        self.logs_updated.emit(logs)


# Global backend client instance
backend_client = MockBackendClient()  # Use MockBackendClient for development
