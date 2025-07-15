# Trading API Integration Guide

This document describes the **Trading API**—backed by a Bitget data pipeline—and the core routers you’ll consume in the frontend. It covers:

1. **Base URLs & Environment**
2. **REST Endpoints** (paths, parameters, response shapes)
3. **WebSocket Endpoints** (URIs, message schemas)
4. **Data Models & Variables**
5. **Usage Examples**
6. **Core Router Mapping**



## 1. Base URLs & Environment

* **API base URL** (in development):

  ```bash
  http://localhost:8100
  ```
* **WebSocket base URL** (in development):

  ```bash
  ws://localhost:8100
  ```
* **Frontend environment variable**:

  ```bash
  VITE_API_URL=http://localhost:8100
  ```

  Inject this into your app (e.g. via `import.meta.env.VITE_API_URL`).

---

## 2. REST Endpoints

### 2.1 GET `/symbols`

* **Description**: Returns the list of all available trading symbols (e.g. `"BTCUSDT"`, `"ETHUSDT"`, …) as pulled from the Bitget REST API and local DB.
* **Parameters**: None
* **Response**:

  ```json
  [
    "BTCUSDT",
    "ETHUSDT",
    // …
  ]
  ```

### 2.2 GET `/ticker`

* **Description**: Fetches current price data for every symbol/market.
* **Parameters**: None
* **Response**:

  ```json
  [
    {
      "symbol": "BTCUSDT",
      "last": 60000.0,
      "bid": 59950.0,
      "ask": 60050.0,
      "volume": 123.45,
      // …other exchange-specific fields
    },
    // …
  ]
  ```

### 2.3 GET `/settings`

* **Description**: Retrieves all saved “coin settings” from the DB (e.g. whether to store live data, backfill history, chart granularity).
* **Parameters**: None
* **Response**:

  ```json
  [
    {
      "symbol": "BTCUSDT",
      "market": "spot",
      "store_live": 1,
      "load_history": 1,
      "history_until": null,
      "favorite": 0,
      "db_resolution": 60,
      "chart_resolution": "1m",
      "updated_at": "2025-06-28T22:02:03"
    },
    // …
  ]
  ```

### 2.4 PUT `/settings`

* **Description**: Updates settings for one or more symbols.
  Optionally triggers a backfill if `load_history` + `history_until` are set.
* **Body**: Array of the same objects returned by GET `/settings`.
* **Response**:

  ```json
  {}  // HTTP 200 on success
  ```

### 2.5 GET `/ohlc`

* **Description**: Fetches historical candlestick data from your ClickHouse DB.
* **Query Parameters**:

  * `symbol` (string, **required**)
  * `market` (string, default `"spot"`)
  * `resolution` (string, default `"1s"`; also supports `"1m"`, `"5m"`, etc.)
  * `limit` (integer, default `200`)
* **Response**:

  ```json
  [
    {
      "ts": "2025-06-28T12:00:00",
      "open": 60000.0,
      "high": 60100.0,
      "low": 59900.0,
      "close": 60050.0,
      "volume": 10.0
    },
    // …
  ]
  ```

### 2.6 GET `/orderbook`

* **Description**: Fetches a snapshot of the order book directly from Bitget’s REST API.
* **Query Parameters**:

  * `symbol` (string, **required**)
  * `market_type` (string, default `"spot"`)
  * `limit` (integer, default `10`)
* **Response**:

  ```json
  {
    "bids": [[59900.0, 1.234], [59850.0, 0.5], …],
    "asks": [[60050.0, 0.8], [60100.0, 2.0], …]
  }
  ```

### 2.7 GET `/healthz`

* **Description**: Health check for API, WebSockets & ClickHouse connectivity.
* **Response**:

  ```json
  { "status": "ok" }
  ```

### 2.8 GET `/debugtest`

* **Description**: Exercises logging & error handling.
* **Response**:

  ```json
  {}  // HTTP 200 on success
  ```

### 2.9 POST `/publish`

