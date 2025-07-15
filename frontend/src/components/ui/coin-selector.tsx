import { useEffect, useState } from "react";

interface CoinData {
  id: string;
  symbol: string;
  market: string;
  price?: string;
  change?: string;
  changePercent?: number;
  isFavorite?: boolean;
  liveStatus?: "green" | "red";
  histStatus?: "green" | "red";
}

type SortField = "favorite" | "coin" | "price" | "change" | "live" | "hist";
type SortDirection = "asc" | "desc" | "random";

// Mapping von Trading Mode zu Market Filter
const TRADING_MODE_TO_MARKET: { [key: string]: string } = {
  "Spot": "spot",
  "USDT-M Futures": "usdt-m",
  "Coin-M Perpetual-Futures": "coin-m-perp",
  "Coin-M Delivery-Futures": "coin-m-delivery",
  "USDC-M Futures": "usdc-m",
};

// Gruppiert Coins nach Markt
function groupByMarket(coins: CoinData[]) {
  const grouped: { [market: string]: CoinData[] } = {};
  coins.forEach((coin) => {
    if (!grouped[coin.market]) grouped[coin.market] = [];
    grouped[coin.market].push(coin);
  });
  return grouped;
}

const CoinSelector = ({
  selectedCoin,
  onCoinSelect,
  selectedTradingMode = "Spot", // Neuer Parameter für Trading Mode
  showLiveStatus = true,
  showHistStatus = true,
}: {
  selectedCoin: string;
  onCoinSelect: (coin: CoinData) => void;
  selectedTradingMode?: string; // Trading Mode von der Navigation
  showLiveStatus?: boolean;
  showHistStatus?: boolean;
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [sortField, setSortField] = useState<SortField>("coin");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [coins, setCoins] = useState<CoinData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // API-Call mit Error Handling
  useEffect(() => {
    const fetchSymbols = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch("/api/symbols");
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data && Array.isArray(data.symbols)) {
          // Map API data to CoinData format
          const mappedCoins = data.symbols.map((apiCoin: any, idx: number) => ({
            id: idx.toString(),
            symbol: apiCoin.symbol || "UNKNOWN",
            market: apiCoin.market || "unknown",
            price: apiCoin.price || "-",
            change: apiCoin.change || "-",
            changePercent: apiCoin.changePercent || 0,
            isFavorite: false,
            liveStatus: "green" as const,
            histStatus: "green" as const,
          }));
          
          setCoins(mappedCoins);
        } else {
          throw new Error("Invalid API response format");
        }
      } catch (err) {
        console.error("Failed to fetch symbols:", err);
        setError(err instanceof Error ? err.message : "Failed to load symbols");
        
        // Fallback zu Dummy-Daten wenn API nicht verfügbar
        setCoins([
          {
            id: "1",
            symbol: "BTC/USDT",
            market: "spot",
            price: "104,911.62",
            change: "-3.56%",
            changePercent: -3.56,
            isFavorite: true,
            liveStatus: "green",
            histStatus: "green",
          },
          {
            id: "2",
            symbol: "ETH/USDT",
            market: "spot",
            price: "3,252.10",
            change: "+1.20%",
            changePercent: 1.2,
            isFavorite: false,
            liveStatus: "green",
            histStatus: "red",
          },
          {
            id: "3",
            symbol: "SOL/USDT",
            market: "spot",
            price: "134.51",
            change: "+0.30%",
            changePercent: 0.3,
            isFavorite: true,
            liveStatus: "green",
            histStatus: "green",
          },
          {
            id: "4",
            symbol: "BTC/USDT",
            market: "usdt-m",
            price: "104,420.00",
            change: "-0.18%",
            changePercent: -0.18,
            isFavorite: false,
            liveStatus: "red",
            histStatus: "red",
          },
          {
            id: "5",
            symbol: "ETH/USDT",
            market: "usdt-m",
            price: "3,240.50",
            change: "+0.85%",
            changePercent: 0.85,
            isFavorite: false,
            liveStatus: "green",
            histStatus: "green",
          },
          {
            id: "6",
            symbol: "BTC/USD",
            market: "coin-m-perp",
            price: "104,350.00",
            change: "-0.25%",
            changePercent: -0.25,
            isFavorite: false,
            liveStatus: "green",
            histStatus: "red",
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchSymbols();
  }, []);

  // Filtere Coins basierend auf dem ausgewählten Trading Mode
  const getFilteredCoins = () => {
    const targetMarket = TRADING_MODE_TO_MARKET[selectedTradingMode];
    
    if (!targetMarket) {
      // Fallback: Zeige alle Coins wenn Trading Mode unbekannt
      return coins;
    }
    
    return coins.filter(coin => coin.market === targetMarket);
  };

  const filteredCoins = getFilteredCoins();
  const groupedCoins = groupByMarket(filteredCoins);

  const sortCoins = (coins: CoinData[], field: SortField) => {
    // Optional: Sortfunktion implementieren falls gewünscht
    return coins;
  };

  const handleCoinSelect = (coin: CoinData) => {
    onCoinSelect(coin);
    setIsOpen(false);
  };

  const toggleFavorite = (coinId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setCoins(
      coins.map((coin) =>
        coin.id === coinId ? { ...coin, isFavorite: !coin.isFavorite } : coin
      )
    );
  };

  return (
    <div className="relative">
      {/* Dropdown Button */}
      <button
        className="text-[#222] dark:text-white rounded px-0 py-1.5 font-medium bg-transparent hover:bg-gray-100 dark:hover:bg-gray-700 my-auto w-full"
        onClick={() => setIsOpen(!isOpen)}
      >
        {selectedCoin}&nbsp;&nbsp;&nbsp;&nbsp;
        <span>▽</span>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 z-50 max-w-[480px]">
          <div className="min-w-[368px] rounded-xl shadow-2xl bg-white dark:bg-gray-800 overflow-hidden backdrop-blur-sm border border-gray-200 dark:border-gray-700">
            
            {/* Loading State */}
            {loading && (
              <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                Loading symbols...
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="px-4 py-4 text-center">
                <div className="text-red-600 dark:text-red-400 text-sm mb-2">
                  API Error: {error}
                </div>
                <div className="text-gray-500 dark:text-gray-400 text-xs">
                  Using fallback data
                </div>
              </div>
            )}

            {/* Market Filter Info */}
            {!loading && filteredCoins.length > 0 && (
              <div className="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                Showing {selectedTradingMode} markets ({filteredCoins.length} symbols)
              </div>
            )}

            {/* Header Row */}
            <div className="flex items-center px-4 py-2 bg-gray-800 dark:bg-gray-800 border-b border-gray-700">
              <div className="w-[40px] text-center">
                <span className="text-yellow-500">★</span>
              </div>
              <div className="w-[120px] font-bold text-xs text-gray-300 uppercase">
                COIN <span className="ml-1">↑</span>
              </div>
              <div className="w-[120px] text-right font-bold text-xs text-gray-300 uppercase">
                PRICE
              </div>
              <div className="w-[100px] text-right font-bold text-xs text-gray-300 uppercase">
                24H
              </div>
              <div className="w-[40px] text-center font-bold text-xs text-gray-300 uppercase">
                L
              </div>
              <div className="w-[40px] text-center font-bold text-xs text-gray-300 uppercase">
                H
              </div>
            </div>

            {/* Coins list */}
            {!loading && filteredCoins.map((coin) => (
              <div
                key={coin.id}
                className={`flex items-center px-4 h-[50px] font-sans cursor-pointer transition-all duration-200 border-b border-gray-700 ${
                  coin.symbol === selectedCoin
                    ? "bg-gray-700"
                    : "hover:bg-gray-700"
                }`}
                onClick={() => handleCoinSelect(coin)}
              >
                <div className="w-[40px] text-center">
                  <span
                    className={`text-lg cursor-pointer hover:scale-125 transition-transform duration-200 ${
                      coin.isFavorite
                        ? "text-yellow-500"
                        : "text-gray-500"
                    }`}
                    onClick={(e) => toggleFavorite(coin.id, e)}
                  >
                    ★
                  </span>
                </div>
                <div className="w-[120px] font-bold text-sm text-white">
                  {coin.symbol}
                </div>
                <div className="w-[120px] text-right font-semibold text-sm text-white">
                  {coin.price}
                </div>
                <div
                  className={`w-[100px] text-right font-bold text-sm ${
                    (coin.changePercent ?? 0) >= 0
                      ? "text-green-500"
                      : "text-red-500"
                  }`}
                >
                  {coin.change}
                </div>
                <div className="w-[40px] text-center">
                  <span
                    className="inline-block rounded-full"
                    style={{
                      width: "12px",
                      height: "12px",
                      backgroundColor:
                        coin.liveStatus === "green"
                          ? "rgba(16, 185, 129, 0.9)"
                          : "rgba(239, 68, 68, 0.9)",
                    }}
                  ></span>
                </div>
                <div className="w-[40px] text-center">
                  <span
                    className="inline-block rounded-full"
                    style={{
                      width: "12px",
                      height: "12px",
                      backgroundColor:
                        coin.histStatus === "green"
                          ? "rgba(16, 185, 129, 0.9)"
                          : "rgba(239, 68, 68, 0.9)",
                    }}
                  ></span>
                </div>
              </div>
            ))}

            {/* Empty State - wenn keine Coins für den gewählten Markt */}
            {!loading && !error && filteredCoins.length === 0 && (
              <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                <div className="text-sm mb-2">No symbols available for {selectedTradingMode}</div>
                <div className="text-xs">Try selecting a different market</div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Overlay to close dropdown when clicking outside */}
      {isOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      )}
    </div>
  );
};

export default CoinSelector;