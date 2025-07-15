"""
DarkMa Trading Desktop GUI - Theme Management
============================================

Advanced theme management with Dark, Light, and System theme support.
Includes dynamic theme switching and darkdetect integration for macOS.
"""

import sys
from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

try:
    import darkdetect
    DARKDETECT_AVAILABLE = True
except ImportError:
    DARKDETECT_AVAILABLE = False

from .config import config_manager


class DarkPalette:
    """Dark theme color palette for DarkMa Trading."""
    
    PRIMARY = QColor(30, 136, 229)        # #1e88e5
    PRIMARY_DARK = QColor(21, 101, 192)   # #1565c0
    SUCCESS = QColor(67, 160, 71)         # #43a047
    WARNING = QColor(255, 179, 0)         # #ffb300
    DANGER = QColor(229, 57, 53)          # #e53935
    
    # Background colors
    DARK = QColor(18, 18, 18)             # #121212
    DARKER = QColor(10, 10, 10)           # #0a0a0a
    CARD_BG = QColor(30, 30, 30)          # #1e1e1e
    HOVER_BG = QColor(42, 42, 42)         # #2a2a2a
    
    # Text colors
    LIGHT = QColor(245, 245, 245)         # #f5f5f5
    TEXT_MUTED = QColor(170, 170, 170)    # #aaa
    
    # Border and accent colors
    BORDER = QColor(61, 61, 61)           # #3d3d3d
    GRAY = QColor(45, 45, 45)             # #2d2d2d


class LightPalette:
    """Light theme color palette for DarkMa Trading."""
    
    PRIMARY = QColor(30, 136, 229)        # #1e88e5
    PRIMARY_DARK = QColor(21, 101, 192)   # #1565c0
    SUCCESS = QColor(67, 160, 71)         # #43a047
    WARNING = QColor(255, 179, 0)         # #ffb300
    DANGER = QColor(229, 57, 53)          # #e53935
    
    # Background colors
    LIGHT = QColor(255, 255, 255)         # #ffffff
    LIGHTER = QColor(248, 249, 250)       # #f8f9fa
    CARD_BG = QColor(255, 255, 255)       # #ffffff
    HOVER_BG = QColor(245, 245, 245)      # #f5f5f5
    
    # Text colors
    DARK = QColor(33, 37, 41)             # #212529
    TEXT_MUTED = QColor(108, 117, 125)    # #6c757d
    
    # Border and accent colors
    BORDER = QColor(222, 226, 230)        # #dee2e6
    GRAY = QColor(233, 236, 239)          # #e9ecef


class MacOSGrayPalette:
    """macOS Gray theme - Docker Desktop style."""
    
    PRIMARY = QColor(88, 166, 255)        # macOS blue
    PRIMARY_DARK = QColor(64, 130, 216)   # darker blue
    SUCCESS = QColor(52, 199, 89)         # macOS green
    WARNING = QColor(255, 149, 0)         # macOS orange
    DANGER = QColor(255, 69, 58)          # macOS red
    
    # Background colors (Docker-style grays)
    LIGHT = QColor(240, 240, 240)         # #f0f0f0
    LIGHTER = QColor(248, 248, 248)       # #f8f8f8
    CARD_BG = QColor(255, 255, 255)       # #ffffff
    HOVER_BG = QColor(232, 232, 232)      # #e8e8e8
    
    # Text colors
    DARK = QColor(51, 51, 51)             # #333333
    TEXT_MUTED = QColor(142, 142, 147)    # macOS gray
    
    # Border and accent colors
    BORDER = QColor(209, 209, 209)        # #d1d1d1
    GRAY = QColor(229, 229, 229)          # #e5e5e5


