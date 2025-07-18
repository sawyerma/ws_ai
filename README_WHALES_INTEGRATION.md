# Whale Monitoring System - Frontend Integration Guide

## 🐋 Systemübersicht

Das Whale Monitoring System überwacht große Kryptowährungstransaktionen (Whales) auf mehreren Blockchains und stellt diese Daten über APIs und WebSockets für das Frontend zur Verfügung.

### Unterstützte Blockchains
- **Ethereum** (ETH, USDT, USDC)
- **Binance Smart Chain** (BNB, BUSD)
- **Polygon** (MATIC, USDC)

### Überwachte Coins
- **Tier 1**: BTC, ETH, USDT (Höchste Priorität)
- **Tier 2**: SOL, BNB, XRP (Mittlere Priorität)
- **Tier 3**: ADA, AVAX, SUI, SEI (Niedrige Priorität)
- **Tier 4**: USDC, BUSD (Stablecoins)

---

## 🏗️ Systemarchitektur

### Backend-Komponenten

```
backend/
├── whales/                          # Whale Monitoring Hauptmodul
│   ├── __init__.py
│   ├── main.py                      # Hauptanwendung
│   ├── config.py                    # Konfiguration
│   ├── collector_manager.py         # Collector-Management
│   ├── collectors/                  # Datensammler
│   │   ├── blockchain_collector.py  # Blockchain-Datensammler
│   │   └── token_collector.py       # Token-Datensammler
│   └── services/                    # Services
│       └── price_service.py         # Preisservice
├── db/
│   ├── clickhouse_whales.py         # ClickHouse-Verbindung
│   └── migrations/
│       └── 20250701_create_whale_tables.sql
└── core/
    └── routers/                     # API-Endpunkte (zu implementieren)
```

---

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```ini
# === Database Settings ===
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=bitget
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# === Whale System APIs ===
ETHEREUM_API_KEY="YOUR_ETHERSCAN_API_KEY"
BSC_API_KEY="YOUR_BSCSCAN_API_KEY"
POLYGON_API_KEY="YOUR_POLYGONSCAN_API_KEY"

# === Price Service ===
PRICE_UPDATE_INTERVAL=300
```

### Port-Konfiguration

| Service | Port | Beschreibung |
|---------|------|-------------|
| ClickHouse HTTP | 8123 | Datenbank-Zugriff |
| ClickHouse TCP | 9000 | Natives Protokoll |
| Whale API | 8000 | REST API (zu implementieren) |
| Whale WebSocket | 8001 | Real-time Updates (zu implementieren) |

---

## 🗄️ Datenbank-Schema

### Tabelle: whale_events

```sql
CREATE TABLE whale_events (
    event_id UUID,
    ts DateTime,
    chain String,                    -- ethereum, binance, polygon
    tx_hash String,
    from_addr String,
    to_addr String,
    token String,                    -- Contract-Adresse (NULL für native)
    symbol String,                   -- BTC, ETH, USDT, etc.
    amount Float64,                  -- Anzahl Tokens
    is_native UInt8,                 -- 1 für native Coins, 0 für Tokens
    exchange String,                 -- Binance, Coinbase, etc.
    amount_usd Float64,              -- USD-Wert
    from_exchange String,            -- Quell-Exchange
    from_country String,             -- Quell-Land
    from_city String,                -- Quell-Stadt
    to_exchange String,              -- Ziel-Exchange
    to_country String,               -- Ziel-Land
    to_city String,                  -- Ziel-Stadt
    is_cross_border UInt8,           -- 1 für grenzüberschreitend
    source String,                   -- Datenquelle
    threshold_usd Float64,           -- Verwendeter Schwellwert
    coin_rank UInt16,                -- Coin-Priorität (1-4)
    created_at DateTime
);
```

### Tabelle: coin_config

```sql
CREATE TABLE coin_config (
    symbol String,                   -- BTC, ETH, etc.
    chain String,                    -- ethereum, binance, polygon
    contract_addr String,            -- Token-Contract (NULL für native)
    coingecko_id String,             -- CoinGecko-ID für Preise
    decimals UInt8,                  -- Token-Dezimalstellen
    threshold_usd Float64,           -- Whale-Schwellwert in USD
    priority UInt8,                  -- 1=High, 2=Medium, 3=Low, 4=Stablecoin
    active UInt8,                    -- 1=aktiv, 0=deaktiviert
    last_updated DateTime
);
```

---

## 🔌 API-Endpunkte (zu implementieren)

