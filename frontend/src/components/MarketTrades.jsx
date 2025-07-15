import React, { useEffect, useState, useRef } from "react";

export default function MarketTrades({
  symbol = "BTCUSDT",
  market = "spot",
  wsBase = "ws://localhost:8100",   // ggf. anpassen
  maxLength = 30
}) {
  const [trades, setTrades] = useState([]);
  const [wsStatus, setWsStatus] = useState("disconnected");
  const wsRef = useRef(null);

  useEffect(() => {
    const wsUrl = `${wsBase}/ws/${symbol}/${market}/trades`;
    setWsStatus("connecting");
    const ws = new window.WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setWsStatus("connected");
    ws.onclose = () => setWsStatus("disconnected");
    ws.onerror = () => setWsStatus("error");

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "trade") {
          setTrades((prev) => {
            const updated = [msg, ...prev];
            return updated.slice(0, maxLength);
          });
        }
      } catch {}
    };

    return () => {
      ws.close();
    };
  }, [symbol, market, wsBase, maxLength]);

  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-xl shadow w-full max-w-md">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-bold text-lg">Market Trades</span>
        <span className={`text-xs px-2 py-1 rounded ${wsStatus === "connected" ? "bg-green-200 text-green-800" : wsStatus === "error" ? "bg-red-200 text-red-800" : "bg-gray-200 text-gray-800"}`}>
          {wsStatus}
        </span>
      </div>
      <div className="overflow-y-auto max-h-80">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th align="left">Time</th>
              <th align="right">Price</th>
              <th align="right">Amount</th>
              <th align="center">Side</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t, idx) => (
              <tr key={idx}>
                <td>{new Date(t.time).toLocaleTimeString()}</td>
                <td align="right" className={t.side === "buy" ? "text-green-500" : "text-red-500"}>{t.price}</td>
                <td align="right">{t.amount}</td>
                <td align="center">{t.side}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {trades.length === 0 && <div className="text-gray-400 p-2 text-center">No trades yet.</div>}
      </div>
    </div>
  );
}
