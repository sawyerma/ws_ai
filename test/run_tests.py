#!/usr/bin/env python3
"""
Systematischer Test-Runner für das komplette System
Startet Docker, aktiviert venv, bietet Test-Auswahl
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Basis-Pfade
BASE_DIR = Path(__file__).parent.parent
TEST_DIR = Path(__file__).parent
VENV_DIR = BASE_DIR / "test_venv"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestRunner:
    def __init__(self):
        self.docker_started = False
        self.venv_activated = False
        
    def print_header(self, title):
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}{Colors.END}\n")
        
    def print_success(self, msg):
        print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
        
    def print_error(self, msg):
        print(f"{Colors.RED}❌ {msg}{Colors.END}")
        
    def print_info(self, msg):
        print(f"{Colors.BLUE}🔄 {msg}{Colors.END}")
        
    def run_command(self, cmd, cwd=None, capture_output=False):
        """Führt einen Befehl aus"""
        try:
            if capture_output:
                result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(cmd, shell=True, cwd=cwd)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)
            
    def check_docker_running(self):
        """Prüft ob Docker läuft"""
        success, stdout, stderr = self.run_command("docker ps", capture_output=True)
        return success
        
    def start_docker_compose(self):
        """Startet Docker Compose"""
        self.print_info("Starte Docker Compose...")
        
        if not self.check_docker_running():
            self.print_error("Docker ist nicht gestartet. Bitte Docker starten!")
            return False
            
        # Docker Compose starten
        success, stdout, stderr = self.run_command("docker-compose up -d", cwd=BASE_DIR, capture_output=True)
        if success:
            self.print_success("Docker Compose gestartet")
            self.docker_started = True
            
            # Warten bis Services bereit sind
            self.print_info("Warte auf Services...")
            time.sleep(10)
            
            # ClickHouse Status prüfen
            success, stdout, stderr = self.run_command("docker ps | grep clickhouse", capture_output=True)
            if success and "clickhouse" in stdout:
                self.print_success("ClickHouse läuft")
            else:
                self.print_error("ClickHouse nicht gefunden")
                
            # Redis Status prüfen  
            success, stdout, stderr = self.run_command("docker ps | grep redis", capture_output=True)
            if success and "redis" in stdout:
                self.print_success("Redis läuft")
            else:
                self.print_error("Redis nicht gefunden")
                
            return True
        else:
            self.print_error(f"Docker Compose Start fehlgeschlagen: {stderr}")
            return False
            
    def setup_venv(self):
        """Setup Virtual Environment"""
        self.print_info("Setup Virtual Environment...")
        
        # Virtual Environment aktivieren und Requirements installieren
        if os.name == 'nt':  # Windows
            pip_cmd = f"{VENV_DIR}/Scripts/pip"
            python_cmd = f"{VENV_DIR}/Scripts/python"
        else:  # Unix/Linux/macOS
            pip_cmd = f"{VENV_DIR}/bin/pip"
            python_cmd = f"{VENV_DIR}/bin/python"
            
        # Requirements installieren falls nicht vorhanden
        success, stdout, stderr = self.run_command(f"{pip_cmd} install -r requirements.txt", cwd=BASE_DIR, capture_output=True)
        if success:
            self.print_success("Requirements installiert")
            self.venv_activated = True
            return python_cmd
        else:
            self.print_error(f"Requirements Installation fehlgeschlagen: {stderr}")
            return None
            
    def run_pytest(self, python_cmd, test_path, extra_args=""):
        """Führt pytest aus"""
        cmd = f"{python_cmd} -m pytest {test_path} -v {extra_args}"
        self.print_info(f"Führe aus: {cmd}")
        
        success, stdout, stderr = self.run_command(cmd, cwd=BASE_DIR)
        return success
    
    def run_performance_tests(self, python_cmd):
        """Führt spezielle Performance Tests aus"""
        self.print_info("🚀 Starte Performance Test Suite...")
        
        # Performance Tests Menu
        perf_tests = [
            ("1", "Pipeline Performance Test (Redis + Backend)", "test/05_bitget_system/test_full_pipeline_performance.py"),
            ("2", "Frontend Performance Test (Browser + DOM)", "test/05_bitget_system/frontend_performance_tester.py"),
            ("3", "Beide Performance Tests", "both"),
            ("b", "Zurück zum Hauptmenü", "back")
        ]
        
        while True:
            print(f"\n{Colors.CYAN}{Colors.BOLD}🚀 PERFORMANCE TEST AUSWAHL{Colors.END}")
            print(f"{Colors.BOLD}Verfügbare Performance Tests:{Colors.END}")
            
            for num, name, _ in perf_tests:
                print(f"{Colors.YELLOW}{num}{Colors.END}. {name}")
            
            choice = input(f"\n{Colors.CYAN}Wählen Sie einen Performance Test (1-3, b zurück): {Colors.END}").lower().strip()
            
            if choice == 'b':
                return True
            
            selected_test = next((test for test in perf_tests if test[0] == choice), None)
            if not selected_test:
                self.print_error("Ungültige Auswahl!")
                continue
            
            test_num, test_name, test_path = selected_test
            
            self.print_header(f"🚀 PERFORMANCE TEST: {test_name}")
            
            success = True
            
            if test_path == "both":
                # Führe beide Tests aus
                self.print_info("🔄 Starte Pipeline Performance Test...")
                success1 = self.run_command(f"{python_cmd} test/05_bitget_system/test_full_pipeline_performance.py", cwd=BASE_DIR)
                
                if success1[0]:
                    self.print_success("Pipeline Performance Test abgeschlossen")
                    time.sleep(2)
                    
                    # Installiere Selenium falls nicht vorhanden
                    self.print_info("🔄 Installiere Selenium für Frontend Tests...")
                    self.run_command(f"{python_cmd.replace('python', 'pip')} install selenium", cwd=BASE_DIR, capture_output=True)
                    
                    self.print_info("🔄 Starte Frontend Performance Test...")
                    success2 = self.run_command(f"{python_cmd} test/05_bitget_system/frontend_performance_tester.py", cwd=BASE_DIR)
                    success = success1[0] and success2[0]
                else:
                    success = False
                    
            elif test_path.endswith("frontend_performance_tester.py"):
                # Frontend Test - installiere Selenium
                self.print_info("🔄 Installiere Selenium für Frontend Tests...")
                self.run_command(f"{python_cmd.replace('python', 'pip')} install selenium", cwd=BASE_DIR, capture_output=True)
                success, _, _ = self.run_command(f"{python_cmd} {test_path}", cwd=BASE_DIR)
                
            else:
                # Standard Performance Test
                success, _, _ = self.run_command(f"{python_cmd} {test_path}", cwd=BASE_DIR)
            
            if success:
                self.print_success(f"Performance Test '{test_name}' erfolgreich!")
            else:
                self.print_error(f"Performance Test '{test_name}' fehlgeschlagen!")
            
            input(f"\n{Colors.CYAN}Drücken Sie Enter um fortzufahren...{Colors.END}")
        
        return True
        
    def show_menu(self):
        """Zeigt Test-Auswahl-Menü"""
        tests = [
            ("1", "Infrastructure Tests", "test/01_infrastructure/"),
            ("2", "Backend API Tests", "test/02_backend_api/"),
            ("3", "Frontend API Tests", "test/03_frontend_api/"),
            ("4", "Whale System Tests", "test/04_whale_system/"),
            ("5", "Bitget System Tests", "test/05_bitget_system/"),
            ("6", "System Integration Tests", "test/06_system_integration/"),
            ("p", "🚀 Performance Tests (Redis + Frontend)", "performance"),
            ("a", "Alle Tests", "test/"),
            ("q", "Beenden", "")
        ]
        
        while True:
            self.print_header("TEST AUSWAHL")
            print(f"{Colors.BOLD}Verfügbare Tests:{Colors.END}")
            
            for num, name, path in tests:
                print(f"{Colors.YELLOW}{num}{Colors.END}. {name}")
                
            choice = input(f"\n{Colors.CYAN}Wählen Sie einen Test (1-6, a für alle, q zum Beenden): {Colors.END}").lower().strip()
            
            if choice == 'q':
                break
                
            # Finde gewählten Test
            selected_test = next((test for test in tests if test[0] == choice), None)
            if not selected_test:
                self.print_error("Ungültige Auswahl!")
                continue
                
            test_num, test_name, test_path = selected_test
            
            if test_path:  # Nicht bei "Beenden"
                self.print_header(f"FÜHRE AUS: {test_name}")
                
                # Virtual Environment Setup
                python_cmd = self.setup_venv()
                if not python_cmd:
                    continue
                    
                # Spezielle Behandlung für Performance Tests
                if test_path == "performance":
                    success = self.run_performance_tests(python_cmd)
                else:
                    # Standard pytest ausführen
                    success = self.run_pytest(python_cmd, test_path)
                
                if success:
                    self.print_success(f"Test '{test_name}' erfolgreich abgeschlossen!")
                else:
                    self.print_error(f"Test '{test_name}' fehlgeschlagen!")
                    
                input(f"\n{Colors.CYAN}Drücken Sie Enter um fortzufahren...{Colors.END}")
                
    def cleanup(self):
        """Cleanup beim Beenden"""
        if self.docker_started:
            self.print_info("Docker Compose wird gestoppt...")
            self.run_command("docker-compose down", cwd=BASE_DIR)
            
    def run(self):
        """Hauptfunktion"""
        try:
            self.print_header("SYSTEM TEST RUNNER")
            
            # Docker starten
            if not self.start_docker_compose():
                return False
                
            # Test-Menü anzeigen
            self.show_menu()
            
        except KeyboardInterrupt:
            self.print_info("\nTest Runner wird beendet...")
        finally:
            self.cleanup()
            
        return True

def main():
    """Main Funktion"""
    # Signal Handler für sauberen Exit
    def signal_handler(sig, frame):
        print(f"\n{Colors.YELLOW}Signal {sig} erhalten. Beende...{Colors.END}")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Test Runner starten
    runner = TestRunner()
    runner.run()

if __name__ == "__main__":
    main()
