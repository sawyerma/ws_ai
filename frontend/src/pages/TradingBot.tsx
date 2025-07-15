import { useState } from "react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";

interface TradingBotProps {
  onBackToTrading?: () => void;
}

const TradingBot = ({ onBackToTrading }: TradingBotProps = {}) => {
  const [activeBot, setActiveBot] = useState("grid");
  const [isRunning, setIsRunning] = useState(false);

  const sidebarItems = [
    { id: "grid", name: "Grid Trading", icon: "🔲" },
    { id: "dca", name: "DCA Bot", icon: "📊" },
    { id: "arbitrage", name: "Arbitrage", icon: "⚖️" },
    { id: "momentum", name: "Momentum", icon: "🚀" },
    { id: "scalping", name: "Scalping", icon: "⚡" },
    { id: "martingale", name: "Martingale", icon: "🎯" },
    { id: "custom", name: "Custom Strategy", icon: "🛠️" },
    { id: "backtest", name: "Backtesting", icon: "📈" },
  ];

  const botStats = [
    { label: "Total Profit", value: "+$2,847.32", color: "text-green-600" },
    { label: "Win Rate", value: "73.2%", color: "text-blue-600" },
    { label: "Active Trades", value: "12", color: "text-orange-600" },
    { label: "Runtime", value: "7d 14h", color: "text-purple-600" },
  ];

  const activeTrades = [
    {
      pair: "BTC/USDT",
      side: "BUY",
      entry: "42,350.50",
      current: "42,890.25",
      pnl: "+$539.75",
      status: "running",
    },
    {
      pair: "ETH/USDT",
      side: "SELL",
      entry: "2,650.25",
      current: "2,598.10",
      pnl: "+$52.15",
      status: "running",
    },
    {
      pair: "SOL/USDT",
      side: "BUY",
      entry: "98.75",
      current: "101.20",
      pnl: "+$245.00",
      status: "running",
    },
  ];

  const renderContent = () => (
    <div className="flex-1 p-6 overflow-y-auto">
      {/* Bot Control Panel */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Grid Trading Bot
          </h2>
          <div className="flex items-center gap-4">
            <div
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                isRunning
                  ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                  : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
              }`}
            >
              {isRunning ? "Running" : "Stopped"}
            </div>
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                isRunning
                  ? "bg-red-600 text-white hover:bg-red-700"
                  : "bg-green-600 text-white hover:bg-green-700"
              }`}
            >
              {isRunning ? "Stop Bot" : "Start Bot"}
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {botStats.map((stat, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow"
            >
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                {stat.label}
              </h3>
              <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Bot Configuration */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Bot Configuration
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Trading Pair
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <option>BTC/USDT</option>
                <option>ETH/USDT</option>
                <option>SOL/USDT</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Investment Amount
              </label>
              <input
                type="number"
                placeholder="1000"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Grid Levels
              </label>
              <input
                type="number"
                placeholder="10"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Price Range (%)
              </label>
              <input
                type="number"
                placeholder="5"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Risk Management
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Stop Loss (%)
              </label>
              <input
                type="number"
                placeholder="5"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Take Profit (%)
              </label>
              <input
                type="number"
                placeholder="10"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max Drawdown (%)
              </label>
              <input
                type="number"
                placeholder="15"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto-restart"
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded"
              />
              <label
                htmlFor="auto-restart"
                className="ml-2 text-sm text-gray-700 dark:text-gray-300"
              >
                Auto-restart on stop
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Active Trades */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Active Trades
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Pair
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Side
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Entry Price
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Current Price
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  P&L
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {activeTrades.map((trade, index) => (
                <tr
                  key={index}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                    {trade.pair}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        trade.side === "BUY"
                          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                          : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                      }`}
                    >
                      {trade.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-gray-900 dark:text-white">
                    ${trade.entry}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-gray-900 dark:text-white">
                    ${trade.current}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono font-semibold text-green-600">
                    {trade.pnl}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      {trade.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
              <h1 className="text-2xl font-bold">Trading Bot</h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                Automated
              </span>
            </div>
            <div className="flex items-center gap-4">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Create Strategy
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
                Bot Strategies
              </h3>
              <nav className="space-y-1">
                {sidebarItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveBot(item.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeBot === item.id
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

            {/* Bot Performance Summary */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 mt-8">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
                Performance
              </h4>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Today's P&L
                  </span>
                  <span className="text-sm font-semibold text-green-600">
                    +$247.32
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Total Trades
                  </span>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    1,847
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Success Rate
                  </span>
                  <span className="text-sm font-semibold text-blue-600">
                    73.2%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Status
                  </span>
                  <span
                    className={`text-sm font-semibold ${
                      isRunning ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {isRunning ? "Active" : "Stopped"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          {renderContent()}
        </div>
      </div>
    </ThemeProvider>
  );
};

export default TradingBot;