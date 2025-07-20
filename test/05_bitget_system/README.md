# Bitget System Tests

Umfassende Testsuite für das Bitget Trading System mit Live-API-Tests.

## Überblick

Dieses Testverzeichnis enthält alle Tests für die Bitget-Integration, einschließlich:
- Live-API-Verbindungstests  
- Datenbank-Integrationstests
- WebSocket-Verbindungstests
- Rate-Limiting-Tests

## Teststruktur

```
test/05_bitget_system/
├── conftest.py                      # Pytest-Konfiguration und Fixtures
├── test_bitget_api_connections.py   # Live-API-Verbindungstests
├── test_bitget_integration.py       # Integrationstests (folgt)
├── test_bitget_database.py          # Datenbanktests (folgt)
└── README.md                        # Diese Datei
```

## Vorbereitung

### 1. Umgebungsvariablen setzen

```bash
export BITGET_API_KEY=your_api_key
export BITGET_SECRET_KEY=your_secret
export BITGET_PASSPHRASE=your_passphrase
export REDIS_HOST=localhost
export REDIS_PORT=6380
export CLICKHOUSE_HOST=localhost
export CLICKHOUSE_PORT=8123
```

### 2. Docker-Container starten

```bash
# Stelle sicher dass ClickHouse und Redis laufen
docker ps

# Falls nicht gestartet:
docker-compose up -d
```

### 3. Bitget-Tabellen überprüfen

```bash
# Tabellen in ClickHouse überprüfen
docker exec clickhouse-bolt clickhouse-client --query "SHOW TABLES FROM bitget"
```

## Tests ausführen

### Alle Bitget-Tests ausführen

```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
python -m pytest test/05_bitget_system/ -v
```

### Einzelne Testdateien ausführen

```bash
# API-Verbindungstests
python -m pytest test/05_bitget_system/test_bitget_api_connections.py -v

# Mit detaillierter Ausgabe
python -m pytest test/05_bitget_system/test_bitget_api_connections.py -v -s
```

### Spezifische Tests ausführen

```bash
# Nur REST API Tests
python -m pytest test/05_bitget_system/test_bitget_api_connections.py::TestBitgetAPIConnections::test_bitget_rest_api_connection -v

# Nur WebSocket Tests  
python -m pytest test/05_bitget_system/test_bitget_api_connections.py::TestBitgetAPIConnections::test_bitget_websocket_connection -v
```

## Testbeschreibungen

### test_bitget_api_connections.py

**Live-API-Verbindungstests mit echten Bitget-Daten:**

- `test_bitget_rest_api_connection`: Grundlegende REST-API-Verbindung
- `test_bitget_spot_symbols`: Spot-Symbole abrufen (BTCUSDT, ETHUSDT, etc.)
- `test_bitget_futures_symbols`: Futures-Symbole abrufen
- `test_bitget_spot_ticker`: Live-Ticker-Daten für Spot-Märkte
- `test_bitget_futures_ticker`: Live-Ticker-Daten für Futures-Märkte
- `test_bitget_spot_orderbook`: Orderbook-Daten abrufen
- `test_bitget_spot_candles`: Kerzendaten abrufen
- `test_bitget_websocket_connection`: WebSocket-Verbindung testen
- `test_bitget_api_rate_limiting`: Rate-Limiting-Verhalten prüfen
- `test_bitget_error_handling`: Fehlerbehandlung testen
- `test_bitget_all_market_types`: Alle konfigurierten Markttypen testen

## Erwartete Ausgabe

Bei erfolgreichen Tests:

```
✅ Bitget REST API connection successful - Server time: 1642771200000
✅ Bitget spot symbols fetch successful - 450 symbols
✅ Bitget futures symbols fetch successful - 120 symbols
✅ Bitget spot ticker fetch successful - BTCUSDT: $43250.00
✅ Bitget WebSocket connection successful - Response: {'event': 'subscribe'}
✅ All 4 market types tested successfully
```

## Fehlerbehandlung

### Häufige Probleme

1. **API-Key-Fehler**: 
   ```
   Error: Invalid API Key
   ```
   Lösung: Korrekte API-Credentials in Umgebungsvariablen setzen

2. **Rate-Limiting**:
   ```
   Error: Too Many Requests  
   ```
   Lösung: Tests mit längeren Pausen zwischen Requests ausführen

3. **Netzwerk-Timeouts**:
   ```
   Error: Connection timeout
   ```
   Lösung: Internet-Verbindung prüfen, ggf. Timeout erhöhen

4. **Docker-Container nicht verfügbar**:
   ```
   Error: Connection refused
   ```
   Lösung: `docker-compose up -d` ausführen

## Monitoring

### Test-Coverage

```bash
# Mit Coverage-Report
python -m pytest test/05_bitget_system/ --cov=market.bitget --cov-report=html
```

### Performance-Monitoring

Die Tests messen automatisch:
- API-Response-Zeiten
- WebSocket-Verbindungszeiten  
- Rate-Limiting-Verhalten

## Wichtige Hinweise

⚠️ **Live-Daten**: Alle Tests verwenden echte Bitget-API-Calls
⚠️ **API-Limits**: Tests berücksichtigen Rate-Limits  
⚠️ **Netzwerk**: Erfordert stabile Internet-Verbindung
⚠️ **Credentials**: API-Keys werden aus Umgebungsvariablen gelesen

## Nächste Schritte

Nach erfolgreichem API-Test:
1. Integrationstests implementieren (test_bitget_integration.py)
2. Datenbanktests hinzufügen (test_bitget_database.py) 
3. Router und Frontend-Integration testen

## Support

Bei Problemen:
1. Logs in `logs/` Verzeichnis prüfen
2. Docker-Container-Status überprüfen: `docker ps`
3. Netzwerk-Konnektivität zu Bitget API testen
