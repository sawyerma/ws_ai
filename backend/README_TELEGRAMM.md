````markdown
# 📲 Telegram Notifications – API- & Variablen-Übergabe für Frontend

---

## **Konfigurationsvariablen**

- `TELEGRAM_BOT_TOKEN`  
  _String_ – Dein Bot-Token vom @BotFather  
- `TELEGRAM_CHAT_ID`  
  _String_ – Ziel-Chat oder Kanal (User-ID, Gruppen-ID oder Kanal-Name)

---

## **Low-Level-Versand (in `notifications/telegram/telegram.py`)**

### Funktionen

```python
async def send_telegram_message(text: str, chat_id: Optional[str] = None)
````

* Sendet **Markdown-Text**.

```python
async def send_telegram_photo(image_path: str, caption: Optional[str] = None, chat_id: Optional[str] = None)
```

* Sendet ein **Foto** (Path zur lokalen Datei).

```python
async def send_telegram_document(file_path: str, caption: Optional[str] = None, chat_id: Optional[str] = None)
```

* Sendet jede **Datei** (CSV, PDF, …).

```python
async def post_anything(text: Optional[str] = None, image: Optional[str] = None, file: Optional[str] = None)
```

* Kombiniert Text, Bild und/oder Datei.

---

## **Predefined Templates (in `notifications/templates.py`)**

### 1. **Whale-Alert**

```python
async def whale_alert(event: dict):
    msg = (
        "🐳 *Vorsicht Whale!*\n"
        f"*Symbol:* `{event['symbol']}`\n"
        f"*Betrag:* `{event['amount']}`\n"
        f"*Chain:* `{event['chain']}`\n"
        f"*Zeit:* `{event['ts']}`\n"
        f"*Von:* `{event['from_addr']}`\n"
        f"*Zu:* `{event['to_addr']}`\n"
        f"*TX:* [Etherscan](https://etherscan.io/tx/{event['tx_hash']})"
    )
    await send_telegram_message(msg)
```

---

### 2. **System-/Statusbericht**

```python
async def system_daily_report(stats: dict):
    msg = (
        "📝 *Tagesbericht*\n"
        f"*Trades:* {stats['trades']}\n"
        f"*Bars:* {stats['bars']}\n"
        f"*Aktive Coins:* {stats['coins_active']}\n"
        f"*Letztes Whale-Event:* {stats.get('last_whale_time','–')}\n"
        f"*API-Status:* {'✅' if stats['api_ok'] else '❌'}\n"
        f"*Fehler heute:* {stats['errors']}\n\n"
        f"_{stats.get('ai_summary','Keine KI-Zusammenfassung heute.')}_"
    )
    await send_telegram_message(msg)
```

---

### 3. **KI-Report / Text+Bild-Kombi**

```python
async def ai_insight_report(text: str, image_path: str = None):
    await post_anything(text=text, image=image_path)
```

---

### 4. **Morgen-Report (Scheduler)**

```python
import datetime

async def morning_report():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    summary = "BTC dominiert, AI erkennt erhöhtes Whale-Volumen. Kein Systemfehler."
    stats = {
        'trades': 5200,
        'bars': 480,
        'coins_active': 7,
        'last_whale_time': '2025-07-02 02:13',
        'api_ok': True,
        'errors': 0
    }
    msg = (
        f"🌅 *Morgen-Report* {now}\n"
        f"*Aktive Coins:* {stats['coins_active']}\n"
        f"*Trades:* {stats['trades']}\n"
        f"*Letztes Whale-Event:* {stats['last_whale_time']}\n"
        f"*Fehler heute:* {stats['errors']}\n\n"
        f"_{summary}_"
    )
    await post_anything(text=msg, image="/pfad/zum/chart_screenshot.png")
```

---

## **Payload-Strukturen für das Frontend**

### Whale-Event

```json
{
  "symbol": "BTCUSDT",
  "amount": 1050.0,
  "chain": "ethereum",
  "ts": "2025-07-02 13:15",
  "from_addr": "0xAbc123...",
  "to_addr": "0xDef456...",
  "tx_hash": "0xE12abc..."
}
```

### System-Stats

```json
{
  "trades": 5200,
  "bars": 480,
  "coins_active": 7,
  "last_whale_time": "2025-07-02 02:13",
  "api_ok": true,
  "errors": 0,
  "ai_summary": "BTC könnte heute steigen, viele Whale-Bewegungen."
}
```

### KI-Insight

```json
{
  "text": "⚡️ KI-Analyse: BTC heute stark im Aufwärtstrend!",
  "image_path": "/path/to/chart.png"
}
```

---

## **Integrationsempfehlung für Frontend**

* **Keine Änderungen** an der Notification-Logik nötig.
* Empfange und parse die JSON-Payloads oder Markdown-Messages.
* **Variablennamen** (oben dokumentiert) 1:1 verwenden.
* Neue Felder werden in dieser README ergänzt.

---

## **Stand**: 2025-07-01

*Backend: Sawyer
