import { useState } from "react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";

interface NewsProps {
  onBackToTrading?: () => void;
}

const News = ({ onBackToTrading }: NewsProps = {}) => {
  const [activeCategory, setActiveCategory] = useState("all");

  const sidebarItems = [
    { id: "all", name: "All News", icon: "📰" },
    { id: "bitcoin", name: "Bitcoin", icon: "₿" },
    { id: "ethereum", name: "Ethereum", icon: "Ξ" },
    { id: "defi", name: "DeFi", icon: "🏦" },
    { id: "nft", name: "NFTs", icon: "🎨" },
    { id: "regulations", name: "Regulations", icon: "⚖️" },
    { id: "partnerships", name: "Partnerships", icon: "🤝" },
    { id: "technology", name: "Technology", icon: "⚙️" },
  ];

  const newsArticles = [
    {
      title: "Bitcoin Reaches New All-Time High Amid Institutional Adoption",
      summary:
        "Major corporations continue to add Bitcoin to their treasury reserves, driving price momentum to unprecedented levels.",
      source: "CryptoDaily",
      time: "2 hours ago",
      sentiment: "bullish",
      impact: "high",
    },
    {
      title: "Ethereum 2.0 Staking Surpasses 15 Million ETH",
      summary:
        "The Ethereum network shows strong validator participation as staking rewards attract more institutional investors.",
      source: "DeFi Pulse",
      time: "4 hours ago",
      sentiment: "bullish",
      impact: "medium",
    },
    {
      title: "SEC Announces New Cryptocurrency Regulatory Framework",
      summary:
        "The Securities and Exchange Commission releases comprehensive guidelines for digital asset classification.",
      source: "Regulatory News",
      time: "6 hours ago",
      sentiment: "neutral",
      impact: "high",
    },
    {
      title: "Major DeFi Protocol Reports $50M Total Value Locked Growth",
      summary:
        "Decentralized finance continues to attract liquidity as yield farming opportunities expand across multiple chains.",
      source: "DeFi Weekly",
      time: "8 hours ago",
      sentiment: "bullish",
      impact: "medium",
    },
    {
      title: "Central Bank Digital Currency Pilot Launches in Three Countries",
      summary:
        "Government-backed digital currencies enter testing phases as traditional finance explores blockchain technology.",
      source: "FinTech Today",
      time: "12 hours ago",
      sentiment: "neutral",
      impact: "high",
    },
  ];

  const renderContent = () => (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Crypto News Feed
          </h2>
          <div className="flex items-center gap-4">
            <select className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
              <option>Last 24 hours</option>
              <option>Last week</option>
              <option>Last month</option>
            </select>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              Refresh
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-green-50 dark:bg-green-900 p-3 rounded-lg">
            <h3 className="text-sm font-semibold text-green-800 dark:text-green-200">
              Bullish News
            </h3>
            <p className="text-xl font-bold text-green-900 dark:text-green-100">
              67%
            </p>
          </div>
          <div className="bg-red-50 dark:bg-red-900 p-3 rounded-lg">
            <h3 className="text-sm font-semibold text-red-800 dark:text-red-200">
              Bearish News
            </h3>
            <p className="text-xl font-bold text-red-900 dark:text-red-100">
              18%
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
              Neutral
            </h3>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              15%
            </p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900 p-3 rounded-lg">
            <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-200">
              Total Articles
            </h3>
            <p className="text-xl font-bold text-blue-900 dark:text-blue-100">
              247
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {newsArticles.map((article, index) => (
          <div
            key={index}
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white pr-4 leading-tight">
                {article.title}
              </h3>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    article.sentiment === "bullish"
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                      : article.sentiment === "bearish"
                        ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                        : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                  }`}
                >
                  {article.sentiment}
                </span>
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    article.impact === "high"
                      ? "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200"
                      : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                  }`}
                >
                  {article.impact} impact
                </span>
              </div>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-3 leading-relaxed">
              {article.summary}
            </p>
            <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
              <span className="font-medium">{article.source}</span>
              <span>{article.time}</span>
            </div>
          </div>
        ))}
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
              <h1 className="text-2xl font-bold">Crypto News</h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                Live Feed
              </span>
            </div>
            <div className="flex items-center gap-4">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Subscribe
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
                Categories
              </h3>
              <nav className="space-y-1">
                {sidebarItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveCategory(item.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeCategory === item.id
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

export default News;
