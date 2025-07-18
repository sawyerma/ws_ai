import { useState, useEffect } from "react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";
import { Search, ArrowUpDown, Filter } from "lucide-react";

// Backend Whale Event Interface - basierend auf ClickHouse Schema
interface WhaleEvent {
  event_id: string;
  ts: string;
  chain: string;
  tx_hash: string;
  from_addr: string;
  to_addr: string;
  token?: string;
  symbol: string;
  amount: number;
  is_native: boolean;
  exchange: string;
  amount_usd: number;
  from_exchange: string;
  from_country: string;
  from_city: string;
  to_exchange: string;
  to_country: string;
  to_city: string;
  is_cross_border: boolean;
  source: string;
  threshold_usd: number;
  coin_rank: number;
  created_at: string;
}

// System Status Interface
interface WhaleSystemStatus {
  backfill_status: "Running" | "Completed" | "Error";
  backfill_date: string; // dd.mm.yyyy
  test_status: "passed" | "failed";
  last_test_run: string;
}

// Legacy Interface für Kompatibilität
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
  // Backend Data States
  const [whaleEvents, setWhaleEvents] = useState<WhaleEvent[]>([]);
  const [systemStatus, setSystemStatus] = useState<WhaleSystemStatus>({
    backfill_status: "Running",
    backfill_date: "15.01.2025",
    test_status: "passed",
    last_test_run: new Date().toISOString()
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Chart Data States
  const [chartData, setChartData] = useState<Array<{time: string, buy: number, sell: number}>>([]);
  const [chartLoading, setChartLoading] = useState(true);
  
  // Available Coins (dynamically populated from backend)
  const [availableCoins, setAvailableCoins] = useState<string[]>([]);
  
  // Available Exchanges (dynamically populated from backend)
  const [availableExchanges, setAvailableExchanges] = useState<string[]>([]);

  // Filter States
  const [timeFilter, setTimeFilter] = useState("1 Hour");
  const [symbolFilter, setSymbolFilter] = useState("All Symbols");
  const [exchangeFilter, setExchangeFilter] = useState("All Exchanges");
  const [tradeFilter, setTradeFilter] = useState("All Trades");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof WhaleTransaction>("timestamp");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [favoriteCoins, setFavoriteCoins] = useState<Set<string>>(new Set());
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  // API Configuration
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // API Functions
  const fetchWhaleEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE}/api/whales/recent?limit=50`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setWhaleEvents(data.events || []);
    } catch (err) {
      setError(`Failed to load whale events: ${err instanceof Error ? err.message : 'Unknown error'}`);
      console.error('Whale events fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/whales/status`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSystemStatus({
        backfill_status: data.backfill_status || "Running",
        backfill_date: data.backfill_date || "15.01.2025",
        test_status: data.test_status || "passed",
        last_test_run: data.last_test_run || new Date().toISOString()
      });
    } catch (err) {
      console.error('System status fetch error:', err);
      // Fallback status wenn API fehlschlägt
      setSystemStatus(prev => ({
        ...prev,
        test_status: "failed",
        last_test_run: new Date().toISOString()
      }));
    }
  };

  const fetchChartData = async () => {
    try {
      setChartLoading(true);
      
      // Filter whale events by symbol if specified
      let eventsToProcess = whaleEvents;
      if (symbolFilter !== "All Symbols" && symbolFilter !== "⭐ Favorites") {
        eventsToProcess = eventsToProcess.filter(event => 
          event.symbol.toUpperCase() === symbolFilter.toUpperCase()
        );
      }
      
      // Filter whale events by exchange if specified
      if (exchangeFilter !== "All Exchanges") {
        eventsToProcess = eventsToProcess.filter(event => {
          const eventExchange = event.exchange || event.from_exchange || event.to_exchange;
          return eventExchange === exchangeFilter;
        });
      }
      
      // Convert to hourly chart data
      const hourlyData = [];
      for (let hour = 0; hour < 24; hour += 4) {
        const hourStr = hour.toString().padStart(2, '0') + ':00';
        
        // Find data for this hour range
        const hourEvents = eventsToProcess.filter(event => {
          const eventHour = new Date(event.ts).getHours();
          return eventHour >= hour && eventHour < hour + 4;
        });
        
        // Calculate buy/sell volumes (in millions)
        const buyVolume = hourEvents
          .filter(event => event.from_exchange === '' && event.to_exchange !== '')
          .reduce((sum, event) => sum + (event.amount_usd || 0), 0) / 1_000_000;
        
        const sellVolume = hourEvents
          .filter(event => event.from_exchange !== '' && event.to_exchange === '')
          .reduce((sum, event) => sum + (event.amount_usd || 0), 0) / 1_000_000;
        
        hourlyData.push({
          time: hourStr,
          buy: Math.round(buyVolume),
          sell: -Math.round(sellVolume)
        });
      }
      
      // Always use backend data - no fallback to mock data
      setChartData(hourlyData);
      
    } catch (err) {
      console.error('Chart data fetch error:', err);
      // Set empty data on error - no mock fallback
      setChartData([
        { time: "00:00", buy: 0, sell: 0 },
        { time: "04:00", buy: 0, sell: 0 },
        { time: "08:00", buy: 0, sell: 0 },
        { time: "12:00", buy: 0, sell: 0 },
        { time: "16:00", buy: 0, sell: 0 },
        { time: "20:00", buy: 0, sell: 0 },
      ]);
    } finally {
      setChartLoading(false);
    }
  };

  // Initial data load and timers
  useEffect(() => {
    // Load initial data
    fetchWhaleEvents();
    fetchSystemStatus();
    fetchChartData();

    // Set up 10-minute timer for tests
    const testInterval = setInterval(() => {
      fetchSystemStatus();
    }, 10 * 60 * 1000); // 10 minutes

    // Set up 30-second timer for whale events refresh
    const whaleInterval = setInterval(() => {
      fetchWhaleEvents();
    }, 30 * 1000); // 30 seconds

    // Set up 5-minute timer for chart data refresh
    const chartInterval = setInterval(() => {
      fetchChartData();
    }, 5 * 60 * 1000); // 5 minutes

    return () => {
      clearInterval(testInterval);
      clearInterval(whaleInterval);
      clearInterval(chartInterval);
    };
  }, []);

  // Extract available coins from whale events
  useEffect(() => {
    if (whaleEvents.length > 0) {
      const uniqueCoins = [...new Set(whaleEvents.map(event => event.symbol))].sort();
      setAvailableCoins(uniqueCoins);
    }
  }, [whaleEvents]);

  // Extract available exchanges from whale events
  useEffect(() => {
    if (whaleEvents.length > 0) {
      const uniqueExchanges = [...new Set(whaleEvents.map(event => 
        event.exchange || event.from_exchange || event.to_exchange
      ))].filter(ex => ex && ex !== '').sort();
      setAvailableExchanges(uniqueExchanges);
    }
  }, [whaleEvents]);

  // Update chart when symbol or exchange filter changes
  useEffect(() => {
    if (whaleEvents.length > 0) {
      fetchChartData();
    }
  }, [symbolFilter, exchangeFilter, whaleEvents]);


  // Convert Backend Data to Display Format
  const formatWhaleEvent = (event: WhaleEvent) => {
    const date = new Date(event.ts);
    return {
      id: event.event_id,
      chain: event.chain,
      symbol: event.symbol,
      amount: event.amount.toFixed(4),
      amount_usd: event.amount_usd,
      from_country: event.from_country,
      to_country: event.to_country,
      from_city: event.from_city,
      to_city: event.to_city,
      exchange: event.exchange || event.from_exchange || event.to_exchange,
      tx_hash: event.tx_hash,
      is_cross_border: event.is_cross_border,
      timestamp: date.getTime(),
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString(),
      from_addr: event.from_addr,
      to_addr: event.to_addr
    };
  };

  // Filter and sort whale events
  const filteredWhaleEvents = whaleEvents
    .filter(event => {
      // Filter by symbol
      if (symbolFilter !== "All Symbols" && symbolFilter !== "Favorites") {
        if (!event.symbol.toLowerCase().includes(symbolFilter.toLowerCase())) {
          return false;
        }
      }
      
      // Filter by exchange
      if (exchangeFilter !== "All Exchanges") {
        const eventExchange = event.exchange || event.from_exchange || event.to_exchange;
        if (eventExchange !== exchangeFilter) {
          return false;
        }
      }
      
      // Search filter
      if (searchQuery) {
        return event.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
               event.chain.toLowerCase().includes(searchQuery.toLowerCase()) ||
               event.tx_hash.toLowerCase().includes(searchQuery.toLowerCase());
      }
      
      return true;
    })
    .sort((a, b) => {
      // Sort by timestamp (newest first)
      const aTime = new Date(a.ts).getTime();
      const bTime = new Date(b.ts).getTime();
      return sortDirection === 'asc' ? aTime - bTime : bTime - aTime;
    })
    .map(formatWhaleEvent);

  // Display only real backend data - no mock fallback
  const displayTransactions = filteredWhaleEvents;

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
              {availableCoins.map(coin => (
                <option key={coin} value={coin}>{coin}</option>
              ))}
            </select>

            <select 
              value={exchangeFilter}
              onChange={(e) => setExchangeFilter(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
            >
              <option>All Exchanges</option>
              {availableExchanges.map(exchange => (
                <option key={exchange} value={exchange}>{exchange}</option>
              ))}
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
                  {displayTransactions.map((tx: any) => (
                    <tr 
                      key={tx.id} 
                      className="hover:bg-gray-700 transition-colors"
                    >
                      <td className="px-4 py-3 text-sm text-white">{tx.id}</td>
                      <td className="px-4 py-3 text-sm font-medium text-white">
                        {tx.symbol || tx.coin}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">{tx.exchange}</td>
                      <td className="px-4 py-3 text-sm font-mono text-white">
                        {tx.amount ? `${tx.amount} ${tx.symbol}` : tx.quantity}
                      </td>
                      <td className="px-4 py-3 text-sm font-mono font-semibold text-white">
                        {tx.amount_usd ? `$${tx.amount_usd.toLocaleString()}` : tx.total}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${
                          tx.is_cross_border ? "bg-yellow-900 text-yellow-200" : "bg-green-900 text-green-200"
                        }`}>
                          {tx.is_cross_border ? "CROSS" : "SAME"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-300">{tx.date} {tx.time}</td>
                      <td className="px-4 py-3 text-sm font-mono text-white">
                        {tx.from_country} → {tx.to_country}
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-blue-400">
                        {tx.tx_hash ? `${tx.tx_hash.slice(0, 8)}...${tx.tx_hash.slice(-4)}` : 
                         (tx.maker && `${tx.maker.slice(0, 8)}...${tx.maker.slice(-4)}`)}
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={favoriteCoins.has(tx.symbol || tx.coin)}
                          onChange={() => toggleCoinSelection(tx.symbol || tx.coin)}
                          className="rounded text-yellow-500"
                        />
                        {favoriteCoins.has(tx.symbol || tx.coin) && (
                          <span className="ml-2 text-yellow-500">⭐</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {displayTransactions.length === 0 && (
              <div className="text-center py-12 text-gray-400">
                {loading ? "Loading whale transactions..." : 
                 error ? `Error: ${error}` :
                 symbolFilter === "⭐ Favorites" && favoriteCoins.size === 0 
                  ? "No favorite coins selected. Mark coins with ⭐ to see them here."
                  : "No whale transactions found matching your criteria."
                }
              </div>
            )}
          </div>
        </div>

        {/* Status Panel - Bottom Right */}
        <div className="fixed bottom-6 right-6 bg-gray-800 border border-gray-700 rounded-lg p-4 w-80 shadow-lg z-50">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white">System Status</h3>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                loading ? 'bg-yellow-500' : 
                error ? 'bg-red-500' : 
                'bg-green-500'
              }`}></div>
              <span className="text-xs text-gray-400">
                {loading ? 'Loading...' : error ? 'Error' : 'Online'}
              </span>
            </div>
          </div>
          
          <div className="space-y-2">
            {/* Backfill Status */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Backfill:</span>
              <div className="flex items-center gap-2">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${
                  systemStatus.backfill_status === "Running" ? "bg-blue-900 text-blue-200" :
                  systemStatus.backfill_status === "Completed" ? "bg-green-900 text-green-200" :
                  "bg-red-900 text-red-200"
                }`}>
                  {systemStatus.backfill_status}
                </span>
                <span className="text-xs text-gray-300">bis {systemStatus.backfill_date}</span>
              </div>
            </div>

            {/* Test Status */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Tests:</span>
              <div className="flex items-center gap-2">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${
                  systemStatus.test_status === "passed" ? "bg-green-900 text-green-200" : "bg-red-900 text-red-200"
                }`}>
                  {systemStatus.test_status === "passed" ? "✅ Passed" : "❌ Failed"}
                </span>
              </div>
            </div>

            {/* Last Test Run */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Last Test:</span>
              <span className="text-xs text-gray-300">
                {new Date(systemStatus.last_test_run).toLocaleTimeString()}
              </span>
            </div>

            {/* Data Count */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Events:</span>
              <span className="text-xs text-gray-300">
                {whaleEvents.length} loaded
              </span>
            </div>

            {/* Refresh Timer */}
            <div className="flex items-center justify-between pt-2 border-t border-gray-700">
              <span className="text-xs text-gray-400">Auto-refresh:</span>
              <span className="text-xs text-gray-300">30s / 10m</span>
            </div>
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default Whales;
