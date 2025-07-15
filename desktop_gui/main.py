"""
DarkMa Trading Desktop GUI - Main Entry Point
=============================================

Enterprise-level desktop application for DarkMa Trading System.
This is the main entry point that starts the PySide6 application.

Usage:
    python main.py [options]

Options:
    --debug         Enable debug logging
    --minimized     Start minimized to system tray
    --no-tray       Disable system tray integration
    --theme THEME   Set theme (dark, light, system)
    --backend URL   Set backend URL
    --help          Show this help message

Author: DarkMa Trading Systems
Version: 1.2.0
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from desktop_gui.core.application import app_instance
from desktop_gui.core.config import config_manager


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DarkMa Trading Desktop Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                          # Start with default settings
    python main.py --debug                  # Start with debug logging
    python main.py --minimized              # Start minimized to tray
    python main.py --theme dark             # Force dark theme
    python main.py --backend localhost:8100 # Custom backend URL
        """
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="Start minimized to system tray"
    )
    
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Disable system tray integration"
    )
    
    parser.add_argument(
        "--theme",
        choices=["dark", "light", "system"],
        help="Set application theme"
    )
    
    parser.add_argument(
        "--backend",
        metavar="URL",
        help="Backend server URL (e.g., http://localhost:8100)"
    )
    
    parser.add_argument(
        "--config-dir",
        metavar="PATH",
        help="Custom configuration directory"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="DarkMa Trading Desktop v1.2.0"
    )
    
    return parser.parse_args()


def apply_command_line_config(args):
    """Apply command line arguments to configuration."""
    
    # Set debug logging
    if args.debug:
        config_manager.set("logging.level", "DEBUG")
        config_manager.set("logging.console_enabled", True)
    
    # Set start minimized
    if args.minimized:
        config_manager.set("system_tray.start_minimized", True)
    
    # Disable system tray
    if args.no_tray:
        config_manager.set("system_tray.enabled", False)
    
    # Set theme
    if args.theme:
        config_manager.set_theme_mode(args.theme)
    
    # Set backend URL
    if args.backend:
        # Ensure proper URL format
        backend_url = args.backend
        if not backend_url.startswith(("http://", "https://")):
            backend_url = f"http://{backend_url}"
        
        config_manager.set_backend_url(backend_url)
        
        # Also update WebSocket URL
        ws_url = backend_url.replace("http://", "ws://").replace("https://", "wss://")
        config_manager.set_websocket_url(f"{ws_url}/ws")


def check_system_requirements():
    """Check if system meets minimum requirements."""
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("ERROR: Python 3.8 or higher is required")
            return False
        
        # Check PySide6 availability
        try:
            import PySide6
            print(f"✓ PySide6 {PySide6.__version__} detected")
        except ImportError:
            print("ERROR: PySide6 is required but not installed")
            print("Install with: pip install PySide6")
            return False
        
        # Check asyncio support
        try:
            import asyncio
            print("✓ Asyncio support available")
        except ImportError:
            print("ERROR: Asyncio support required")
            return False
        
        # Check optional dependencies
        try:
            import darkdetect
            print("✓ darkdetect available (system theme detection)")
        except ImportError:
            print("⚠ darkdetect not available (system theme detection disabled)")
        
        try:
            import aiohttp
            print("✓ aiohttp available (HTTP client)")
        except ImportError:
            print("⚠ aiohttp not available (using fallback HTTP client)")
        
        return True
        
    except Exception as e:
        print(f"ERROR during system check: {e}")
        return False


def setup_crash_handler():
    """Setup crash handler for better error reporting."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupt to work normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logging.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Try to show error dialog if Qt is available
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance()
            if app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("Kritischer Fehler")
                msg_box.setText(
                    f"Ein unerwarteter Fehler ist aufgetreten:\n\n"
                    f"{exc_type.__name__}: {exc_value}\n\n"
                    f"Weitere Details finden Sie in den Log-Dateien."
                )
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
        except:
            pass
    
    sys.excepthook = handle_exception


def create_desktop_shortcut():
    """Create desktop shortcut (platform-specific)."""
    try:
        import platform
        
        if platform.system() == "Darwin":  # macOS
            # Could create .app bundle or alias
            pass
        elif platform.system() == "Windows":
            # Could create .lnk shortcut
            pass
        elif platform.system() == "Linux":
            # Could create .desktop file
            pass
            
    except Exception as e:
        logging.debug(f"Could not create desktop shortcut: {e}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("🧠 DarkMa Trading Desktop Application")
    print("=" * 60)
    print(f"Version: 1.2.0")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Check system requirements
    print("Checking system requirements...")
    if not check_system_requirements():
        print("\n❌ System requirements not met. Exiting.")
        return 1
    
    print("\n✅ System requirements satisfied")
    print()
    
    # Apply command line configuration
    apply_command_line_config(args)
    
    # Setup crash handler
    setup_crash_handler()
    
    # Print configuration info
    print("Configuration:")
    print(f"  Backend URL: {config_manager.get_backend_url()}")
    print(f"  WebSocket URL: {config_manager.get_websocket_url()}")
    print(f"  Theme: {config_manager.get_theme_mode()}")
    print(f"  System Tray: {'Enabled' if config_manager.get_system_tray_enabled() else 'Disabled'}")
    print(f"  Start Minimized: {'Yes' if config_manager.get('system_tray.start_minimized', False) else 'No'}")
    print(f"  Log Level: {config_manager.get('logging.level', 'INFO')}")
    print()
    
    # Run the application
    print("Starting DarkMa Trading Desktop...")
    try:
        exit_code = app_instance.run(sys.argv)
        
        if exit_code == 0:
            print("\n✅ Application exited successfully")
        else:
            print(f"\n❌ Application exited with code {exit_code}")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⚠ Application interrupted by user")
        return 130  # Standard exit code for Ctrl+C
        
    except Exception as e:
        print(f"\n❌ Critical error during startup: {e}")
        logging.exception("Critical startup error")
        return 1


if __name__ == "__main__":
    # Enable high DPI scaling for modern displays
    import os
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    # Run the application
    exit_code = main()
    sys.exit(exit_code)
