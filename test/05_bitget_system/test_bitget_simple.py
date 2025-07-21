"""
Einfacher Test für Bitget Integration
"""
import asyncio
import sys
import os
sys.path.insert(0, 'backend')

async def test_bitget_integration():
    print('🔄 Teste Bitget Integration...')
    
    # Test 1: Konfiguration
    try:
        from market.bitget.config import bitget_config, system_config
        print('✅ Konfiguration geladen')
        print(f'   - Free Tier aktiv: {not bitget_config.is_premium}')
        print(f'   - Max RPS: {bitget_config.effective_max_rps}')
        print(f'   - Symbole pro Verbindung: {bitget_config.max_symbols_per_connection}')
    except Exception as e:
        print(f'❌ Konfigurationsfehler: {e}')
        return
    
    # Test 2: REST API
    try:
        from market.bitget.services.bitget_rest import BitgetRestAPI
        api = BitgetRestAPI()
        
        print('📊 Teste Spot Symbole...')
        symbols_response = await api.fetch_spot_symbols()
        
        if symbols_response and symbols_response.get('code') == '00000':
            symbols = symbols_response.get('data', [])
            print(f'✅ {len(symbols)} Spot Symbole geladen')
            
            # Prüfe BTCUSDT
            btc_found = any(s.get('symbol') == 'BTCUSDT' for s in symbols)
            print(f'   - BTCUSDT verfügbar: {btc_found}')
            
        else:
            print(f'❌ Symbole Fehler: {symbols_response}')
        
        print('📈 Teste Spot Ticker...')
        ticker_response = await api.fetch_spot_tickers()
        
        if ticker_response and ticker_response.get('code') == '00000':
            tickers = ticker_response.get('data', [])
            print(f'✅ {len(tickers)} Ticker geladen')
            
            # Finde BTCUSDT Ticker
            btc_ticker = next((t for t in tickers if t.get('symbol') == 'BTCUSDT'), None)
            if btc_ticker:
                price = btc_ticker.get('lastPr', 'N/A')
                volume = btc_ticker.get('baseVolume', 'N/A')
                print(f'   - BTCUSDT: ${price} (Volume: {volume})')
                
        else:
            print(f'❌ Ticker Fehler: {ticker_response}')
            
        await api.close()
        print('✅ API Session geschlossen')
        
    except Exception as e:
        print(f'❌ REST API Fehler: {e}')
        import traceback
        traceback.print_exc()
    
    # Test 3: Rate Limiter
    try:
        from market.bitget.utils.adaptive_rate_limiter import get_rate_limiter
        limiter = get_rate_limiter('test-integration')
        stats = limiter.get_stats()
        print(f'✅ Rate Limiter: {stats["base_rps"]} RPS')
    except Exception as e:
        print(f'❌ Rate Limiter Fehler: {e}')
    
    # Test 4: System Config
    try:
        effective_markets = system_config.get_effective_market_types(bitget_config)
        max_symbols = system_config.get_max_symbols_per_market(bitget_config)
        resolutions = system_config.get_resolutions(bitget_config)
        
        print(f'✅ System Config:')
        print(f'   - Märkte: {effective_markets}')
        print(f'   - Max Symbole/Markt: {max_symbols}')
        print(f'   - Auflösungen: {resolutions}')
    except Exception as e:
        print(f'❌ System Config Fehler: {e}')
    
    # Test 5: Auto-Remediation
    try:
        from market.bitget.services.auto_remediation import check_system_health
        health = await check_system_health()
        print(f'✅ System Health: {health.get("status", "unknown")}')
    except Exception as e:
        print(f'❌ Health Check Fehler: {e}')
    
    print('\n🎉 Bitget Integration Test abgeschlossen')

if __name__ == '__main__':
    asyncio.run(test_bitget_integration())
