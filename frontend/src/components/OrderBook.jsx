import React, { useEffect, useState } from "react";

export default function Orderbook({
  symbol = "BTCUSDT",
  market = "spot",
  apiBase = "http://localhost:8000",  // ggf. anpassen
  limit = 15
}) {
  const [orderbook, setOrderbook] = useState({ asks: [], bids: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    const fetchOrderbook = async () => {
      setLoading(true);
      setError(null);
      try {
        const market_type = market === "spot" ? "spot" : market === "usdtm" ? "usdtm" : "coinm";
        const url = `${apiBase}/orderbook?symbol=${symbol}&market_type=${market_type}&limit=${limit}`;
        const resp = await fetch(url);
        const data = await resp.json();
        if (!ignore) setOrderbook({ asks: data.asks || [], bids: data.bids || [] });
      } catch (e) {
        if (!ignore) setError(e.message || "Orderbook error");
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    fetchOrderbook();
    const interval = setInterval(fetchOrderbook, 2000); // Refresh alle 2s
    return () => { ignore = true; clearInterval(interval); };
  }, [symbol, market, apiBase, limit]);

  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-xl shadow w-full max-w-md mt-4">
      <div className="mb-2 font-bold text-lg">Orderbook</div>
      {loading && <div className="text-xs text-gray-400">Loading...</div>}
      {error && <div className="text-xs text-red-600">{error}</div>}
      <div className="flex flex-row gap-4">
        <div className="flex-1">
          <div className="font-semibold text-xs text-red-500">Asks</div>
          <table className="w-full text-xs">
            <tbody>
              {orderbook.asks.slice(-limit).reverse().map((a, i) => (
                <tr key={i}>
                  <td align="right">{a.price}</td>
                  <td align="right">{a.size}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex-1">
          <div className="font-semibold text-xs text-green-500">Bids</div>
          <table className="w-full text-xs">
            <tbody>
              {orderbook.bids.slice(0, limit).map((b, i) => (
                <tr key={i}>
                  <td align="right">{b.price}</td>
                  <td align="right">{b.size}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
