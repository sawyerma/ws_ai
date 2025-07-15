# Whale-Detection Backend – API- & Variablen-Übergabe für Frontend

---

## **Datenquellen & Endpunkte**

### **REST-API**

- **`GET /api/coins`**
  - _Beschreibung:_ Liefert alle Coins/Token, die für Whale-Detection gemappt sind
  - **Response:**  
    ```json
    [
      {
        "symbol": "ETH",
        "chain": "ethereum",
        "contract_addr": "",
        "is_native": 1,
        "exchange": "bitget",
        "active": 1
      },
      ...
    ]
    ```
  - **Filter:**  
    - `symbol` (optional)
    - `chain` (optional)
    - `exchange` (optional, z. B. "bitget", "none")
    - `active` (optional, 1/0)

---

- **`GET /api/whale_events`**
  - _Beschreibung:_ Gibt Whale-Events (Großtransfers) zurück, filterbar
  - **Query-Parameter:**
    - `symbol` (optional)
    - `exchange` (optional)
    - `since` (optional, `YYYY-MM-DD HH:MM:SS`)
    - `until` (optional)
    - `limit` (optional, default: 200)
  - **Response:**  
    ```json
    [
      {
        "event_id": "4d067b2f-...-cbbb9",
        "ts": "2025-07-01 13:21:44",
        "chain": "ethereum",
        "tx_hash": "0x...",
        "from_addr": "0x...",
        "to_addr": "0x...",
        "token": "ETH",
        "symbol": "ETH",
        "amount": 186.0,
        "is_native": 1,
        "exchange": "bitget"
      },
      ...
    ]
    ```

---

### **WebSocket**

- **`/ws/whales`**
  - _Beschreibung:_ Sendet alle neuen Whale-Events live (sowie die letzten 10 beim Connect)
  - **Message/Objekt:**  
    ```json
    {
      "event_id": "4d067b2f-...-cbbb9",
      "ts": "2025-07-01 13:21:44",
      "chain": "ethereum",
      "tx_hash": "0x...",
      "from_addr": "0x...",
      "to_addr": "0x...",
      "token": "ETH",
      "symbol": "ETH",
      "amount": 186.0,
      "is_native": 1,
      "exchange": "bitget"
    }
    ```

---

## **Variablen/Felder für Frontend-Dev**

| Feld         | Typ      | Beschreibung                                  |
| ------------ | -------- | --------------------------------------------- |
| event_id     | UUID     | Eindeutige Event-ID                           |
| ts           | DateTime | Zeitstempel (UTC, Blockzeitpunkt)             |
| chain        | String   | Blockchain-Name (z. B. ethereum)              |
| tx_hash      | String   | Transaktionshash                              |
| from_addr    | String   | Absenderadresse                               |
| to_addr      | String   | Empfängeradresse                              |
| token        | String   | ETH oder Contract-Adresse (bei ERC-20)        |
| symbol       | String   | Token-Symbol (z. B. "ETH", "USDC")            |
| amount       | Float64  | Betrag (in Token-Einheiten, z. B. ETH)        |
| is_native    | UInt8    | 1 = native transfer, 0 = ERC-20 transfer      |
| exchange     | String   | "bitget", "binance", "none", ... (zugeordnet) |

---

## **Hinweise für Frontend-Team**

- **Es werden keine UI-Logik und keine Extra-Variablen übergeben:**  
  _Die komplette Business-Logik ist im Backend, alles ist als Variable direkt in den API-Responses/WS-Messages enthalten._
- **Neue Felder werden in dieser README dokumentiert.**
- **Die Daten sind immer direkt nutzbar (kein Mapping nötig).**
- **Filtersupport wie oben beschrieben.**
- **Für weitere Wünsche: Doku einfach ergänzen, Backend liefert alles sauber nach.**

---

## **Stand**: 2025-07-01  
*Backend: Sawyer/ChatGPT, Frontend: eigenes Team – diese Doku ist die alleinige Referenz für alle Variablen und Felder.*

