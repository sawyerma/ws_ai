import { useState } from "react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";

interface WhalesProps {
  onBackToTrading?: () => void;
}

const Whales = ({ onBackToTrading }: WhalesProps = {}) => {
  const [activeTracker, setActiveTracker] = useState("movements");

  const sidebarItems = [
    { id: "movements", name: "Whale Movements", icon: "🐋" },
    { id: "wallets", name: "Tracked Wallets", icon: "💰" },
    { id: "alerts", name: "Whale Alerts", icon: "🚨" },
    { id: "patterns", name: "Movement Patterns", icon: "📊" },
    { id: "exchanges", name: "Exchange Flows", icon: "🏦" },
    { id: "dormant", name: "Dormant Coins", icon: "😴" },
    { id: "accumulation", name: "Accumulation Zones", icon: "📈" },
    { id: "distribution", name: "Distribution", icon: "📉" },
  ];

  const whaleMovements = [
    {
      time: "2 min ago",
      amount: "1,247 BTC",
      value: "$52.3M",
      from: "Unknown Wallet",
      to: "Binance",
      type: "deposit",
    },
    {
      time: "15 min ago",
      amount: "3,891 ETH",
      value: "$10.2M",
      from: "Coinbase Pro",
      to: "Unknown Wallet",
      type: "withdrawal",
    },
    {
      time: "23 min ago",
      amount: "890 BTC",
      value: "$37.4M",
      from: "Kraken",
      to: "Cold Storage",
      type: "withdrawal",
    },
    {
      time: "1 hour ago",
      amount: "5,234 ETH",
      value: "$13.7M",
      from: "Unknown Wallet",
      to: "Uniswap V3",
      type: "interaction",
    },
  ];

  const renderContent = () => (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Recent Whale Movements
        </h2>
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 dark:bg-blue-900 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200">
              Total Volume 24h
            </h3>
            <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              $2.4B
            </p>
          </div>
          <div className="bg-green-50 dark:bg-green-900 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">
              Active Whales
            </h3>
            <p className="text-2xl font-bold text-green-900 dark:text-green-100">
              1,247
            </p>
          </div>
          <div className="bg-red-50 dark:bg-red-900 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-red-800 dark:text-red-200">
              Large Movements
            </h3>
            <p className="text-2xl font-bold text-red-900 dark:text-red-100">
              89
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Live Whale Tracker
          </h3>
        </div>
        <div className="overflow-hidden">
          {whaleMovements.map((movement, index) => (
            <div
              key={index}
              className="border-b border-gray-200 dark:border-gray-700 last:border-b-0 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      movement.type === "deposit"
                        ? "bg-red-500"
                        : movement.type === "withdrawal"
                          ? "bg-green-500"
                          : "bg-blue-500"
                    }`}
                  ></div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {movement.amount}
                      </span>
                      <span className="text-gray-600 dark:text-gray-400">
                        ({movement.value})
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {movement.from} → {movement.to}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {movement.time}
                  </div>
                  <div
                    className={`text-xs px-2 py-1 rounded-full ${
                      movement.type === "deposit"
                        ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                        : movement.type === "withdrawal"
                          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                          : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                    }`}
                  >
                    {movement.type}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <ThemeProvider>
      <div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white min-h-screen font-['Inter']">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700">
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
              <h1 className="text-2xl font-bold">Whale Tracker</h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                Real-time
              </span>
            </div>
            <div className="flex items-center gap-4">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Set Alert
              </button>
              <ThemeToggle />
            </div>
          </div>
        </div>

        <div className="flex h-[calc(100vh-73px)]">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0">
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
                Whale Analytics
              </h3>
              <nav className="space-y-1">
                {sidebarItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveTracker(item.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeTracker === item.id
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
          </div>

          {/* Main Content */}
          {renderContent()}
        </div>
      </div>
    </ThemeProvider>
  );
};

export default Whales;