### REST API Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|-------------|
| `/api/whales/recent` | GET | Neueste Whale-Transaktionen |
| `/api/whales/live` | GET | Live-Transaktionen (letzte 5 Min) |
| `/api/whales/top` | GET | Top-Whales nach Volumen |
| `/api/whales/stats` | GET | Statistiken und Metriken |
| `/api/whales/chains` | GET | Verfügbare Blockchains |
| `/api/whales/coins` | GET | Unterstützte Coins |
| `/api/whales/config` | GET | Systemkonfiguration |

### Query Parameter

```typescript
interface WhaleQueryParams {
  // Zeitraum
  from?: string;           // ISO DateTime
  to?: string;             // ISO DateTime
  last_hours?: number;     // Letzte X Stunden
  
  // Filter
  chain?: string[];        // ['ethereum', 'binance']
  symbol?: string[];       // ['BTC', 'ETH']
  min_usd?: number;        // Minimum USD-Wert
  max_usd?: number;        // Maximum USD-Wert
  
  // Geografisch
  country?: string[];      // ['USA', 'Germany']
  exchange?: string[];     // ['Binance', 'Coinbase']
  cross_border?: boolean;  // Nur grenzüberschreitend
  
  // Sortierung & Pagination
  sort?: string;           // 'amount_usd' | 'timestamp'
  order?: 'asc' | 'desc';
  limit?: number;          // Default: 100
  offset?: number;         // Default: 0
}
```

---

## 📊 Frontend-Datenstrukturen

### Whale Event (TypeScript)

```typescript
interface WhaleEvent {
  event_id: string;
  timestamp: string;         // ISO DateTime
  chain: 'ethereum' | 'binance' | 'polygon';
  tx_hash: string;
  from_address: string;
  to_address: string;
  token?: string;            // Contract-Adresse
  symbol: string;            // BTC, ETH, etc.
  amount: number;            // Token-Anzahl
  is_native: boolean;
  exchange?: string;
  amount_usd: number;
  from_exchange?: string;
  from_country: string;
  from_city: string;
  to_exchange?: string;
  to_country: string;
  to_city: string;
  is_cross_border: boolean;
  source: string;
  threshold_usd: number;
  coin_rank: 1 | 2 | 3 | 4;
  created_at: string;
}
```

### Whale Statistics

```typescript
interface WhaleStats {
  total_volume_24h: number;
  total_transactions_24h: number;
  top_chains: {
    chain: string;
    volume_usd: number;
    transaction_count: number;
  }[];
  top_coins: {
    symbol: string;
    volume_usd: number;
    transaction_count: number;
  }[];
  geographic_distribution: {
    country: string;
    volume_usd: number;
    transaction_count: number;
  }[];
  exchange_flows: {
    exchange: string;
    inflow_usd: number;
    outflow_usd: number;
    net_flow_usd: number;
  }[];
}
```

---

## 🔄 Real-time Updates (WebSocket)

### WebSocket-Verbindung

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/whales');

ws.onopen = () => {
  console.log('Whale WebSocket verbunden');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleWhaleUpdate(data);
};
```

### WebSocket-Nachrichten

```typescript
interface WhaleWebSocketMessage {
  type: 'whale_transaction' | 'stats_update' | 'system_status';
  data: WhaleEvent | WhaleStats | SystemStatus;
  timestamp: string;
}
```

---

## 🎨 Frontend-Komponenten

### Empfohlene UI-Komponenten

1. **WhaleTransactionList**
   - Zeigt neueste Whale-Transaktionen
   - Filter nach Chain, Coin, Zeitraum
   - Real-time Updates

2. **WhaleDashboard**
   - Statistiken und Metriken
   - Top-Coins und Chains
   - Volumen-Charts

3. **WhaleMap**
   - Geografische Visualisierung
   - Cross-Border-Flows
   - Exchange-Standorte

4. **WhaleAlert**
   - Benachrichtigungen für große Transaktionen
   - Konfigurierbare Schwellwerte
   - Sound/Visual Alerts

### Beispiel-React-Komponente

```tsx
import React, { useState, useEffect } from 'react';

interface WhaleTransactionListProps {
  chain?: string;
  symbol?: string;
  minUsd?: number;
}

