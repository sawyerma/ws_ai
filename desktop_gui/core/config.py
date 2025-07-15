"""
DarkMa Trading Desktop GUI - Configuration Management
===================================================

Configuration management for the DarkMa Trading Desktop application.
Handles settings, themes, and application configuration.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from PySide6.QtCore import QSettings, QStandardPaths


class ConfigManager:
    """Manages application configuration and settings."""
    
    def __init__(self):
        self.app_name = "DarkMa Trading"
        self.organization = "DarkMa Systems"
        
        # Initialize Qt Settings
        self.settings = QSettings(self.organization, self.app_name)
        
        # Get config directory
        self.config_dir = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )) / "DarkMa"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        
        # Default configuration
        self.default_config = {
            "theme": {
                "mode": "system",  # dark, light, system
                "primary_color": "#1e88e5",
                "accent_color": "#43a047"
            },
            "backend": {
                "url": "http://localhost:8100",
                "websocket_url": "ws://localhost:8100/ws",
                "mlflow_url": "http://localhost:5000",
                "marketplace_url": "http://localhost:8080",
                "timeout": 30,
                "retry_attempts": 3
            },
            "system_tray": {
                "enabled": True,
                "minimize_to_tray": True,
                "start_minimized": False,
                "show_notifications": True
            },
            "performance": {
                "max_cpu_cores": 8,
                "max_memory_gb": 16,
                "gpu_acceleration": True,
                "data_compression": True,
                "update_interval": 3000
            },
            "latency": {
                "warning_threshold": 50,
                "critical_threshold": 100,
                "auto_recovery": True
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": True,
                "max_file_size": "10MB",
                "backup_count": 5
            },
            "ui": {
                "window_geometry": None,
                "window_state": None,
                "sidebar_width": 250,
                "auto_refresh": True,
                "show_system_indicators": True
            },
            "auth": {
                "auto_login": False,
                "remember_session": True,
                "session_timeout": 24  # hours
            }
        }
        
        # Load existing config
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults
                config = self.default_config.copy()
                self._deep_update(config, loaded_config)
                return config
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_theme_mode(self) -> str:
        """Get current theme mode."""
        return self.get("theme.mode", "system")
    
    def set_theme_mode(self, mode: str):
        """Set theme mode (dark, light, system)."""
        if mode in ["dark", "light", "system"]:
            self.set("theme.mode", mode)
    
    def get_backend_url(self) -> str:
        """Get backend URL."""
        return self.get("backend.url", "http://localhost:8100")
    
    def set_backend_url(self, url: str):
        """Set backend URL."""
        self.set("backend.url", url)
    
    def get_websocket_url(self) -> str:
        """Get WebSocket URL."""
        return self.get("backend.websocket_url", "ws://localhost:8100/ws")
    
    def set_websocket_url(self, url: str):
        """Set WebSocket URL."""
        self.set("backend.websocket_url", url)
    
    def get_system_tray_enabled(self) -> bool:
        """Check if system tray is enabled."""
        return self.get("system_tray.enabled", True)
    
    def set_system_tray_enabled(self, enabled: bool):
        """Enable/disable system tray."""
        self.set("system_tray.enabled", enabled)
    
    def get_window_geometry(self) -> Optional[bytes]:
        """Get saved window geometry."""
        return self.settings.value("geometry")
    
    def set_window_geometry(self, geometry: bytes):
        """Save window geometry."""
        self.settings.setValue("geometry", geometry)
    
    def get_window_state(self) -> Optional[bytes]:
        """Get saved window state."""
        return self.settings.value("windowState")
    
    def set_window_state(self, state: bytes):
        """Save window state."""
        self.settings.setValue("windowState", state)
    
    def get_update_interval(self) -> int:
        """Get UI update interval in milliseconds."""
        return self.get("performance.update_interval", 3000)
    
    def set_update_interval(self, interval: int):
        """Set UI update interval in milliseconds."""
        self.set("performance.update_interval", interval)
    
    def get_latency_thresholds(self) -> Dict[str, int]:
        """Get latency warning and critical thresholds."""
        return {
            "warning": self.get("latency.warning_threshold", 50),
            "critical": self.get("latency.critical_threshold", 100)
        }
    
    def set_latency_thresholds(self, warning: int, critical: int):
        """Set latency thresholds."""
        self.set("latency.warning_threshold", warning)
        self.set("latency.critical_threshold", critical)
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self.default_config.copy()
        self.save_config()
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Deep update dictionary."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value


# Global config instance
config_manager = ConfigManager()
