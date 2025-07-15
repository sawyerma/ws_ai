from notifications.telegram.telegram import send_telegram_message, post_anything

# 1. Whale-Alert
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

# 2. System-/Statusbericht
async def system_daily_report(stats: dict):
    msg = (
        "📝 *Tagesbericht*\n"
        f"*Trades:* {stats['trades']}\n"
        f"*Bars:* {stats['bars']}\n"
        f"*Aktive Coins:* {stats['coins_active']}\n"
        f"*Letztes Whale-Event:* {stats.get('last_whale_time', '–')}\n"
        f"*API-Status:* {'✅' if stats['api_ok'] else '❌'}\n"
        f"*Fehler heute:* {stats['errors']}\n"
        "\n"
        f"_{stats.get('ai_summary', 'Keine KI-Zusammenfassung heute.')}_"
    )
    await send_telegram_message(msg)

# 3. AI-Report (Text + optional Bild)
async def ai_insight_report(text: str, image_path: str = None):
    await post_anything(text=text, image=image_path)

# 4. Kombinierter Morgenreport (Text + Bild)
import datetime
async def morning_report():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    summary = "Heute dominiert BTC, AI erkennt erhöhtes Whale-Aufkommen. Keine kritischen Fehler im System."
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
        f"*Fehler heute:* {stats['errors']}\n"
        "\n"
        f"_{summary}_"
    )
    await post_anything(text=msg, image="/pfad/zum/chart_screenshot.png")