const WhaleTransactionList: React.FC<WhaleTransactionListProps> = ({
  chain,
  symbol,
  minUsd = 1000000
}) => {
  const [whales, setWhales] = useState<WhaleEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWhales = async () => {
      const params = new URLSearchParams({
        ...(chain && { chain }),
        ...(symbol && { symbol }),
        min_usd: minUsd.toString(),
        limit: '50'
      });

      const response = await fetch(`/api/whales/recent?${params}`);
      const data = await response.json();
      setWhales(data);
      setLoading(false);
    };

    fetchWhales();
  }, [chain, symbol, minUsd]);

  if (loading) return <div>Loading whales...</div>;

  return (
    <div className="whale-transaction-list">
      {whales.map(whale => (
        <div key={whale.event_id} className="whale-transaction">
          <div className="whale-header">
            <span className="chain-badge">{whale.chain}</span>
            <span className="symbol">{whale.symbol}</span>
            <span className="amount">{whale.amount_usd.toLocaleString()} USD</span>
          </div>
          <div className="whale-details">
            <span>From: {whale.from_country} ({whale.from_exchange})</span>
            <span>To: {whale.to_country} ({whale.to_exchange})</span>
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## 🚀 Installation & Setup

### 1. Backend-Setup

```bash
# Whale System starten
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

pip install -r requirements.txt
python whales/main.py
```

### 2. ClickHouse-Setup

```bash
# Docker
docker run -d \
  --name clickhouse \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server

# Tabellen erstellen
clickhouse-client --query "$(cat db/migrations/20250701_create_whale_tables.sql)"
```

### 3. API-Keys konfigurieren

```bash
# .env Datei bearbeiten
ETHEREUM_API_KEY="your_etherscan_api_key"
BSC_API_KEY="your_bscscan_api_key"
POLYGON_API_KEY="your_polygonscan_api_key"
```

---

## 📈 Monitoring & Metriken

### System-Metriken

```typescript
interface SystemMetrics {
  collectors: {
    ethereum: {
      status: 'running' | 'stopped' | 'error';
      last_block: number;
      transactions_processed: number;
      whales_detected: number;
    };
    binance: { /* ... */ };
    polygon: { /* ... */ };
  };
  database: {
    connection_status: 'healthy' | 'degraded' | 'down';
    total_whale_events: number;
    events_last_24h: number;
  };
  price_service: {
    last_update: string;
    coins_tracked: number;
    update_interval: number;
  };
}
```

---

## 🔍 Debugging & Logs

### Log-Levels

```python
# Logging-Konfiguration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Wichtige Log-Nachrichten

```
🐋 ETH Whale: 1,234.56 ($2,500,000)
🌍 Cross-border: USA → Germany ($5,000,000)
🪙 USDT Whale: 10,000,000 ($10,000,000)
✅ Ethereum Collector started
❌ Price update failed: API rate limit
```

---

## 🧪 Testing

### Test-Ausführung

```bash
# Alle Whale-Tests
cd test/04_whale_system
source ../../test_venv/bin/activate
pytest -v

# Einzelne Test-Kategorien
pytest test_infrastructure_whales.py -v
pytest test_api_connections_whales.py -v
pytest test_database_whales.py -v
```

---

## 🔒 Sicherheit

### API-Sicherheit

- API-Keys in Umgebungsvariablen
- Rate-Limiting für externe APIs
- Input-Validierung für alle Endpunkte
- CORS-Konfiguration für Frontend

### Datenbank-Sicherheit

- Nur lesende Zugriffe für Frontend
- Separater User für Frontend-Zugriff
- Monitoring von Datenbankzugriffen

---

## 📞 Support & Wartung

### Kontakte

- **Backend-Team**: Whale System Development
- **Frontend-Team**: GUI Integration
- **DevOps**: Infrastructure & Deployment

### Wartungsarbeiten

- Tägliche Datenbank-Wartung (00:00 UTC)
- Wöchentliche API-Key-Rotation
- Monatliche Performance-Optimierung

---

## 🎯 Roadmap

### Phase 1 (Aktuell)
- ✅ Grundsystem implementiert
- ✅ Datenbank-Schema erstellt
- ✅ Collector implementiert

### Phase 2 (Nächste Schritte)
- [ ] REST API implementieren
- [ ] WebSocket-Server implementieren
- [ ] Frontend-Integration

### Phase 3 (Zukunft)
- [ ] Machine Learning für Whale-Erkennung
- [ ] Erweiterte Geografische Analyse
- [ ] Mobile App Integration

---

## 📚 Weitere Ressourcen

- [ClickHouse Dokumentation](https://clickhouse.com/docs)
- [Etherscan API](https://docs.etherscan.io/)
- [BSCScan API](https://docs.bscscan.com/)
- [PolygonScan API](https://docs.polygonscan.com/)
- [CoinGecko API](https://www.coingecko.com/en/api)

---

**Letzte Aktualisierung**: 18. Januar 2025  
**Version**: 1.0.0  
**Status**: ✅ Produktionsbereit
