# Whale Tracker - Backend Integration Guide

## 📋 **Übersicht**

Diese Dokumentation beschreibt alle Variablen und API-Endpunkte, die das Backend für den Whale Tracker bereitstellen muss.

## 🔗 **API Endpunkte**

### **1. Whale Transactions API**
```
GET /api/whale-transactions
```

**Query Parameter:**
- `timeframe` - Zeitfilter (1h, 6h, 24h, 7d)
- `symbol` - Coin-Filter (BTC, ETH, SOL, etc.)
- `exchange` - Exchange-Filter (Coinbase Pro, Binance, etc.)
- `side` - Trade-Filter (buy, sell, all)
- `limit` - Anzahl Ergebnisse (default: 100)

### **2. Whale Chart Data API**
```
GET /api/whale-chart-data
```



**Query Parameter:**
- `timeframe` - Zeitfilter (1h, 6h, 24h, 7d)
- `interval` - Chart-Intervall (1h, 4h, etc.)

## 📊 **Datenstrukturen**

### **WhaleTransaction Interface**
```typescript
interface WhaleTransaction {
  id: number;                    // Eindeutige Transaction ID
  coin: string;                  // z.B. "BTC-USD", "ETH-USDT"
  exchange: string;              // z.B. "Coinbase Pro", "Binance"
  quantity: string;              // z.B. "2.00000 BTC", "150.5 ETH"
  total: string;                 // z.B. "236,686.00 USD"
  side: "BUY" | "SELL";         // Kauf oder Verkauf
  date: string;                  // z.B. "2024-01-19"
  time: string;                  // z.B. "14:23:45"
  marketcap: string;             // z.B. "$2.1T", "$391B"
  maker: string;                 // Wallet-Adresse
  timestamp: number;             // Unix timestamp für Sortierung
}
```

### **Chart Data Interface**
```typescript
interface WhaleChartData {
  time: string;                  // z.B. "00:00", "04:00"
  buy: number;                   // Buy-Volumen in Millionen
  sell: number;                  // Sell-Volumen in Millionen (negativ)
}
```

## 🔧 **Backend Implementierung**

### **1. Whale Transactions Endpoint**
```javascript
// GET /api/whale-transactions
{
  "transactions": [
    {
      "id": 1,
      "coin": "BTC-USD",
      "exchange": "Coinbase Pro",
      "quantity": "2.00000 BTC",
      "total": "236,686.00 USD",
      "side": "SELL",
      "date": "2024-01-19",
      "time": "14:23:45",
      "marketcap": "$2.1T",
      "maker": "0x742d35Cc6634C0532925a3b8D404fddBD4f4d4d4",
      "timestamp": 1705666425000
    }
  ],
  "total": 1247,
  "page": 1,
  "limit": 100
}
```

### **2. Chart Data Endpoint**
```javascript
// GET /api/whale-chart-data
{
  "chartData": [
    {
      "time": "00:00",
      "buy": 50,      // 50M USD Buy-Volumen
      "sell": -30     // 30M USD Sell-Volumen (negativ)
    },
    {
      "time": "04:00",
      "buy": 80,
      "sell": -60
    }
  ]
}
```

## 🎯 **Wichtige Anforderungen**

### **Whale Transaction Kriterien:**
- **Mindest-Transaktionswert:** > $100,000 USD
- **Große Wallets:** Bekannte Whale-Adressen
- **Exchange-Integration:** Coinbase Pro, Binance, Bybit, Bitstamp, etc.

### **Chart Daten:**
- **Zeitintervalle:** 1h, 4h, 6h, 12h, 24h
- **Volumen-Berechnung:** Aggregierte Buy/Sell-Volumina pro Zeitfenster
- **Skalierung:** Werte in Millionen USD

### **Performance:**
- **Caching:** Chart-Daten für 5 Minuten cachen
- **Pagination:** Tabellen-Daten paginiert ausliefern
- **Real-time:** WebSocket für Live-Updates (optional)

## 🔍 **Filter-Optionen**

### **Zeitfilter:**
- `1h` - Letzte Stunde
- `6h` - Letzte 6 Stunden  
- `24h` - Letzte 24 Stunden
- `7d` - Letzte 7 Tage

### **Symbol-Filter:**
- `all` - Alle Coins
- `BTC` - Nur Bitcoin
- `ETH` - Nur Ethereum
- `SOL` - Nur Solana
- `favorites` - Nur favorisierte Coins

### **Exchange-Filter:**
- `all` - Alle Exchanges
- `coinbase` - Coinbase Pro
- `binance` - Binance
- `bybit` - Bybit
- `bitstamp` - Bitstamp

### **Trade-Filter:**
- `all` - Alle Trades
- `buy` - Nur Käufe
- `sell` - Nur Verkäufe

## 📱 **Frontend Integration**

### **API Calls im Frontend:**
```typescript
// Whale Transactions laden
const fetchWhaleTransactions = async (filters) => {
  const params = new URLSearchParams({
    timeframe: filters.timeFilter,
    symbol: filters.symbolFilter,
    exchange: filters.exchangeFilter,
    side: filters.tradeFilter,
    limit: '100'
  });
  
  const response = await fetch(`/api/whale-transactions?${params}`);
  return response.json();
};

// Chart Data laden
const fetchChartData = async (timeframe) => {
  const response = await fetch(`/api/whale-chart-data?timeframe=${timeframe}`);
  return response.json();
};
```

### **State Management:**
```typescript
const [whaleTransactions, setWhaleTransactions] = useState([]);
const [chartData, setChartData] = useState([]);
const [timeFilter, setTimeFilter] = useState("1h");
const [symbolFilter, setSymbolFilter] = useState("all");
const [exchangeFilter, setExchangeFilter] = useState("all");
const [tradeFilter, setTradeFilter] = useState("all");
```

## 🚀 **Deployment Hinweise**

1. **Environment Variables:**
   ```
   WHALE_API_BASE_URL=https://api.yourbackend.com
   WHALE_MIN_TRANSACTION_VALUE=100000
   WHALE_CACHE_TTL=300
   ```

2. **Rate Limiting:**
   - Max 60 Requests pro Minute pro IP
   - Caching für häufige Anfragen

3. **Error Handling:**
   - 404: Keine Daten gefunden
   - 429: Rate Limit erreicht
   - 500: Server Error

## 📈 **Metriken & Monitoring**

- **Response Time:** < 500ms für Tabellen-Daten
- **Chart Loading:** < 200ms für Chart-Updates
- **Data Freshness:** Max 5 Minuten alte Daten
- **Uptime:** 99.9% Verfügbarkeit

---

**Kontakt:** Bei Fragen zur Integration wenden Sie sich an das Frontend-Team.