#!/usr/bin/env python3
"""
Test-Script für deinen ursprünglichen curl Command
curl -s http://localhost:8100/symbols (statt symbolsCheckpoint)
Mit limitierten Daten um Token-Limits zu vermeiden.
"""
import requests
import json
import subprocess
import sys
from datetime import datetime

def test_curl_command():
    """
    Testet den ursprünglichen curl command mit limitierten Daten
    """
    print("=" * 60)
    print("🧪 CURL SYMBOLS LIMITED TEST")  
    print("=" * 60)
    print("Original Command: curl -s http://localhost:8100/symbols")
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    try:
        # Curl command ausführen (wie in deiner ursprünglichen Nachricht)
        print("🔄 Executing: curl -s http://localhost:8100/symbols")
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8100/symbols"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ Curl failed with return code: {result.returncode}")
            print(f"❌ Error: {result.stderr}")
            return False
            
        # JSON parsen
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            print(f"❌ Response preview: {result.stdout[:200]}...")
            return False
        
        # Original-Datenmengen anzeigen
        original_symbols_count = len(data.get("symbols", []))
        original_db_symbols_count = len(data.get("db_symbols", []))
        
        print(f"✅ Curl successful! Data received:")
        print(f"   - API Symbols: {original_symbols_count}")
        print(f"   - DB Symbols: {original_db_symbols_count}")
        
        # Hier würde normalerweise das Token-Limit-Problem auftreten!
        full_response_size = len(result.stdout.encode('utf-8')) / 1024
        print(f"   - Full response size: {full_response_size:.2f} KB")
        
        if full_response_size > 1000:  # > 1MB könnte problematisch sein
            print(f"⚠️  WARNING: Response size could cause token limit issues!")
        
        # LÖSUNG: Daten clientseitig limitieren (wie im anderen Test)
        limit = 50
        if "symbols" in data and len(data["symbols"]) > limit:
            data["symbols"] = data["symbols"][:limit]
            print(f"✂️  Limited API symbols from {original_symbols_count} to {len(data['symbols'])}")
        
        if "db_symbols" in data and len(data["db_symbols"]) > limit:
            data["db_symbols"] = data["db_symbols"][:limit]
            print(f"✂️  Limited DB symbols from {original_db_symbols_count} to {len(data['db_symbols'])}")
        
        # Limitierte Datengröße berechnen
        limited_response = json.dumps(data)
        limited_size_kb = len(limited_response.encode('utf-8')) / 1024
        
        print(f"\n📏 After limiting to {limit} symbols:")
        print(f"   - Limited response size: {limited_size_kb:.2f} KB")
        print(f"   - Symbols: {len(data.get('symbols', []))}")
        print(f"   - DB Symbols: {len(data.get('db_symbols', []))}")
        
        if limited_size_kb < 100:
            print(f"✅ Limited response is safe for token limits!")
        
        # Beispiel-Daten zeigen
        if data.get("symbols"):
            print(f"\n📋 Sample data:")
            for i, sym in enumerate(data["symbols"][:3], 1):
                symbol_name = sym.get('symbol', 'N/A')
                symbol_type = sym.get('symbolType', 'N/A')
                print(f"   {i}. {symbol_name} ({symbol_type})")
        
        print(f"\n✅ Curl test erfolgreich!")
        print(f"✅ Originaler curl-Command funktioniert mit limitierten Daten")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Curl command timeout - Backend might be slow")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_original_problem():
    """
    Demonstriert das ursprüngliche Token-Limit Problem
    """
    print("\n" + "=" * 60)
    print("🚨 ORIGINAL PROBLEM DEMONSTRATION")
    print("=" * 60)
    print("Zeige warum der ursprüngliche curl zu viele Tokens verursacht:")
    print()
    
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8100/symbols"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Zeige nur die Größe, nicht die kompletten Daten (wegen Token-Limit)
            response_size_kb = len(result.stdout.encode('utf-8')) / 1024
            response_size_mb = response_size_kb / 1024
            
            # Geschätzte Token-Anzahl (ungefähr 1 Token = 4 Zeichen)
            estimated_tokens = len(result.stdout) / 4
            
            print(f"📊 Full response metrics:")
            print(f"   - Response size: {response_size_kb:.2f} KB ({response_size_mb:.2f} MB)")
            print(f"   - Estimated tokens: {estimated_tokens:,.0f}")
            print(f"   - Token limit: 200,000")
            
            if estimated_tokens > 200000:
                print(f"❌ PROBLEM: {estimated_tokens:,.0f} tokens > 200,000 limit!")
                print(f"❌ Das ist warum die API mit 400 'prompt is too long' Fehler abbricht")
            else:
                print(f"✅ Tokens within limit")
                
            print(f"\n💡 LÖSUNG: Daten clientseitig auf 50 Symbole begrenzen")
            print(f"💡 Reduziert von ~{estimated_tokens:,.0f} auf ~2,000 Tokens")
    
    except Exception as e:
        print(f"❌ Could not analyze original problem: {e}")

def main():
    """
    Haupt-Testfunktion
    """
    # Test 1: Originaler curl command mit Lösung
    success = test_curl_command()
    
    # Test 2: Problem-Demonstration
    test_original_problem()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 CURL TEST ERFOLGREICH!")
        print("✅ Dein ursprünglicher curl-Command funktioniert jetzt")
        print("✅ Token-Limit-Problem gelöst durch clientseitige Limitierung")
        print()
        print("💡 Verwendung:")
        print("   curl -s http://localhost:8100/symbols | python -c \"")
        print("   import json, sys; data=json.load(sys.stdin);")
        print("   data['symbols']=data['symbols'][:50]; print(json.dumps(data))\"")
    else:
        print("❌ CURL TEST FEHLGESCHLAGEN!")
        print("🛠️  Überprüfe Backend-Status mit: docker ps")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
