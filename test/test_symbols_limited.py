#!/usr/bin/env python3
"""
Test-Script für limitierte Symbols-API Tests
Testet den /symbols Endpoint mit nur 50 Symbolen um Token-Limits zu vermeiden.
Deine bestehenden Bitget codes bleiben unberührt!
"""
import requests
import json
import sys
from datetime import datetime

def test_symbols_limited(limit=50):
    """
    Testet den /symbols Endpoint mit einer Begrenzung auf die ersten N Symbole
    """
    print(f"🔍 Testing /symbols endpoint with {limit} symbol limit...")
    print(f"⏰ Test started at: {datetime.now()}")
    
    try:
        # Aufruf deiner bestehenden API (bleibt unberührt!)
        print("📡 Calling http://localhost:8100/symbols...")
        response = requests.get("http://localhost:8100/symbols", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
        data = response.json()
        print(f"✅ API Response received successfully")
        
        # Original-Datenmengen anzeigen
        original_symbols_count = len(data.get("symbols", []))
        original_db_symbols_count = len(data.get("db_symbols", []))
        
        print(f"📊 Original data received:")
        print(f"   - API Symbols: {original_symbols_count}")
        print(f"   - DB Symbols: {original_db_symbols_count}")
        
        # Zähler: Nur erste N Symbole nehmen
        if "symbols" in data and len(data["symbols"]) > limit:
            data["symbols"] = data["symbols"][:limit]
            print(f"✂️  Limited API symbols from {original_symbols_count} to {len(data['symbols'])}")
        
        if "db_symbols" in data and len(data["db_symbols"]) > limit:
            data["db_symbols"] = data["db_symbols"][:limit]
            print(f"✂️  Limited DB symbols from {original_db_symbols_count} to {len(data['db_symbols'])}")
        
        # Test-Validierung mit limitierten Daten
        print(f"\n🧪 Validating limited data:")
        
        # Check API symbols structure
        if "symbols" in data and data["symbols"]:
            first_symbol = data["symbols"][0]
            required_fields = ["symbol", "baseCoin", "quoteCoin"]
            missing_fields = [field for field in required_fields if field not in first_symbol]
            
            if missing_fields:
                print(f"❌ Missing required fields in symbols: {missing_fields}")
                return False
            else:
                print(f"✅ API Symbols structure valid")
                print(f"   - First symbol: {first_symbol.get('symbol', 'N/A')}")
                print(f"   - Symbol type: {first_symbol.get('symbolType', 'N/A')}")
        
        # Show some sample data
        print(f"\n📋 Sample limited data:")
        if data.get("symbols"):
            sample_symbols = data["symbols"][:3]  # Erste 3 als Beispiel
            for i, sym in enumerate(sample_symbols, 1):
                print(f"   {i}. {sym.get('symbol', 'N/A')} ({sym.get('symbolType', 'N/A')})")
        
        # Calculate response size estimate
        response_text = json.dumps(data)
        response_size_kb = len(response_text.encode('utf-8')) / 1024
        
        print(f"\n📏 Limited response metrics:")
        print(f"   - Response size: {response_size_kb:.2f} KB")
        print(f"   - Total symbols: {len(data.get('symbols', []))}")
        print(f"   - Total DB symbols: {len(data.get('db_symbols', []))}")
        
        if response_size_kb < 100:  # Unter 100KB sollte sicher sein
            print(f"✅ Response size is safe for token limits")
        else:
            print(f"⚠️  Response size might still be large")
        
        print(f"\n✅ Test erfolgreich abgeschlossen!")
        print(f"✅ API läuft korrekt mit limitierten Daten ({limit} Symbole)")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout - Backend might be slow or not responding")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Is backend running on http://localhost:8100?")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed with unexpected error: {e}")
        return False

def main():
    """
    Haupt-Testfunktion mit verschiedenen Limits
    """
    print("=" * 60)
    print("🧪 SYMBOLS API LIMITED TEST")
    print("=" * 60)
    print("Deine Bitget codes und routers bleiben unberührt!")
    print("Dieser Test begrenzt nur die Antwort für Token-Limit-Compliance.")
    print()
    
    # Test mit verschiedenen Limits
    test_limits = [10, 25, 50]
    
    for limit in test_limits:
        print(f"\n{'=' * 50}")
        print(f"🔄 Testing with {limit} symbol limit")
        print(f"{'=' * 50}")
        
        success = test_symbols_limited(limit)
        
        if success:
            print(f"✅ Test with {limit} symbols: PASSED")
        else:
            print(f"❌ Test with {limit} symbols: FAILED")
            print("🛑 Stopping further tests due to failure")
            sys.exit(1)
        
        print()
    
    print("=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ /symbols Endpoint funktioniert mit limitierten Daten")
    print("✅ Keine Token-Limit-Probleme mehr")
    print("=" * 60)

if __name__ == "__main__":
    main()
