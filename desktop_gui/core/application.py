"""
DarkMa Trading Desktop GUI - Main Application
============================================

Enterprise-level main application class that orchestrates all core components,
manages application lifecycle, and provides the foundation for the GUI.
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QTimer, QObject, Signal, QThread
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

from .config import config_manager
from .theme_manager import theme_manager
from .system_tray import system_tray_manager, SystemStatus
from .backend_client import backend_client, BackendStatus
from .test_manager import test_manager
from .test_scheduler import test_scheduler
from .latency_monitor import latency_monitor
from .job_monitor import job_monitor


class AsyncRunner(QThread):
    """Thread for running async operations."""
    
    def __init__(self, coro):
        super().__init__()
        self.coro = coro
        self.loop = None
    
    def run(self):
        """Run the async coroutine."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.coro)
        finally:
            self.loop.close()


class DarkMaApplication(QObject):
    """Main DarkMa Trading Desktop Application."""
    
    # Signals
    ready = Signal()
    error = Signal(str, str)  # error_type, message
    
    def __init__(self):
        super().__init__()
        
        # Application instance
        self.app = None
        self.main_window = None
        
        # Core components
        self.config = config_manager
        self.theme = theme_manager
        self.system_tray = system_tray_manager
        self.backend = backend_client
        
        # Async runner
        self.async_runner = None
        
        # Application state
        self.is_initialized = False
        self.is_shutting_down = False
        
        # Setup logging
        self.setup_logging()
        
        logging.info("DarkMa Trading Desktop Application initialized")
    
    def setup_logging(self):
        """Setup application logging."""
        log_level = getattr(logging, self.config.get("logging.level", "INFO"))
        
        # Create logs directory
        log_dir = Path.home() / ".darkma" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "darkma_desktop.log"),
                logging.StreamHandler(sys.stdout) if self.config.get("logging.console_enabled", True) else logging.NullHandler()
            ]
        )
        
        # Set log rotation if needed
        if self.config.get("logging.file_enabled", True):
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_dir / "darkma_desktop.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            
            # Add to root logger
            logging.getLogger().addHandler(file_handler)
    
    def create_application(self, argv: list) -> QApplication:
        """Create and configure the Qt application."""
        
        # Set application properties
        QApplication.setApplicationName("DarkMa Trading")
        QApplication.setApplicationVersion("1.2.0")
        QApplication.setOrganizationName("DarkMa Systems")
        QApplication.setOrganizationDomain("darkma.trading")
        
        # Create application
        self.app = QApplication(argv)
        
        # Set application icon
        self.set_application_icon()
        
        # Configure application
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when window closes
        
        logging.info("Qt Application created")
        return self.app
    
    def set_application_icon(self):
        """Set the application icon."""
        # Create a simple icon programmatically
        icon_pixmap = QPixmap(64, 64)
        icon_pixmap.fill(QColor(0, 0, 0, 0))  # Transparent
        
        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw brain icon (simplified)
        painter.setBrush(QColor(30, 136, 229))  # Primary blue
        painter.setPen(QColor(21, 101, 192))    # Primary dark
        painter.drawEllipse(8, 8, 48, 48)
        
        # Add inner details
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(20, 20, 8, 8)
        painter.drawEllipse(36, 20, 8, 8)
        painter.drawEllipse(28, 35, 8, 8)
        
        painter.end()
        
        icon = QIcon(icon_pixmap)
        self.app.setWindowIcon(icon)
    
    async def initialize_async_components(self):
        """Initialize async components like backend client."""
        try:
            logging.info("Initializing async components...")
            
            # Initialize backend client
            await self.backend.initialize()
            
            logging.info("Async components initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize async components: {e}")
            self.error.emit("initialization", str(e))
    
    def initialize_components(self):
        """Initialize all application components."""
        try:
            logging.info("Initializing application components...")
            
            # Initialize theme manager
            self.theme.initialize_theme()
            logging.info("Theme manager initialized")
            
            # Connect theme manager signals
            self.theme.theme_changed.connect(self.on_theme_changed)
            
            # Initialize system tray
            if self.config.get_system_tray_enabled():
                self.system_tray.initialize()
                
                # Connect system tray signals
                self.system_tray.show_main_window.connect(self.show_main_window)
                self.system_tray.show_settings.connect(self.show_settings)
                self.system_tray.restart_application.connect(self.restart)
                self.system_tray.quit_application.connect(self.quit_application)
                
                # Set initial status to RUNNING with passed tests
                self.system_tray.set_status(SystemStatus.RUNNING)
                self.system_tray.set_test_status("passed")
                
                logging.info("System tray initialized")
            
            # Connect backend signals
            self.backend.status_changed.connect(self.on_backend_status_changed)
            self.backend.error_occurred.connect(self.on_backend_error)
            
            # Initialize async components
            self.async_runner = AsyncRunner(self.initialize_async_components())
            self.async_runner.finished.connect(self.on_async_initialization_complete)
            self.async_runner.start()
            
            logging.info("Components initialization started")
            
        except Exception as e:
            logging.error(f"Component initialization failed: {e}")
            self.error.emit("components", str(e))
    
    def on_async_initialization_complete(self):
        """Handle completion of async initialization."""
        logging.info("Async initialization completed")
        self.is_initialized = True
        self.ready.emit()
    
    def create_main_window(self):
        """Create and configure the main window."""
        # Import here to avoid circular imports
        from ..ui.main_window import MainWindow
        
        self.main_window = MainWindow()
        
        # Connect window signals
        self.main_window.close_requested.connect(self.on_main_window_close)
        
        # Restore window geometry
        geometry = self.config.get_window_geometry()
        if geometry:
            self.main_window.restoreGeometry(geometry)
        
        window_state = self.config.get_window_state()
        if window_state:
            self.main_window.restoreState(window_state)
        
        logging.info("Main window created")
        
        return self.main_window
    
    def show_main_window(self):
        """Show the main window."""
        if not self.main_window:
            self.create_main_window()
        
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        logging.info("Main window shown")
    
    def hide_main_window(self):
        """Hide the main window."""
        if self.main_window:
            # Save window geometry before hiding
            self.config.set_window_geometry(self.main_window.saveGeometry())
            self.config.set_window_state(self.main_window.saveState())
            
            self.main_window.hide()
            logging.info("Main window hidden")
    
    def on_main_window_close(self):
        """Handle main window close request."""
        if self.config.get("system_tray.minimize_to_tray", True) and self.system_tray.tray_icon:
            # Minimize to system tray instead of closing
            self.hide_main_window()
            
            # Show notification
            self.system_tray.show_notification(
                "DarkMa Trading",
                "Anwendung wurde in die Systemleiste minimiert"
            )
        else:
            # Actually quit the application
            self.quit_application()
    
    def show_settings(self):
        """Show settings dialog."""
        logging.info("Settings requested")
        # TODO: Implement settings dialog
        
    def on_theme_changed(self, theme: str):
        """Handle theme change."""
        logging.info(f"Theme changed to: {theme}")
    
    def on_backend_status_changed(self, status: str):
        """Handle backend status change."""
        logging.info(f"Backend status changed to: {status}")
        
        # Update system tray status
        if status == "connected":
            self.system_tray.set_status("running")
        elif status == "connecting":
            self.system_tray.set_status("warning")
        elif status == "error":
            self.system_tray.set_status("error")
        else:
            self.system_tray.set_status("offline")
    
    def on_backend_error(self, error_type: str, message: str):
        """Handle backend error."""
        logging.error(f"Backend error ({error_type}): {message}")
        
        # Show error notification if severe
        if error_type in ["connection", "authentication"]:
            self.system_tray.show_notification(
                "DarkMa Trading - Fehler",
                f"Backend-Verbindungsfehler: {message}"
            )
    
    def show_error_dialog(self, title: str, message: str):
        """Show error dialog to user."""
        if self.app:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
    
    def quit_application(self):
        """Gracefully quit the application."""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logging.info("Application shutdown initiated")
        
        try:
            # Save window state
            if self.main_window:
                self.config.set_window_geometry(self.main_window.saveGeometry())
                self.config.set_window_state(self.main_window.saveState())
            
            # Cleanup components
            if self.system_tray:
                self.system_tray.cleanup()
            
            if self.backend:
                self.backend.disconnect()
            
            # Stop async runner
            if self.async_runner and self.async_runner.isRunning():
                self.async_runner.quit()
                self.async_runner.wait(3000)  # Wait max 3 seconds
            
            logging.info("Components cleaned up successfully")
            
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
        
        finally:
            # Quit Qt application
            if self.app:
                self.app.quit()
    
    def run(self, argv: list) -> int:
        """Run the application."""
        try:
            # Create Qt application
            self.create_application(argv)
            
            # Connect error signal
            self.error.connect(self.show_error_dialog)
            
            # Initialize components
            self.initialize_components()
            
            # Show main window if not starting minimized
            if not self.config.get("system_tray.start_minimized", False):
                QTimer.singleShot(100, self.show_main_window)  # Slight delay for better UX
            
            # Run event loop
            return self.app.exec()
            
        except Exception as e:
            logging.error(f"Critical application error: {e}")
            
            if self.app:
                QMessageBox.critical(
                    None,
                    "Kritischer Fehler",
                    f"Die Anwendung konnte nicht gestartet werden:\n{e}"
                )
            
            return 1
    
    def restart(self):
        """Restart the application."""
        logging.info("Application restart requested")
        
        # Save current state
        if self.main_window:
            self.config.set_window_geometry(self.main_window.saveGeometry())
            self.config.set_window_state(self.main_window.saveState())
        
        # Cleanup and restart
        self.quit_application()
        
        # The actual restart should be handled by the launcher script
        # or the operating system


# Global application instance
app_instance = DarkMaApplication()
