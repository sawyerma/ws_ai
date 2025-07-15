import { useState, useEffect } from "react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";
import CoinSettingsModal from "../components/ui/coin-settings-modal";
import { getSettings, CoinSetting } from "../api/symbols";
import { RefreshCw, Settings, Download, Database as DatabaseIcon, Clock, TrendingUp } from "lucide-react";

interface DatabaseProps {
  onBackToTrading?: () => void;
}

const Database = ({ onBackToTrading }: DatabaseProps = {}) => {
  const [activeTable, setActiveTable] = useState("trades");
  const [searchQuery, setSearchQuery] = useState("");
  const [settings, setSettings] = useState<CoinSetting[]>([]);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Load settings from backend
  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getSettings();
      setSettings(data);
      setLastUpdate(new Date());
    } catch (err) {
      setError('Failed to load settings');
      console.error('Error loading settings:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
  }, []);

  // Get stats from settings
  const getStats = () => {
    const liveEnabled = settings.filter(s => s.store_live).length;
    const historyEnabled = settings.filter(s => s.load_history).length;
    const totalSymbols = settings.length;
    const favoriteSymbols = settings.filter(s => s.favorite).length;
    
    return {
      liveEnabled,
      historyEnabled,
      totalSymbols,
      favoriteSymbols,
    };
  };

  const stats = getStats();

  const sidebarItems = [
    { id: "trades", name: "Trades", icon: "💹" },
    { id: "orderbook", name: "Orderbook", icon: "📊" },
    { id: "candlesticks", name: "Candlesticks", icon: "🕯️" },
    { id: "volume", name: "Volume", icon: "📈" },
    { id: "analytics", name: "Analytics", icon: "🔍" },
    { id: "wallets", name: "Wallets", icon: "💰" },
    { id: "transactions", name: "Transactions", icon: "🔄" },
    { id: "alerts", name: "Alerts", icon: "🚨" },
  ];

  const sampleTradesData = [
    {
      id: 1,
      timestamp: "2024-01-19 14:23:45",
      pair: "BTC/USDT",
      side: "buy",
      price: "42,350.50",
      amount: "0.0245",
      total: "1,037.59",
      fee: "1.04",
    },
    {
      id: 2,
      timestamp: "2024-01-19 14:22:12",
      pair: "ETH/USDT",
      side: "sell",
      price: "2,650.25",
      amount: "1.2500",
      total: "3,312.81",
      fee: "3.31",
    },
    {
      id: 3,
      timestamp: "2024-01-19 14:20:38",
      pair: "BTC/USDT",
      side: "buy",
      price: "42,280.00",
      amount: "0.0158",
      total: "668.02",
      fee: "0.67",
    },
    {
      id: 4,
      timestamp: "2024-01-19 14:19:55",
      pair: "ADA/USDT",
      side: "sell",
      price: "0.4825",
      amount: "2,500.00",
      total: "1,206.25",
      fee: "1.21",
    },
    {
      id: 5,
      timestamp: "2024-01-19 14:18:27",
      pair: "SOL/USDT",
      side: "buy",
      price: "98.75",
      amount: "5.2400",
      total: "517.47",
      fee: "0.52",
    },
  ];

  const renderTradesTable = () => (
    <div className="flex-1 overflow-hidden flex flex-col">
      {/* Search and Filter Bar */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Trading Database
          </h2>
          <div className="flex items-center gap-4">
            <input
              type="text"
              placeholder="Search trades..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option>Last 24h</option>
              <option>Last 7 days</option>
              <option>Last 30 days</option>
              <option>All time</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Pair
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Side
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Price
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Amount
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Total
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Fee
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {sampleTradesData.map((trade) => (
              <tr
                key={trade.id}
                className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {trade.timestamp}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                    {trade.pair}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      trade.side === "buy"
                        ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                        : "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200"
                    }`}
                  >
                    {trade.side.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-white">
                  ${trade.price}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-white">
                  {trade.amount}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono font-semibold text-gray-900 dark:text-white">
                  ${trade.total}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500 dark:text-gray-400">
                  ${trade.fee}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTable) {
      case "trades":
        return renderTradesTable();
      default:
        return (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                {sidebarItems.find((item) => item.id === activeTable)?.name}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                This section is under development
              </p>
            </div>
          </div>
        );
    }
  };

  return (
    <ThemeProvider>
      <div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white min-h-screen font-['Inter']">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              {onBackToTrading && (
                <button
                  onClick={onBackToTrading}
                  className="px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center gap-2"
                >
                  ← Back to Trading
                </button>
              )}
              <h1 className="text-2xl font-bold">Trading Database</h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                Live
              </span>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => loadSettings()}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              >
                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                Refresh
              </button>
              <button
                onClick={() => setSettingsModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Settings size={16} />
                Settings
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <Download size={16} />
                Export Data
              </button>
              <ThemeToggle />
            </div>
          </div>
        </div>

        <div className="flex h-[calc(100vh-73px)]">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
                Data Tables
              </h3>
              <nav className="space-y-1">
                {sidebarItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveTable(item.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeTable === item.id
                        ? "bg-blue-600 text-white"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                    }`}
                  >
                    <span className="mr-3">{item.icon}</span>
                    {item.name}
                  </button>
                ))}
              </nav>
            </div>

            {/* Stats Summary */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 mt-8">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
                Quick Stats
              </h4>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Total Symbols
                  </span>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    {stats.totalSymbols}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Live Enabled
                  </span>
                  <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                    {stats.liveEnabled}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    History Enabled
                  </span>
                  <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                    {stats.historyEnabled}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Favorites
                  </span>
                  <span className="text-sm font-semibold text-yellow-600 dark:text-yellow-400">
                    {stats.favoriteSymbols}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Last Update
                  </span>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          {renderContent()}
        </div>

        {/* Settings Modal */}
        <CoinSettingsModal
          isOpen={settingsModalOpen}
          onClose={() => {
            setSettingsModalOpen(false);
            loadSettings(); // Refresh settings after modal closes
          }}
        />
      </div>
    </ThemeProvider>
  );
};

export default Database;