class ThemeManager(QObject):
    """Manages application themes with system integration."""
    
    theme_changed = Signal(str)  # Emitted when theme changes
    
    def __init__(self):
        super().__init__()
        self.current_theme = "system"
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self._check_system_theme)
        
        # Track last known system theme to detect changes
        self.last_system_theme = None
        
        if DARKDETECT_AVAILABLE:
            self.system_timer.start(1000)  # Check every second for system theme changes
    
    def get_current_theme(self) -> str:
        """Get the currently active theme."""
        return self.current_theme
    
    def set_theme(self, theme: str):
        """Set the application theme."""
        if theme not in ["dark", "light", "macos_gray", "system"]:
            raise ValueError("Theme must be 'dark', 'light', 'macos_gray', or 'system'")
        
        self.current_theme = theme
        config_manager.set_theme_mode(theme)
        
        # Apply the theme
        self._apply_theme()
        self.theme_changed.emit(theme)
    
    def _apply_theme(self):
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if not app:
            return
        
        effective_theme = self._get_effective_theme()
        
        if effective_theme == "dark":
            self._apply_dark_theme(app)
        elif effective_theme == "macos_gray":
            self._apply_macos_gray_theme(app)
        else:
            self._apply_light_theme(app)
    
    def _get_effective_theme(self) -> str:
        """Get the effective theme (resolving 'system' to actual theme)."""
        if self.current_theme == "system":
            if DARKDETECT_AVAILABLE:
                return "dark" if darkdetect.isDark() else "light"
            else:
                # Fallback to dark on non-macOS systems
                return "dark"
        else:
            return self.current_theme
    
    def _apply_dark_theme(self, app: QApplication):
        """Apply dark theme to the application."""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, DarkPalette.DARK)
        palette.setColor(QPalette.ColorRole.WindowText, DarkPalette.LIGHT)
        
        # Base colors (for input fields, etc.)
        palette.setColor(QPalette.ColorRole.Base, DarkPalette.CARD_BG)
        palette.setColor(QPalette.ColorRole.AlternateBase, DarkPalette.GRAY)
        
        # Text colors
        palette.setColor(QPalette.ColorRole.Text, DarkPalette.LIGHT)
        palette.setColor(QPalette.ColorRole.BrightText, DarkPalette.LIGHT)
        palette.setColor(QPalette.ColorRole.PlaceholderText, DarkPalette.TEXT_MUTED)
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, DarkPalette.GRAY)
        palette.setColor(QPalette.ColorRole.ButtonText, DarkPalette.LIGHT)
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, DarkPalette.PRIMARY)
        palette.setColor(QPalette.ColorRole.HighlightedText, DarkPalette.LIGHT)
        
        # Link colors
        palette.setColor(QPalette.ColorRole.Link, DarkPalette.PRIMARY)
        palette.setColor(QPalette.ColorRole.LinkVisited, DarkPalette.PRIMARY_DARK)
        
        # Disabled state
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, DarkPalette.TEXT_MUTED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, DarkPalette.TEXT_MUTED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, DarkPalette.TEXT_MUTED)
        
        app.setPalette(palette)
        
        # Set application style sheet for advanced styling
        app.setStyleSheet(self._get_dark_stylesheet())
    
    def _apply_light_theme(self, app: QApplication):
        """Apply light theme to the application."""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, LightPalette.LIGHT)
        palette.setColor(QPalette.ColorRole.WindowText, LightPalette.DARK)
        
        # Base colors
        palette.setColor(QPalette.ColorRole.Base, LightPalette.CARD_BG)
        palette.setColor(QPalette.ColorRole.AlternateBase, LightPalette.GRAY)
        
        # Text colors
        palette.setColor(QPalette.ColorRole.Text, LightPalette.DARK)
        palette.setColor(QPalette.ColorRole.BrightText, LightPalette.DARK)
        palette.setColor(QPalette.ColorRole.PlaceholderText, LightPalette.TEXT_MUTED)
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, LightPalette.GRAY)
        palette.setColor(QPalette.ColorRole.ButtonText, LightPalette.DARK)
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, LightPalette.PRIMARY)
        palette.setColor(QPalette.ColorRole.HighlightedText, LightPalette.LIGHT)
        
        # Link colors
        palette.setColor(QPalette.ColorRole.Link, LightPalette.PRIMARY)
        palette.setColor(QPalette.ColorRole.LinkVisited, LightPalette.PRIMARY_DARK)
        
        # Disabled state
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, LightPalette.TEXT_MUTED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, LightPalette.TEXT_MUTED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, LightPalette.TEXT_MUTED)
        
        app.setPalette(palette)
        
        # Set application style sheet for advanced styling
        app.setStyleSheet(self._get_light_stylesheet())
    
    def _apply_macos_gray_theme(self, app: QApplication):
        """Apply macOS Gray theme (Docker-style)."""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, MacOSGrayPalette.LIGHT)
        palette.setColor(QPalette.ColorRole.WindowText, MacOSGrayPalette.DARK)
        
        # Base colors
        palette.setColor(QPalette.ColorRole.Base, MacOSGrayPalette.CARD_BG)
        palette.setColor(QPalette.ColorRole.AlternateBase, MacOSGrayPalette.GRAY)
        
        # Text colors
        palette.setColor(QPalette.ColorRole.Text, MacOSGrayPalette.DARK)
        palette.setColor(QPalette.ColorRole.BrightText, MacOSGrayPalette.DARK)
        palette.setColor(QPalette.ColorRole.PlaceholderText, MacOSGrayPalette.TEXT_MUTED)
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, MacOSGrayPalette.GRAY)
        palette.setColor(QPalette.ColorRole.ButtonText, MacOSGrayPalette.DARK)
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, MacOSGrayPalette.PRIMARY)
        palette.setColor(QPalette.ColorRole.HighlightedText, MacOSGrayPalette.CARD_BG)
        
        # Link colors
        palette.setColor(QPalette.ColorRole.Link, MacOSGrayPalette.PRIMARY)
        palette.setColor(QPalette.ColorRole.LinkVisited, MacOSGrayPalette.PRIMARY_DARK)
        
        # Disabled state
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, MacOSGrayPalette.TEXT_MUTED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, MacOSGrayPalette.TEXT_MUTED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, MacOSGrayPalette.TEXT_MUTED)
        
        app.setPalette(palette)
        app.setStyleSheet(self._get_macos_gray_stylesheet())
    
    def _get_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet."""
        return """
        QMainWindow {
            background-color: #121212;
            color: #f5f5f5;
        }
        
        QWidget {
            background-color: #121212;
            color: #f5f5f5;
        }
        
        QScrollArea {
            border: none;
            background-color: #121212;
        }
        
        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #1e88e5;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #1565c0;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        
        QMenuBar {
            background-color: #0a0a0a;
            color: #f5f5f5;
            border-bottom: 1px solid #3d3d3d;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 8px 16px;
        }
        
        QMenuBar::item:selected {
            background-color: #1e88e5;
        }
        
        QMenu {
            background-color: #1e1e1e;
            color: #f5f5f5;
            border: 1px solid #3d3d3d;
        }
        
        QMenu::item {
            padding: 8px 16px;
        }
        
        QMenu::item:selected {
            background-color: #1e88e5;
        }
        
        QToolTip {
            background-color: #1e1e1e;
            color: #f5f5f5;
            border: 1px solid #3d3d3d;
            padding: 4px;
        }
        
        QStatusBar {
            background-color: #0a0a0a;
            color: #f5f5f5;
            border-top: 1px solid #3d3d3d;
        }
        """
    
    def _get_light_stylesheet(self) -> str:
        """Get light theme stylesheet."""
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #212529;
        }
        
        QWidget {
            background-color: #ffffff;
            color: #212529;
        }
        
        QScrollArea {
            border: none;
            background-color: #ffffff;
        }
        
        QScrollBar:vertical {
            background-color: #e9ecef;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #1e88e5;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #1565c0;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        
        QMenuBar {
            background-color: #f8f9fa;
            color: #212529;
            border-bottom: 1px solid #dee2e6;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 8px 16px;
        }
        
        QMenuBar::item:selected {
            background-color: #1e88e5;
            color: #ffffff;
        }
        
        QMenu {
            background-color: #ffffff;
            color: #212529;
            border: 1px solid #dee2e6;
        }
        
        QMenu::item {
            padding: 8px 16px;
        }
        
        QMenu::item:selected {
            background-color: #1e88e5;
            color: #ffffff;
        }
        
        QToolTip {
            background-color: #ffffff;
            color: #212529;
            border: 1px solid #dee2e6;
            padding: 4px;
        }
        
        QStatusBar {
            background-color: #f8f9fa;
            color: #212529;
            border-top: 1px solid #dee2e6;
        }
        """
    
    def _get_macos_gray_stylesheet(self) -> str:
        """Get macOS Gray theme stylesheet (Docker-style)."""
        return """
        QMainWindow {
            background-color: #f0f0f0;
            color: #333333;
        }
        
        QWidget {
            background-color: #f0f0f0;
            color: #333333;
        }
        
        QScrollArea {
            border: none;
            background-color: #f0f0f0;
        }
        
        QScrollBar:vertical {
            background-color: #e5e5e5;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #58a6ff;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #4082d8;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        
        QMenuBar {
            background-color: #f8f8f8;
            color: #333333;
            border-bottom: 1px solid #d1d1d1;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 8px 16px;
        }
        
        QMenuBar::item:selected {
            background-color: #58a6ff;
            color: #ffffff;
        }
        
        QMenu {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #d1d1d1;
            border-radius: 6px;
        }
        
        QMenu::item {
            padding: 8px 16px;
        }
        
        QMenu::item:selected {
            background-color: #58a6ff;
            color: #ffffff;
        }
        
        QToolTip {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #d1d1d1;
            padding: 4px;
            border-radius: 4px;
        }
        
        QStatusBar {
            background-color: #f8f8f8;
            color: #333333;
            border-top: 1px solid #d1d1d1;
        }
        """
    
    def _check_system_theme(self):
        """Check for system theme changes (macOS)."""
        if not DARKDETECT_AVAILABLE or self.current_theme != "system":
            return
        
        current_system_theme = "dark" if darkdetect.isDark() else "light"
        
        if self.last_system_theme != current_system_theme:
            self.last_system_theme = current_system_theme
            self._apply_theme()
            self.theme_changed.emit("system")
    
    def initialize_theme(self):
        """Initialize theme from configuration."""
        saved_theme = config_manager.get_theme_mode()
        self.current_theme = saved_theme
        self._apply_theme()
    
    def get_theme_colors(self) -> Dict[str, QColor]:
        """Get current theme colors."""
        effective_theme = self._get_effective_theme()
        
        if effective_theme == "dark":
            return {
                "primary": DarkPalette.PRIMARY,
                "primary_dark": DarkPalette.PRIMARY_DARK,
                "success": DarkPalette.SUCCESS,
                "warning": DarkPalette.WARNING,
                "danger": DarkPalette.DANGER,
                "background": DarkPalette.DARK,
                "background_dark": DarkPalette.DARKER,
                "card_bg": DarkPalette.CARD_BG,
                "hover_bg": DarkPalette.HOVER_BG,
                "text": DarkPalette.LIGHT,
                "text_muted": DarkPalette.TEXT_MUTED,
                "border": DarkPalette.BORDER,
                "gray": DarkPalette.GRAY
            }
        elif effective_theme == "macos_gray":
            return {
                "primary": MacOSGrayPalette.PRIMARY,
                "primary_dark": MacOSGrayPalette.PRIMARY_DARK,
                "success": MacOSGrayPalette.SUCCESS,
                "warning": MacOSGrayPalette.WARNING,
                "danger": MacOSGrayPalette.DANGER,
                "background": MacOSGrayPalette.LIGHT,
                "background_dark": MacOSGrayPalette.LIGHTER,
                "card_bg": MacOSGrayPalette.CARD_BG,
                "hover_bg": MacOSGrayPalette.HOVER_BG,
                "text": MacOSGrayPalette.DARK,
                "text_muted": MacOSGrayPalette.TEXT_MUTED,
                "border": MacOSGrayPalette.BORDER,
                "gray": MacOSGrayPalette.GRAY
            }
        else:
            return {
                "primary": LightPalette.PRIMARY,
                "primary_dark": LightPalette.PRIMARY_DARK,
                "success": LightPalette.SUCCESS,
                "warning": LightPalette.WARNING,
                "danger": LightPalette.DANGER,
                "background": LightPalette.LIGHT,
                "background_dark": LightPalette.LIGHTER,
                "card_bg": LightPalette.CARD_BG,
                "hover_bg": LightPalette.HOVER_BG,
                "text": LightPalette.DARK,
                "text_muted": LightPalette.TEXT_MUTED,
                "border": LightPalette.BORDER,
                "gray": LightPalette.GRAY
            }


# Global theme manager instance
theme_manager = ThemeManager()
