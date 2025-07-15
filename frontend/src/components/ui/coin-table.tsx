import { useState } from "react";

interface CoinData {
  id: string;
  symbol: string;
  price: string;
  change: string;
  changePercent: number;
  isFavorite: boolean;
  liveStatus: "green" | "red";
  histStatus: "green" | "red";
}

const CoinTable = () => {
  const [coins] = useState<CoinData[]>([
    {
      id: "1",
      symbol: "BTC/USDT",
      price: "104,911.62",
      change: "−3.56%",
      changePercent: -3.56,
      isFavorite: true,
      liveStatus: "green",
      histStatus: "green",
    },
    {
      id: "2",
      symbol: "ETH/USDT",
      price: "3,500.00",
      change: "+1.23%",
      changePercent: 1.23,
      isFavorite: false,
      liveStatus: "green",
      histStatus: "red",
    },
    {
      id: "3",
      symbol: "SOL/USDT",
      price: "134.51",
      change: "+0.30%",
      changePercent: 0.3,
      isFavorite: true,
      liveStatus: "green",
      histStatus: "green",
    },
    {
      id: "4",
      symbol: "BTC/USD",
      price: "104,420.00",
      change: "−0.18%",
      changePercent: -0.18,
      isFavorite: false,
      liveStatus: "red",
      histStatus: "red",
    },
  ]);

  const [selectedCoin, setSelectedCoin] = useState("1");

  return (
    <div className="mt-1">
      <table className="min-w-[270px] text-xs rounded-lg shadow border overflow-hidden">
        <thead>
          <tr className="bg-gray-50">
            <th className="px-2 py-1 text-yellow-500 w-7 text-center">★</th>
            <th className="px-2 py-1">Coin</th>
            <th className="px-2 py-1">Preis</th>
            <th className="px-2 py-1">Δ</th>
            <th className="px-2 py-1">Live</th>
            <th className="px-2 py-1">Hist</th>
          </tr>
        </thead>
        <tbody>
          {coins.map((coin) => (
            <tr
              key={coin.id}
              className={`cursor-pointer transition-colors ${
                selectedCoin === coin.id ? "bg-blue-50" : "hover:bg-blue-50"
              }`}
              onClick={() => setSelectedCoin(coin.id)}
            >
              <td className="px-2 py-1 text-xs">
                <span
                  className={
                    coin.isFavorite ? "text-yellow-400" : "text-gray-300"
                  }
                >
                  ★
                </span>
              </td>
              <td className="px-2 py-1 font-bold">{coin.symbol}</td>
              <td className="px-2 py-1">{coin.price}</td>
              <td
                className={`px-2 py-1 font-bold ${
                  coin.changePercent >= 0 ? "text-green-500" : "text-red-500"
                }`}
              >
                {coin.change}
              </td>
              <td className="px-2 py-1 text-xs">
                <span
                  className={`inline-block w-3 h-3 rounded-full ${
                    coin.liveStatus === "green" ? "bg-green-500" : "bg-red-500"
                  }`}
                >
                  ●
                </span>
              </td>
              <td className="px-2 py-1 text-xs">
                <span
                  className={`inline-block w-3 h-3 rounded-full ${
                    coin.histStatus === "green" ? "bg-green-500" : "bg-red-500"
                  }`}
                >
                  ●
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CoinTable;
