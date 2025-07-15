import asyncio
import httpx
import logging
from datetime import datetime, timezone
from typing import List

from db.clickhouse import insert_bar  # Import der zentralen DB-Funktion

logger = logging.getLogger("bitget-backfill")

class BitgetBackfill:
    """
    Stellt rückwirkenden Datenimport (Backfill) für Kerzen sicher,
    strikt nach Rate‐Limit und Paging für Bitget V2-API.
    """
    BASE_URL = "https://api.bitget.com"
    HISTORY_ENDPOINT = "/api/v2/spot/public/candles"
    MAX_REQS_PER_SEC = 15

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=self.BASE_URL)
        self._sem = asyncio.Semaphore(self.MAX_REQS_PER_SEC)
        self._delay = 1.0 / self.MAX_REQS_PER_SEC

    async def history(
        self,
        symbol: str,
        until: datetime,
        granularity: str = "1m",
        limit: int = 200
    ):
        """
        Lädt rückwirkend Kerzen von jetzt bis `until` und persistiert sie in ClickHouse.
        Paging anhand Timestamp, Abbruch, wenn keine Daten mehr.
        """
        now_ms   = int(datetime.now(timezone.utc).timestamp() * 1000)
        until_ms = int(until.timestamp() * 1000)
        end_ts   = now_ms

        while end_ts > until_ms:
            # V2-API: symbol muss in 'btc_usdt' Form, period statt granularity
            api_symbol = symbol.replace("USDT", "_usdt").lower()
            params = {
                "symbol":  api_symbol,
                "period":  granularity,
                "endTime": end_ts,
                "limit":   limit,
            }

            async with self._sem:
                resp = await self.client.get(self.HISTORY_ENDPOINT, params=params)

            if resp.status_code == 429:
                logger.warning(f"[BitgetBackfill] Rate-Limit für {symbol} erreicht, warte 1s...")
                await asyncio.sleep(1)
                continue

            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                logger.info(f"[BitgetBackfill] Keine Daten mehr für {symbol}. Beende.")
                break

            # Persistiere jede Kerze
            for ts_ms, o, h, l, c, v in data:
                dt_obj = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                insert_bar(symbol, "spot", float(o), float(h), float(l), float(c), float(v), dt_obj)

            # Setze neues Ende auf den kleinsten Timestamp minus 1 ms
            end_ts = min(item[0] for item in data) - 1
            logger.info(f"[BitgetBackfill] {symbol}: bis {end_ts} weiter gefüllt")
            await asyncio.sleep(self._delay)

        logger.info(f"[BitgetBackfill] Fertig mit {symbol} bis {until.isoformat()}")

    async def close(self):
        await self.client.aclose()

async def backfill_symbols(
    symbols: List[str],
    until: datetime,
    granularity: str = "1m",
    limit: int = 200
):
    """
    Führt den Backfill für eine Liste von Symbolen aus.
    """
    manager = BitgetBackfill()
    for symbol in symbols:
        logger.info(f"[BitgetBackfill] Starte für {symbol} bis {until.isoformat()}")
        try:
            await manager.history(symbol, until, granularity, limit)
        except Exception as e:
            logger.error(f"[BitgetBackfill] Fehler beim Backfill von {symbol}: {e}")
    await manager.close()