* **Description**: Ingests a new trade event (used by upstream producers).
* **Body**: Free-form JSON trade object.
* **Response**:

  ```json
  {}  // HTTP 200 on success
  ```

### 2.10 POST `/backfill`

* **Description**: Triggers a historical backfill for a given symbol.
* **Body**:

  ```json
  {
    "symbol": "BTCUSDT",
    "until": "2025-06-28T00:00:00",
    "granularity": "1s",
    "limit": 200
  }
  ```
* **Response**:

  ```json
  {}  // HTTP 200 on success
  ```

---

## 3. WebSocket Endpoints

| URI                                    | Description            | Message Schema                           |
| -------------------------------------- | ---------------------- | ---------------------------------------- |
| `/ws/{symbol}`                         | Live OHLC updates      | `{ ts, open, high, low, close, volume }` |
| `/ws/{symbol}/{market_type}/trades`    | Live trade events      | `{ ts, price, size, side }`              |
| `/ws/{symbol}/{market_type}/orderbook` | Live order-book deltas | `{ bids: [...], asks: [...] }`           |

* **Usage**:

  ```js
  const ws = new WebSocket(`${WSS_URL}/ws/${symbol}`);
  ws.onmessage = evt => { 
    const bar = JSON.parse(evt.data);
    // bar: { ts, open, high, … }
  };
  ```

---

## 4. Data Models & Variables

* **`symbol`**: uppercase ticker (e.g. `"BTCUSDT"`).
* **`market` / `market_type`**: `"spot"` or other exchange-defined markets.
* **`resolution`** / **`chart_resolution`**: string (e.g. `"1s"`, `"1m"`, `"5m"`, …).
* **`db_resolution`**: integer in seconds (e.g. `60` for 1-minute bars).
* **`limit`**: number of records to return.
* **Timestamps** (`ts`, `updated_at`, `history_until`) are ISO-8601 strings.

---

## 5. Usage Examples

```js
const API = import.meta.env.VITE_API_URL;

// 1. Fetch symbols for dropdown
async function loadSymbols() {
  const symbols = await fetch(`${API}/symbols`).then(r => r.json());
  return symbols;  // ["BTCUSDT", "ETHUSDT", …]
}

// 2. Load 1m OHLC
async function loadBars(symbol) {
  return fetch(`${API}/ohlc?symbol=${symbol}&resolution=1m&limit=200`)
    .then(r => r.json());
}

// 3. Connect for real-time updates
function subscribeLiveBars(symbol, onBar) {
  const ws = new WebSocket(`${API.replace(/^http/, 'ws')}/ws/${symbol}`);
  ws.onmessage = e => onBar(JSON.parse(e.data));
  return ws;
}
```

---

## 6. Core Router Mapping

| Router File                 | Mount Path   | Purpose                              |
| --------------------------- | ------------ | ------------------------------------ |
| `core/routers/symbols.py`   | `/symbols`   | Symbol list                          |
| `core/routers/ticker.py`    | `/ticker`    | Live ticker/prices                   |
| `core/routers/settings.py`  | `/settings`  | Get/put coin settings                |
| `core/routers/ohlc.py`      | `/ohlc`      | Historical bar data                  |
| `core/routers/orderbook.py` | `/orderbook` | Order-book snapshots                 |
| `core/routers/health.py`    | `/healthz`   | Health check                         |
| `core/routers/debugtest.py` | `/debugtest` | Log / exception testing              |
| `core/routers/ws/*.py`      | `/ws/...`    | WebSocket endpoints for live updates |

---

**Notes for Frontend Team:**

* CORS is enabled for **all** origins on the API—no extra headers needed.
* If you serve the built production frontend from the backend, remove or update the static‐files mount in `core/main.py`. Otherwise, host your compiled assets via Vite and only call the API.
* For any new data fields or router additions, just match the path + JSON schema above.

With this guide, you should have everything needed to integrate seamlessly with the backend! Let me know if any fields or endpoints need further clarification.
