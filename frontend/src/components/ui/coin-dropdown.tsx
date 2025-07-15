import { useState } from "react";

interface CoinDropdownData {
  id: string;
  symbol: string;
  price: string;
  change: string;
  changePercent: number;
  isFavorite: boolean;
  liveStatus: "green" | "red";
  histStatus: "green" | "red";
  isActive?: boolean;
}

const CoinDropdown = () => {
  const [coins] = useState<CoinDropdownData[]>([
    {
      id: "1",
      symbol: "BTC/USDT",
      price: "104,911.62",
      change: "-3.56 %",
      changePercent: -3.56,
      isFavorite: true,
      liveStatus: "green",
      histStatus: "green",
      isActive: true,
    },
    {
      id: "2",
      symbol: "ETH/USDT",
      price: "3,252.10",
      change: "+1.20 %",
      changePercent: 1.2,
      isFavorite: false,
      liveStatus: "green",
      histStatus: "red",
    },
    {
      id: "3",
      symbol: "SOL/USDT",
      price: "134.51",
      change: "+0.30 %",
      changePercent: 0.3,
      isFavorite: true,
      liveStatus: "green",
      histStatus: "green",
    },
    {
      id: "4",
      symbol: "BTC/USD",
      price: "104,420.00",
      change: "-0.18 %",
      changePercent: -0.18,
      isFavorite: false,
      liveStatus: "red",
      histStatus: "red",
    },
  ]);

  const [selectedCoin, setSelectedCoin] = useState("1");

  return (
    <div className="min-w-[630px] rounded-[18px] shadow-[0_4px_32px_0_rgba(40,60,120,0.13)] border-[1.5px] border-[#eee] bg-white overflow-hidden mx-auto my-8">
      {/* Header */}
      <div className="flex items-center px-[30px] bg-[#f7fafd] font-bold h-14 text-[#65717c] tracking-[0.03em] border-b border-[#f3f3f3]">
        <div className="w-[68px] text-center text-[0.78em]"></div>
        <div className="w-[190px] font-bold text-[0.83em]">Coin</div>
        <div className="w-[178px] text-right text-[0.83em]">Letzter Preis</div>
        <div className="w-[160px] text-right text-[0.83em]">Δ 24h</div>
        <div className="w-[70px] text-center text-[0.82em]">Live</div>
        <div className="w-[70px] text-center text-[0.82em]">Hist</div>
      </div>

      {/* Rows */}
      {coins.map((coin) => (
        <div
          key={coin.id}
          className={`flex items-center px-[30px] h-[62px] text-[1.1rem] cursor-pointer transition-colors border-b border-[#f3f3f3] ${
            coin.isActive
              ? "bg-[#eaffee]"
              : selectedCoin === coin.id
                ? "bg-[#f5fafe]"
                : "hover:bg-[#f5fafe]"
          }`}
          onClick={() => setSelectedCoin(coin.id)}
        >
          <div className="w-[68px] text-center">
            <span
              className={`text-[0.83em] ${
                coin.isFavorite ? "text-[#ffd600]" : "text-[#e7e7e7]"
              }`}
            >
              ★
            </span>
          </div>
          <div className="w-[190px] font-bold">{coin.symbol}</div>
          <div className="w-[178px] text-right font-medium font-mono">
            {coin.price}
          </div>
          <div
            className={`w-[160px] text-right font-bold ${
              coin.changePercent >= 0 ? "text-[#15b446]" : "text-[#d53939]"
            }`}
          >
            {coin.change}
          </div>
          <div className="w-[70px] text-center">
            <span
              className={`inline-block w-4 h-4 rounded-full border-2 ${
                coin.liveStatus === "green"
                  ? "bg-[#41cf58] border-[#40ba59]"
                  : "bg-[#ef4444] border-[#d73c3c]"
              }`}
            ></span>
          </div>
          <div className="w-[70px] text-center">
            <span
              className={`inline-block w-4 h-4 rounded-full border-2 ${
                coin.histStatus === "green"
                  ? "bg-[#41cf58] border-[#40ba59]"
                  : "bg-[#ef4444] border-[#d73c3c]"
              }`}
            ></span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default CoinDropdown;