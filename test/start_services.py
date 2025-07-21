#!/usr/bin/env python3
"""
EINFACHER SERVICE STARTER
Startet nur Docker Services - keine Tests, kein Menü, kein Bullshit
"""

import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def run_command(cmd, cwd=None):
    """Führt einen Befehl aus"""
    try:
        print(f"🔄 {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {e}")
        return False

def main():
    print("🚀 Setup Virtual Environment und Services...")
    
    # 1. Virtual Environment erstellen/aktivieren
    venv_path = BASE_DIR / "test_venv"
    if not venv_path.exists():
        print("📦 Erstelle Virtual Environment...")
        run_command("python3 -m venv test_venv", cwd=BASE_DIR)
    
    # 2. Requirements installieren (nur die einfachen ohne scipy)
    print("📦 Installiere Requirements (ohne problematische Pakete)...")
    pip_cmd = f"{venv_path}/bin/pip"
    run_command(f"{pip_cmd} install requests selenium pytest httpx", cwd=BASE_DIR)
    
    # 3. Docker Services starten
    print("🚀 Starte Docker Services...")
    success = run_command("docker-compose up -d clickhouse-bolt redis-bolt backend_bolt frontend_bolt", cwd=BASE_DIR)
    
    if not success:
        print("❌ Docker Start fehlgeschlagen!")
        return
    
    print("✅ Docker Services gestartet!")
    print("⏳ Warte 10 Sekunden...")
    time.sleep(10)
    
    # Status anzeigen
    print("\n📊 SERVICE STATUS:")
    run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    
    print("\n🎉 FERTIG!")
    print("💡 Tests ausführen:")
    print("   cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI")
    print("   python3 test/05_bitget_system/simple_bitget_test.py")
    print("   python3 test/05_bitget_system/frontend_performance_tester.py  # Selenium jetzt verfügbar!")

if __name__ == "__main__":
    main()
