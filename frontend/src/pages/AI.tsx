import { useState } from "react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";

interface AIProps {
  onBackToTrading?: () => void;
}

const AI = ({ onBackToTrading }: AIProps = {}) => {
  const [activeModel, setActiveModel] = useState("prediction");

  const sidebarItems = [
    { id: "prediction", name: "Price Prediction", icon: "🎯" },
    { id: "sentiment", name: "Market Sentiment", icon: "📊" },
    { id: "patterns", name: "Pattern Recognition", icon: "🔍" },
    { id: "signals", name: "Trading Signals", icon: "📡" },
    { id: "risk", name: "Risk Assessment", icon: "⚠️" },
    { id: "portfolio", name: "Portfolio Optimization", icon: "📈" },
    { id: "anomaly", name: "Anomaly Detection", icon: "���" },
    { id: "models", name: "AI Models", icon: "🤖" },
  ];

  const renderContent = () => (
    <div className="flex-1 p-6">
      <div className="text-center py-20">
        <div className="text-6xl mb-4">🤖</div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          AI Trading Assistant
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
          Advanced artificial intelligence tools for trading analysis
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
          <div className="bg-blue-50 dark:bg-blue-900 p-4 rounded-lg">
            <div className="text-2xl mb-2">🎯</div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Price Prediction
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              ML-powered price forecasting
            </p>
          </div>
          <div className="bg-green-50 dark:bg-green-900 p-4 rounded-lg">
            <div className="text-2xl mb-2">📊</div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Sentiment Analysis
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Market emotion tracking
            </p>
          </div>
          <div className="bg-purple-50 dark:bg-purple-900 p-4 rounded-lg">
            <div className="text-2xl mb-2">🔍</div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Pattern Recognition
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Chart pattern detection
            </p>
          </div>
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
              <h1 className="text-2xl font-bold">AI Trading</h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                Neural Network
              </span>
            </div>
            <div className="flex items-center gap-4">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Train Model
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
                AI Tools
              </h3>
              <nav className="space-y-1">
                {sidebarItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveModel(item.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeModel === item.id
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

export default AI;
