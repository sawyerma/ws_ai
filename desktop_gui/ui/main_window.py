"""
DarkMa Trading Desktop GUI - Main Window
=======================================

Main application window with dark theme and trading platform interface.
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QSplitter, QTabWidget, QLabel, QFrame, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
                               QScrollArea, QGridLayout, QStackedWidget)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont, QPalette, QColor

import random
from typing import Dict, List


class JobsTab(QWidget):
    """Jobs overview tab."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        title = QLabel("📋 Jobs Übersicht")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e88e5;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Buttons
        new_job_btn = QPushButton("➕ Neuer Job")
        refresh_btn = QPushButton("🔄 Aktualisieren")
        
        for btn in [new_job_btn, refresh_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e88e5;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
        
        header_layout.addWidget(new_job_btn)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header)
        
        # Jobs table
        self.jobs_table = QTableWidget()
        self.jobs_table.setColumnCount(6)
        self.jobs_table.setHorizontalHeaderLabels([
            "Name", "Typ", "Status", "CPU", "RAM", "Latenz"
        ])
        
        # Style table
        self.jobs_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QTableWidget::item:selected {
                background-color: #2a2a2a;
            }
            QHeaderView::section {
                background-color: #0a0a0a;
                color: #aaa;
                border: 1px solid #3d3d3d;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # Populate with sample data
        self.populate_jobs_table()
        
        layout.addWidget(self.jobs_table)
        self.setLayout(layout)
    
    def populate_jobs_table(self):
        """Populate jobs table with sample data."""
        jobs = [
            ("Whale Detection", "Marktanalyse", "🟢 Laufend", "14.2%", "412 MB", "32ms"),
            ("Trend Prognose", "ML Vorhersage", "🟢 Laufend", "8.7%", "287 MB", "45ms"),
            ("Orderbuch Analyse", "Echtzeitanalyse", "🟡 Pausiert", "0%", "0 MB", "-"),
            ("Volatilitäts Scanner", "Marktanalyse", "🟢 Laufend", "6.3%", "521 MB", "82ms"),
            ("Sentiment Analyse", "NLP Verarbeitung", "🔴 Gestoppt", "0%", "0 MB", "-")
        ]
        
        self.jobs_table.setRowCount(len(jobs))
        
        for row, job in enumerate(jobs):
            for col, value in enumerate(job):
                item = QTableWidgetItem(str(value))
                
                # Color coding for status
                if col == 2:  # Status column
                    if "Laufend" in value:
                        item.setForeground(QColor("#43a047"))
                    elif "Pausiert" in value:
                        item.setForeground(QColor("#ffb300"))
                    elif "Gestoppt" in value:
                        item.setForeground(QColor("#e53935"))
                
                self.jobs_table.setItem(row, col, item)
        
        # Adjust column widths
        header = self.jobs_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def setup_timer(self):
        """Setup timer for updating job data."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_jobs)
        self.update_timer.start(3000)  # Update every 3 seconds
    
    def update_jobs(self):
        """Update job metrics."""
        for row in range(self.jobs_table.rowCount()):
            status_item = self.jobs_table.item(row, 2)
            if status_item and "Laufend" in status_item.text():
                # Update CPU
                cpu_value = random.uniform(5, 25)
                cpu_item = self.jobs_table.item(row, 3)
                if cpu_item:
                    cpu_item.setText(f"{cpu_value:.1f}%")
                
                # Update latency
                latency_value = random.randint(25, 100)
                latency_item = self.jobs_table.item(row, 5)
                if latency_item:
                    latency_item.setText(f"{latency_value}ms")


class WorkersTab(QWidget):
    """Workers/Nodes overview tab."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🖥️ Worker/Nodes Übersicht")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e88e5; margin-bottom: 20px;")
        layout.addWidget(header)
        
        # Workers grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        workers_widget = QWidget()
        workers_layout = QGridLayout(workers_widget)
        
        # Sample workers
        workers = [
            ("Haupt-Worker (GPU)", "192.168.1.101", "🟢 Online", 82, 43, 78),
            ("Analyse-Node #1", "192.168.1.102", "🟢 Online", 62, 52, 32),
            ("Datenbank-Node", "192.168.1.103", "🟡 Warning", 65, 100, 5),
            ("Backup-Node", "192.168.1.104", "🔴 Offline", 0, 0, 0)
        ]
        
        for i, (name, ip, status, cpu, ram, gpu) in enumerate(workers):
            worker_card = self.create_worker_card(name, ip, status, cpu, ram, gpu)
            workers_layout.addWidget(worker_card, i // 2, i % 2)
        
        scroll.setWidget(workers_widget)
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def create_worker_card(self, name: str, ip: str, status: str, cpu: int, ram: int, gpu: int) -> QWidget:
        """Create a worker card widget."""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(name)
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        status_label = QLabel(status)
        
        if "Online" in status:
            status_label.setStyleSheet("color: #43a047;")
        elif "Warning" in status:
            status_label.setStyleSheet("color: #ffb300;")
        else:
            status_label.setStyleSheet("color: #e53935;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # IP
        ip_label = QLabel(f"IP: {ip}")
        ip_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(ip_label)
        
        # Metrics
        if "Online" in status:
            metrics = [("CPU", cpu, "#43a047"), ("RAM", ram, "#3b82f6"), ("GPU", gpu, "#ffb300")]
            for metric_name, value, color in metrics:
                metric_widget = self.create_metric_widget(metric_name, value, color)
                layout.addWidget(metric_widget)
        
        return card
    
    def create_metric_widget(self, name: str, value: int, color: str) -> QWidget:
        """Create a metric widget with progress bar."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Header
        header_layout = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setStyleSheet("color: white; font-size: 12px;")
        value_label = QLabel(f"{value}%")
        value_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        header_layout.addWidget(value_label)
        layout.addLayout(header_layout)
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(value)
        progress.setTextVisible(False)
        progress.setFixedHeight(8)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #2d2d2d;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        layout.addWidget(progress)
        return widget


class SystemTab(QWidget):
    """System resources tab."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("💾 Systemressourcen Übersicht")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e88e5; margin-bottom: 20px;")
        layout.addWidget(header)
        
        # System metrics grid
        metrics_widget = QWidget()
        metrics_layout = QGridLayout(metrics_widget)
        
        # Sample system data
        metrics = [
            ("CPU Auslastung", "42%", "#43a047", {"Kerne": "16", "Temp": "68°C", "Takt": "3.8 GHz"}),
            ("RAM Nutzung", "34.2/128 GB", "#3b82f6", {"Belegt": "26.7%", "Cache": "5.8 GB", "Swap": "1.2 GB"}),
            ("GPU Auslastung", "78%", "#ffb300", {"VRAM": "8.2/24 GB", "Temp": "74°C", "Takt": "1890 MHz"}),
            ("Festplatten", "1.2/4 TB", "#8b5cf6", {"Lesen": "120 MB/s", "Schreiben": "45 MB/s", "IOPS": "850"})
        ]
        
        for i, (name, value, color, details) in enumerate(metrics):
            card = self.create_system_card(name, value, color, details)
            metrics_layout.addWidget(card, i // 2, i % 2)
        
        layout.addWidget(metrics_widget)
        self.setLayout(layout)
    
    def create_system_card(self, name: str, value: str, color: str, details: Dict[str, str]) -> QWidget:
        """Create a system metrics card."""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 20px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Header
        header = QLabel(name)
        header.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {color};")
        layout.addWidget(header)
        
        # Main value
        main_value = QLabel(value)
        main_value.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin: 10px 0;")
        layout.addWidget(main_value)
        
        # Details
        for detail_name, detail_value in details.items():
            detail_layout = QHBoxLayout()
            detail_layout.addWidget(QLabel(detail_name))
            detail_layout.addStretch()
            value_label = QLabel(detail_value)
            value_label.setStyleSheet("font-weight: bold;")
            detail_layout.addWidget(value_label)
            layout.addLayout(detail_layout)
        
        return card


class LogsTab(QWidget):
    """Logs viewer tab."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("📄 System Logs")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e88e5; margin-bottom: 20px;")
        layout.addWidget(header)
        
        # Logs container
        self.logs_widget = QWidget()
        self.logs_layout = QVBoxLayout(self.logs_widget)
        
        # Add sample logs
        self.add_log_entries()
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.logs_widget)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
            }
        """)
        
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def add_log_entries(self):
        """Add sample log entries."""
        logs = [
            ("INFO", "WhaleDetection", "Analysezyklus gestartet"),
            ("INFO", "TrendPrognose", "Marktdaten erfolgreich geladen"),
            ("WARN", "OrderbuchAnalyse", "Ungewöhnliche Volatilität erkannt"),
            ("INFO", "System", "GPU-Beschleunigung aktiv - 8.5% Auslastung"),
            ("ERROR", "Datenbank", "Verbindungsfehler zu ClickHouse")
        ]
        
        for level, source, message in logs:
            self.add_log_entry(level, source, message)
    
    def add_log_entry(self, level: str, source: str, message: str):
        """Add a single log entry."""
        from datetime import datetime
        
        entry = QWidget()
        entry.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(entry)
        
        # Timestamp
        timestamp = QLabel(datetime.now().strftime("%H:%M:%S"))
        timestamp.setStyleSheet("color: #aaa; font-family: monospace; min-width: 60px;")
        layout.addWidget(timestamp)
        
        # Level
        level_label = QLabel(level)
        level_label.setFixedWidth(50)
        
        if level == "INFO":
            level_label.setStyleSheet("color: #3b82f6; font-weight: bold;")
        elif level == "WARN":
            level_label.setStyleSheet("color: #ffb300; font-weight: bold;")
        elif level == "ERROR":
            level_label.setStyleSheet("color: #e53935; font-weight: bold;")
        
        layout.addWidget(level_label)
        
        # Source
        source_label = QLabel(source)
        source_label.setStyleSheet("color: #1e88e5; font-weight: bold; min-width: 120px;")
        layout.addWidget(source_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setStyleSheet("color: white;")
        layout.addWidget(message_label)
        layout.addStretch()
        
        self.logs_layout.addWidget(entry)
    
    def setup_timer(self):
        """Setup timer for adding new logs."""
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.add_random_log)
        self.log_timer.start(5000)  # Add log every 5 seconds
    
    def add_random_log(self):
        """Add a random log entry."""
        import random
        
        levels = ["INFO", "WARN", "ERROR", "DEBUG"]
        sources = ["System", "WhaleDetection", "TrendPrognose", "Backend", "Database"]
        messages = [
            "Neuer Job gestartet",
            "Datenbankverbindung hergestellt",
            "GPU-Temperatur: 72°C",
            "Cache aktualisiert",
            "WebSocket-Verbindung aktiv",
            "Berechnungslatenz: 38ms"
        ]
        
        level = random.choice(levels)
        source = random.choice(sources)
        message = random.choice(messages)
        
        self.add_log_entry(level, source, message)


class TestHistoryTab(QWidget):
    """Test History and Status Logs tab."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🧪 Test History & Status")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e88e5;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # Test controls
        run_tests_btn = QPushButton("▶️ Tests ausführen")
        clear_history_btn = QPushButton("🗑️ History löschen")
        
        for btn in [run_tests_btn, clear_history_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e88e5;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
        
        header_layout.addWidget(run_tests_btn)
        header_layout.addWidget(clear_history_btn)
        
        layout.addWidget(QWidget())  # Spacer
        layout.itemAt(0).widget().setLayout(header_layout)
        layout.itemAt(0).widget().setFixedHeight(60)
        
        # Current test status
        self.status_widget = self.create_status_widget()
        layout.addWidget(self.status_widget)
        
        # Test history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Zeit", "Test", "Status", "Dauer", "Typ", "Details"
        ])
        
        # Style table
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QTableWidget::item:selected {
                background-color: #2a2a2a;
            }
            QHeaderView::section {
                background-color: #0a0a0a;
                color: #aaa;
                border: 1px solid #3d3d3d;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # Populate with sample test history
        self.populate_test_history()
        
        layout.addWidget(self.history_table)
        self.setLayout(layout)
    
    def create_status_widget(self) -> QWidget:
        """Create current test status widget."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        
        # Overall status
        self.overall_status = QLabel("🟢 Alle Tests bestanden")
        self.overall_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #43a047;")
        layout.addWidget(self.overall_status)
        
        layout.addStretch()
        
        # Last test time
        self.last_test_time = QLabel("Letzte Tests: vor 5 Minuten")
        self.last_test_time.setStyleSheet("color: #aaa; font-size: 14px;")
        layout.addWidget(self.last_test_time)
        
        # Next test time  
        self.next_test_time = QLabel("Nächste Tests: in 5 Minuten")
        self.next_test_time.setStyleSheet("color: #aaa; font-size: 14px; margin-left: 20px;")
        layout.addWidget(self.next_test_time)
        
        return widget
    
    def populate_test_history(self):
        """Populate test history table with sample data."""
        from datetime import datetime, timedelta
        
        tests = [
            ("12:10:30", "Docker Compose Services", "🟢 PASSED", "2.3s", "Infrastructure", "Alle Services laufen"),
            ("12:10:28", "ClickHouse Database", "🟢 PASSED", "0.8s", "Infrastructure", "Verbindung erfolgreich"),
            ("12:10:25", "Health Endpoints", "🟢 PASSED", "1.2s", "Backend API", "Alle Endpoints erreichbar"),
            ("12:10:22", "WebSocket Core", "🟢 PASSED", "3.1s", "WebSocket", "Ping-Pong erfolgreich"),
            ("12:10:18", "Latency Tests", "🟡 WARNING", "5.4s", "Latency", "Erhöhte Latenz: 78ms"),
            ("12:10:12", "Concurrent Connections", "🟢 PASSED", "8.7s", "Concurrent", "100 gleichzeitige Verbindungen"),
            ("12:05:45", "Bitget API Connectivity", "🟢 PASSED", "1.9s", "Bitget API", "API erreichbar"),
            ("12:05:42", "Bitget API Latency", "🔴 FAILED", "10.0s", "Bitget API", "Timeout nach 10s"),
            ("12:00:30", "Docker Compose Services", "🟢 PASSED", "2.1s", "Infrastructure", "Alle Services laufen"),
            ("12:00:28", "ClickHouse Database", "🟢 PASSED", "0.7s", "Infrastructure", "Verbindung erfolgreich"),
        ]
        
        self.history_table.setRowCount(len(tests))
        
        for row, test in enumerate(tests):
            for col, value in enumerate(test):
                item = QTableWidgetItem(str(value))
                
                # Color coding for status
                if col == 2:  # Status column
                    if "PASSED" in value:
                        item.setForeground(QColor("#43a047"))
                    elif "WARNING" in value:
                        item.setForeground(QColor("#ffb300"))
                    elif "FAILED" in value:
                        item.setForeground(QColor("#e53935"))
                
                # Color coding for test type
                if col == 4:  # Type column
                    if "Infrastructure" in value:
                        item.setForeground(QColor("#3b82f6"))
                    elif "Backend API" in value:
                        item.setForeground(QColor("#1e88e5"))
                    elif "Bitget API" in value:
                        item.setForeground(QColor("#ffb300"))
                
                self.history_table.setItem(row, col, item)
        
        # Adjust column widths
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Zeit
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Test
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Dauer
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Typ
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Details
    
    def setup_timer(self):
        """Setup timer for updating test status."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_test_status)
        self.update_timer.start(30000)  # Update every 30 seconds
        
        # Also update immediately
        self.update_test_status()
    
    def update_test_status(self):
        """Update test status display."""
        import random
        from datetime import datetime, timedelta
        
        # Simulate test status updates
        statuses = [
            ("🟢 Alle Tests bestanden", "#43a047"),
            ("🟡 Einige Tests mit Warnungen", "#ffb300"),  
            ("🔴 Kritische Tests fehlgeschlagen", "#e53935")
        ]
        
        # Mostly show success status
        weights = [0.7, 0.2, 0.1]
        status_text, color = random.choices(statuses, weights=weights)[0]
        
        self.overall_status.setText(status_text)
        self.overall_status.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        
        # Update times
        last_minutes = random.randint(1, 15)
        next_minutes = random.randint(5, 15)
        
        self.last_test_time.setText(f"Letzte Tests: vor {last_minutes} Minuten")
        self.next_test_time.setText(f"Nächste Tests: in {next_minutes} Minuten")
    
    def add_test_result(self, test_name: str, status: str, duration: float, test_type: str, details: str):
        """Add a new test result to the history."""
        from datetime import datetime
        
        # Insert at top
        self.history_table.insertRow(0)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        duration_str = f"{duration:.1f}s"
        
        # Map status to display format
        status_map = {
            "passed": "🟢 PASSED",
            "failed": "🔴 FAILED", 
            "warning": "🟡 WARNING",
            "timeout": "🔴 TIMEOUT"
        }
        status_display = status_map.get(status, f"❓ {status.upper()}")
        
        values = [timestamp, test_name, status_display, duration_str, test_type, details]
        
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            
            # Color coding
            if col == 2:  # Status column
                if "PASSED" in value:
                    item.setForeground(QColor("#43a047"))
                elif "WARNING" in value:
                    item.setForeground(QColor("#ffb300"))
                elif "FAILED" in value or "TIMEOUT" in value:
                    item.setForeground(QColor("#e53935"))
            
            self.history_table.setItem(0, col, item)
        
        # Limit history to 50 entries
        if self.history_table.rowCount() > 50:
            self.history_table.removeRow(50)


class SettingsTab(QWidget):
    """Settings tab."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("⚙️ Einstellungen")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e88e5; margin-bottom: 20px;")
        layout.addWidget(header)
        
        # Settings content
        settings_label = QLabel("Einstellungen werden hier implementiert...")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_label.setStyleSheet("color: #aaa; font-size: 16px; margin: 50px;")
        layout.addWidget(settings_label)
        
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    close_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.apply_dark_theme()
    
    def setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle("DarkMa Trading Manager")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # Add tabs
        self.tab_widget.addTab(JobsTab(), "📋 Jobs")
        self.tab_widget.addTab(WorkersTab(), "🖥️ Worker/Nodes")
        self.tab_widget.addTab(SystemTab(), "💾 System")
        self.tab_widget.addTab(TestHistoryTab(), "🧪 Test History")
        self.tab_widget.addTab(LogsTab(), "📄 Logs")
        self.tab_widget.addTab(SettingsTab(), "⚙️ Settings")
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)
    
    def create_top_bar(self) -> QWidget:
        """Create the top bar with title and controls."""
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("""
            QWidget {
                background-color: #0a0a0a;
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title = QLabel("🧠 DarkMa Trading Manager")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e88e5;")
        layout.addWidget(title)
        layout.addStretch()
        
        # System indicators
        indicators = [
            ("CPU: 24%", "#43a047"),
            ("RAM: 3.4/128 GB", "#3b82f6"),
            ("GPU: 18%", "#ffb300")
        ]
        
        for text, color in indicators:
            indicator = QLabel(text)
            indicator.setStyleSheet(f"color: {color}; font-size: 12px; margin-left: 15px;")
            layout.addWidget(indicator)
        
        # User info
        user = QLabel("👤 John Doe")
        user.setStyleSheet("color: white; font-size: 14px; margin-left: 20px;")
        layout.addWidget(user)
        
        return top_bar
    
    def create_status_bar(self) -> QWidget:
        """Create the status bar with latency and test status indicators."""
        status_bar = QWidget()
        status_bar.setFixedHeight(35)
        status_bar.setStyleSheet("""
            QWidget {
                background-color: #0a0a0a;
                border-top: 1px solid #3d3d3d;
            }
        """)
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(20, 5, 20, 5)
        
        # Left side - General status items
        left_layout = QHBoxLayout()
        status_items = [
            "💿 2.92 GB / 20.95 GB",
            "🔄 Letzte Aktualisierung: vor 0 Sekunden",
            "🛡️ JWT Authentifiziert"
        ]
        
        for item in status_items:
            label = QLabel(item)
            label.setStyleSheet("color: #aaa; font-size: 11px;")
            left_layout.addWidget(label)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Right side - Latency and Test status indicators
        right_layout = QHBoxLayout()
        right_layout.setSpacing(15)
        
        # Latency indicators
        self.latency_widget = self.create_latency_indicators()
        right_layout.addWidget(self.latency_widget)
        
        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #3d3d3d; font-size: 12px;")
        right_layout.addWidget(separator)
        
        # Test status indicators
        self.test_status_widget = self.create_test_status_indicators()
        right_layout.addWidget(self.test_status_widget)
        
        # Another separator
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #3d3d3d; font-size: 12px;")
        right_layout.addWidget(separator2)
        
        # Copyright
        copyright = QLabel("© 2023 DarkMa Manager")
        copyright.setStyleSheet("color: #aaa; font-size: 11px;")
        right_layout.addWidget(copyright)
        
        layout.addLayout(right_layout)
        
        # Setup timer for status updates
        self.setup_status_timers()
        
        return status_bar
    
    def create_latency_indicators(self) -> QWidget:
        """Create latency status indicators."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Backend latency
        self.backend_latency = QLabel("🔗 Backend: 28ms")
        self.backend_latency.setStyleSheet("color: #43a047; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.backend_latency)
        
        # Database latency
        self.db_latency = QLabel("💾 DB: 12ms")
        self.db_latency.setStyleSheet("color: #43a047; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.db_latency)
        
        # API latency
        self.api_latency = QLabel("🌐 API: 45ms")
        self.api_latency.setStyleSheet("color: #ffb300; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.api_latency)
        
        return widget
    
    def create_test_status_indicators(self) -> QWidget:
        """Create test status indicators."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Overall test status
        self.test_status = QLabel("🧪 Tests: 🟢 OK")
        self.test_status.setStyleSheet("color: #43a047; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.test_status)
        
        # Last test run time
        self.last_test_run = QLabel("⏱️ vor 3min")
        self.last_test_run.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.last_test_run)
        
        # Infrastructure status
        self.infra_status = QLabel("🏗️ Infra: ✅")
        self.infra_status.setStyleSheet("color: #43a047; font-size: 11px;")
        layout.addWidget(self.infra_status)
        
        # Backend API status  
        self.backend_api_status = QLabel("🔌 API: ✅")
        self.backend_api_status.setStyleSheet("color: #43a047; font-size: 11px;")
        layout.addWidget(self.backend_api_status)
        
        return widget
    
    def setup_status_timers(self):
        """Setup timers for updating status indicators."""
        # Timer for latency updates (every 5 seconds)
        self.latency_timer = QTimer()
        self.latency_timer.timeout.connect(self.update_latency_indicators)
        self.latency_timer.start(5000)
        
        # Timer for test status updates (every 30 seconds)
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.update_test_status_indicators)
        self.test_timer.start(30000)
        
        # Initial updates
        self.update_latency_indicators()
        self.update_test_status_indicators()
    
    def update_latency_indicators(self):
        """Update latency indicators with simulated data."""
        import random
        
        # Backend latency (20-80ms)
        backend_ms = random.randint(20, 80)
        backend_color = "#43a047" if backend_ms < 50 else "#ffb300" if backend_ms < 70 else "#e53935"
        self.backend_latency.setText(f"🔗 Backend: {backend_ms}ms")
        self.backend_latency.setStyleSheet(f"color: {backend_color}; font-size: 11px; font-weight: bold;")
        
        # Database latency (5-30ms)
        db_ms = random.randint(5, 30)
        db_color = "#43a047" if db_ms < 20 else "#ffb300" if db_ms < 25 else "#e53935"
        self.db_latency.setText(f"💾 DB: {db_ms}ms")
        self.db_latency.setStyleSheet(f"color: {db_color}; font-size: 11px; font-weight: bold;")
        
        # API latency (30-120ms)
        api_ms = random.randint(30, 120)
        api_color = "#43a047" if api_ms < 60 else "#ffb300" if api_ms < 90 else "#e53935"
        self.api_latency.setText(f"🌐 API: {api_ms}ms")
        self.api_latency.setStyleSheet(f"color: {api_color}; font-size: 11px; font-weight: bold;")
    
    def update_test_status_indicators(self):
        """Update test status indicators with simulated data."""
        import random
        
        # Overall test status (mostly positive)
        status_options = [
            ("🧪 Tests: 🟢 OK", "#43a047", 0.8),
            ("🧪 Tests: 🟡 WARN", "#ffb300", 0.15),
            ("🧪 Tests: 🔴 FAIL", "#e53935", 0.05)
        ]
        
        status_text, color, _ = random.choices(
            status_options, 
            weights=[opt[2] for opt in status_options]
        )[0]
        
        self.test_status.setText(status_text)
        self.test_status.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        
        # Last test run time
        minutes_ago = random.randint(1, 15)
        self.last_test_run.setText(f"⏱️ vor {minutes_ago}min")
        
        # Infrastructure status
        infra_options = ["✅", "⚠️", "❌"]
        infra_colors = ["#43a047", "#ffb300", "#e53935"]
        infra_weights = [0.85, 0.1, 0.05]
        
        infra_icon = random.choices(infra_options, weights=infra_weights)[0]
        infra_color = infra_colors[infra_options.index(infra_icon)]
        
        self.infra_status.setText(f"🏗️ Infra: {infra_icon}")
        self.infra_status.setStyleSheet(f"color: {infra_color}; font-size: 11px;")
        
        # Backend API status
        api_icon = random.choices(infra_options, weights=infra_weights)[0]
        api_color = infra_colors[infra_options.index(api_icon)]
        
        self.backend_api_status.setText(f"🔌 API: {api_icon}")
        self.backend_api_status.setStyleSheet(f"color: {api_color}; font-size: 11px;")
    
    def apply_dark_theme(self):
        """Apply dark theme to the main window."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
                color: #f5f5f5;
            }
            
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #121212;
            }
            
            QTabWidget::tab-bar {
                left: 5px;
            }
            
            QTabBar::tab {
                background-color: #1e1e1e;
                color: #aaa;
                border: 1px solid #3d3d3d;
                padding: 12px 20px;
                margin: 1px 0;
                min-width: 120px;
            }
            
            QTabBar::tab:selected {
                background-color: #2a2a2a;
                color: #1e88e5;
                border-left: 3px solid #1e88e5;
            }
            
            QTabBar::tab:hover {
                background-color: #2a2a2a;
                color: #f5f5f5;
            }
            
            QWidget {
                background-color: #121212;
                color: #f5f5f5;
            }
            
            QLabel {
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
        """)
    
    def closeEvent(self, event):
        """Handle close event."""
        self.close_requested.emit()
        event.ignore()  # Let the application handle the close
