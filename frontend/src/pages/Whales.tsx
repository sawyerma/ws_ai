import { useState, useEffect } from "react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";
import { Search, ArrowUpDown, Filter } from "lucide-react";

interface WhaleTransaction {
  id: number;
  coin: string;
  exchange: string;
  quantity: string;
  total: string;
  side: "BUY" | "SELL";
  date: string;
  time: string;
  marketcap: string;
  maker: string;
  age: string;
  timestamp: number;
}

interface WhalesProps {
  onBackToTrading?: () => void;
}

const Whales = ({ onBackToTrading }: WhalesProps = {}) => {
  const [timeFilter, setTimeFilter] = useState("1 Hour");
  const [symbolFilter, setSymbolFilter] = useState("All Symbols");
  const [exchangeFilter, setExchangeFilter] = useState("All Exchanges");
  const [tradeFilter, setTradeFilter] = useState("All Trades");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof WhaleTransaction>("timestamp");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [favoriteCoins, setFavoriteCoins] = useState<Set<string>>(new Set());
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  // Sample whale transaction data
  const [whaleTransactions] = useState<WhaleTransaction[]>([
    {
      id: 1,
      coin: "BTC-USD",
      exchange: "Coinbase Pro",
      quantity: "2.00000 BTC",
      total: "236,686.00 USD",
      side: "SELL",
      date: "2024-01-19",
      time: "14:23:45",
      marketcap: "$2.1T",
      maker: "0x742d35Cc6634C0532925a3b8D404fddBD4f4d4d4",
      age: "23 seconds ago",
      timestamp: Date.now() - 23000,
    },
    {
      id: 2,
      coin: "BTC-USD",
      exchange: "Coinbase Pro",
      quantity: "2.00000 BTC",
      total: "236,720.00 USD",
      side: "SELL",
      date: "2024-01-19",
      time: "14:22:18",
      marketcap: "$2.1T",
      maker: "0x742d35Cc6634C0532925a3b8D404fddBD4f4d4d4",
      age: "27 seconds ago",
      timestamp: Date.now() - 27000,
    },
    {
      id: 3,
      coin: "BTC-USD",
      exchange: "Bybit Futures",
      quantity: "907,200 Cont",
      total: "907,200.00 USD",
      side: "BUY",
      date: "2024-01-19",
      time: "14:21:32",
      marketcap: "$2.1T",
      maker: "0x8f3Cf7ad23Cd3CaDbD9735aff958023239c6A063",
      age: "28 seconds ago",
      timestamp: Date.now() - 28000,
    },
    {
      id: 4,
      coin: "BTC-EUR",
      exchange: "Bitstamp",
      quantity: "0.23742489 BTC",
      total: "24,145.87 EUR",
      side: "BUY",
      date: "2024-01-19",
      time: "14:20:55",
      marketcap: "$2.1T",
      maker: "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
      age: "28 seconds ago",
      timestamp: Date.now() - 28000,
    },
    {
      id: 5,
      coin: "ETH-USD",
      exchange: "Binance",
      quantity: "150.5 ETH",
      total: "489,125.50 USD",
      side: "BUY",
      date: "2024-01-19",
      time: "14:19:12",
      marketcap: "$391B",
      maker: "0xA0b86a33E6411a3b9e6d3a8b5c6e7d8f9e0a1b2c",
      age: "4 minutes ago",
      timestamp: Date.now() - 240000,
    },
    {
      id: 6,
      coin: "SOL-USD",
      exchange: "FTX",
      quantity: "5,000 SOL",
      total: "675,000.00 USD",
      side: "SELL",
      date: "2024-01-19",
      time: "14:15:33",
      marketcap: "$59B",
      maker: "0xB1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0",
      age: "8 minutes ago",
      timestamp: Date.now() - 480000,
    },
  ]);

  // Chart data for whale trades visualization
  const chartData = [
    { time: "00:00", buy: 50, sell: -30 },
    { time: "04:00", buy: 80, sell: -60 },
    { time: "08:00", buy: 35, sell: -25 },
    { time: "12:00", buy: 90, sell: -80 },
    { time: "16:00", buy: 45, sell: -70 },
    { time: "20:00", buy: 100, sell: -50 },
    { time: "24:00", buy: 75, sell: -40 },
  ];

  // Filter and sort transactions
  const filteredTransactions = whaleTransactions
    .filter(tx => {
      // Filter by favorites if "Favorites" is selected in symbol filter
      if (symbolFilter === "Favorites") {
        if (favoriteCoins.size === 0) return false;
        return favoriteCoins.has(tx.coin);
      }
      
      // Filter by symbol
      if (symbolFilter !== "All Symbols" && symbolFilter !== "Favorites") {
        if (!tx.coin.toLowerCase().includes(symbolFilter.toLowerCase())) {
          return false;
        }
      }
      
      // Filter by exchange
      if (exchangeFilter !== "All Exchanges") {
        if (tx.exchange !== exchangeFilter) {
          return false;
        }
      }
      
      // Filter by trade type
      if (tradeFilter !== "All Trades") {
        if (tradeFilter === "Buy Only" && tx.side !== "BUY") return false;
        if (tradeFilter === "Sell Only" && tx.side !== "SELL") return false;
      }
      
      // Search filter
      if (searchQuery) {
        return tx.coin.toLowerCase().includes(searchQuery.toLowerCase()) ||
               tx.exchange.toLowerCase().includes(searchQuery.toLowerCase()) ||
               tx.maker.toLowerCase().includes(searchQuery.toLowerCase());
      }
      
      return true;
    })
    .sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc' 
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }
      
      return 0;
    });

  const handleSort = (field: keyof WhaleTransaction) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const toggleCoinSelection = (coin: string) => {
    const newFavorites = new Set(favoriteCoins);
    if (newFavorites.has(coin)) {
      newFavorites.delete(coin);
    } else {
      newFavorites.add(coin);
    }
    setFavoriteCoins(newFavorites);
  };

  const formatAge = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d`;
    if (hours > 0) return `${hours}h`;
    if (minutes > 0) return `${minutes}m`;
    return `${seconds}s`;
  };

  const SortableHeader = ({ field, children }: { field: keyof WhaleTransaction; children: React.ReactNode }) => (
    <th 
      className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition-colors"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        <ArrowUpDown size={12} className={sortField === field ? 'text-blue-400' : 'text-gray-500'} />
      </div>
    </th>
  );

  return (
    <ThemeProvider>
      <div className="bg-gray-900 text-white min-h-screen font-['Inter']">
        {/* Header */}
        <div className="border-b border-gray-700">
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              {onBackToTrading && (
                <button
                  onClick={onBackToTrading}
                  className="px-3 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
                >
                  ← Back to Trading
                </button>
              )}
              <h1 className="text-2xl font-bold">WHALE TRADES</h1>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
            </div>
          </div>
        </div>

        <div className="p-6">
          {/* Chart Section */}
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-bold text-center mb-6">Whale Trades</h2>
            
            {/* Simple Bar Chart */}
            <div className="relative h-64 mb-6">
              {/* Y-Axis Labels */}
              <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-gray-400 z-10">
                <span>150M</span>
                <span>100M</span>
                <span>50M</span>
                <span>0</span>
                <span>-50M</span>
                <span>-100M</span>
                <span>-150M</span>
              </div>
              
              {/* Chart Container with Grid Lines */}
              <div className="ml-12 h-full relative">
                {/* Horizontal Grid Lines */}
                <div className="absolute inset-0 flex flex-col justify-between">
                  {[...Array(7)].map((_, i) => (
                    <div key={i} className="border-t border-gray-600 opacity-30"></div>
                  ))}
                </div>
                
                {/* Zero Line (Middle) - Thicker and more visible */}
                <div className="absolute top-1/2 left-0 right-0 border-t-2 border-gray-400 z-20"></div>
                
                {/* Vertical Grid Lines and Bars */}
                <div className="h-full flex items-center justify-between relative">
                {chartData.map((data, index) => (
                  <div key={index} className="flex flex-col items-center w-16 relative">
                    {/* Vertical Grid Line */}
                    <div className="absolute top-0 bottom-0 left-1/2 border-l border-gray-600 opacity-30 -translate-x-0.5"></div>
                    
                    {/* Buy bars (positive) - from center upward */}
                    <div 
                      className="bg-blue-500 w-12 absolute bottom-1/2"
                      style={{ 
                        height: `${(data.buy / 150) * 128}px`,
                        transform: 'translateY(0)'
                      }}
                    ></div>
                    
                    {/* Sell bars (negative) - from center downward */}
                    <div 
                      className="bg-red-500 w-12 absolute top-1/2"
                      style={{ 
                        height: `${(Math.abs(data.sell) / 150) * 128}px`
                      }}
                    ></div>
                  </div>
                ))}
                </div>
              </div>
            </div>
          </div>

          {/* Filters - Between Chart and Table */}
          <div className="flex items-center gap-4 mb-6">
            <select 
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
            >
              <option>1 Hour</option>
              <option>6 Hours</option>
              <option>24 Hours</option>
              <option>7 Days</option>
            </select>

            <select 
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
            >
              <option>All Symbols</option>
              <option>⭐ Favorites</option>
              <option>BTC</option>
              <option>ETH</option>
              <option>SOL</option>
            </select>

            <select 
              value={exchangeFilter}
              onChange={(e) => setExchangeFilter(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
            >
              <option>All Exchanges</option>
              <option>Coinbase Pro</option>
              <option>Binance</option>
              <option>Bybit</option>
            </select>

            <select 
              value={tradeFilter}
              onChange={(e) => setTradeFilter(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
            >
              <option>All Trades</option>
              <option>Buy Only</option>
              <option>Sell Only</option>
            </select>

            <div className="relative ml-auto">
              <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded pl-10 pr-4 py-2 text-white text-sm w-64"
              />
            </div>
          </div>

          {/* Filtered by large transactions indicator */}
          <div className="mb-4">
            <span className="text-sm text-gray-400">» Filtered by large transactions</span>
          </div>

          {/* Table */}
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700">
                  <tr>
                    <SortableHeader field="id">#</SortableHeader>
                    <SortableHeader field="coin">Name</SortableHeader>
                    <SortableHeader field="exchange">Exchange</SortableHeader>
                    <SortableHeader field="quantity">Quantity</SortableHeader>
                    <SortableHeader field="total">Total</SortableHeader>
                    <SortableHeader field="side">Side</SortableHeader>
                    <SortableHeader field="timestamp">Date/Time</SortableHeader>
                    <SortableHeader field="marketcap">Market Cap</SortableHeader>
                    <SortableHeader field="maker">Maker</SortableHeader>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      ⭐
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {filteredTransactions.map((tx) => (
                    <tr 
                      key={tx.id} 
                      className="hover:bg-gray-700 transition-colors"
                    >
                      <td className="px-4 py-3 text-sm text-white">{tx.id}</td>
                      <td className="px-4 py-3 text-sm font-medium text-white">{tx.coin}</td>
                      <td className="px-4 py-3 text-sm text-gray-300">{tx.exchange}</td>
                      <td className="px-4 py-3 text-sm font-mono text-white">{tx.quantity}</td>
                      <td className="px-4 py-3 text-sm font-mono font-semibold text-white">{tx.total}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${
                          tx.side === "BUY" 
                            ? "bg-green-900 text-green-200" 
                            : "bg-red-900 text-red-200"
                        }`}>
                          {tx.side}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">{tx.date} {tx.time}</td>
                      <td className="px-4 py-3 text-sm font-mono text-white">{tx.marketcap}</td>
                      <td className="px-4 py-3 text-sm font-mono text-blue-400">
                        {tx.maker.slice(0, 8)}...{tx.maker.slice(-4)}
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={favoriteCoins.has(tx.coin)}
                          onChange={() => toggleCoinSelection(tx.coin)}
                          className="rounded text-yellow-500"
                        />
                        {favoriteCoins.has(tx.coin) && (
                          <span className="ml-2 text-yellow-500">⭐</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredTransactions.length === 0 && (
              <div className="text-center py-12 text-gray-400">
                {symbolFilter === "⭐ Favorites" && favoriteCoins.size === 0 
                  ? "No favorite coins selected. Mark coins with ⭐ to see them here."
                  : "No whale transactions found matching your criteria."
                }
              </div>
            )}
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default Whales;