import { useState } from "react";
import { X, Search, Star } from "lucide-react";

interface IndicatorsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIndicatorSelect?: (indicator: string) => void;
}

const IndicatorsModal = ({ isOpen, onClose, onIndicatorSelect }: IndicatorsModalProps) => {
  const [activeSection, setActiveSection] = useState("Favoriten");
  const [searchQuery, setSearchQuery] = useState("");
  const [favorites, setFavorites] = useState(
    new Set(["Andean Scalping", "CM_RSI Plus EMA", "Elliott Wave Oscillator", "Candlestick Chart"]),
  );

  if (!isOpen) return null;

  const sidebarItems = [
    { id: "Favoriten", name: "Favoriten", icon: "⭐" },
    { id: "Persönliches", name: "Persönliches", icon: "👤" },
    { id: "TechnischeDaten", name: "Technische Daten", icon: "📊" },
    { id: "Finanzdaten", name: "Finanzdaten", icon: "💰" },
    { id: "Community", name: "Community", icon: "👥" },
    { id: "NurAufEinladung", name: "Nur auf Einladung", icon: "🔒" },
  ];

  const indicatorsList = [
    {
      name: "Candlestick Chart",
      author: "TradingView",
      rating: "Built-in",
      category: "Price Action",
      description: "Additional candlestick chart overlay",
      type: "candlestick"
    },
    {
      name: "Volume",
      author: "TradingView", 
      rating: "Built-in",
      category: "Volume",
      description: "Volume histogram in separate panel",
      type: "volume"
    },
    {
      name: "Andean Scalping",
      author: "unclerc0",
      rating: 593,
      category: "Scalping",
      description: "Advanced scalping strategy based on Andean principles",
      type: "andean"
    },
    {
      name: "CM_RSI Plus EMA",
      author: "ChrisMoody",
      rating: "15.2K",
      category: "RSI",
      description: "Enhanced RSI indicator with Exponential Moving Average",
      type: "rsi"
    },
    {
      name: "Elliott Wave Oscillator",
      author: "koryu",
      rating: "12.2K",
      category: "Wave Analysis",
      description: "Professional Elliott Wave analysis tool",
      type: "elliott"
    },
    {
      name: "Elliott Wave [LuxAlgo]",
      author: "LuxAlgo",
      rating: "11.6K",
      category: "Wave Analysis",
      description: "Premium Elliott Wave detection algorithm",
      isPremium: true,
      type: "elliott-lux"
    },
    {
      name: "EMA 20/50/100/200",
      author: "drsweets",
      rating: "13.9K",
      category: "Moving Average",
      description: "Multiple Exponential Moving Averages overlay",
      type: "ema"
    },
    {
      name: "Machine Learning Moving Average [LuxAlgo]",
      author: "LuxAlgo",
      rating: "4.9K",
      category: "AI/ML",
      description: "AI-powered adaptive moving average",
      type: "ml-ma"
    },
    {
      name: "Momentum With Bullish & Bearish Label",
      author: "FriendOfTheTrend",
      rating: 805,
      category: "Momentum",
      description: "Momentum indicator with clear buy/sell signals",
      type: "momentum"
    },
    {
      name: "Moving Average Exponential Day Trade Pack",
      author: "FTynan",
      rating: 540,
      category: "Day Trading",
      description: "Complete EMA package for day traders",
      type: "ema-pack"
    },
    {
      name: "Moving Average Exponential x 4",
      author: "krogsgard",
      rating: "3.4K",
      category: "Moving Average",
      description: "Four EMA lines with different periods",
      type: "ema-4"
    },
    {
      name: "Multi-Coin Table- Extended",
      author: "tradingview",
      rating: "8.1K",
      category: "Multi-Asset",
      description: "Monitor multiple cryptocurrencies simultaneously",
      type: "multi-coin"
    },
    {
      name: "Optimierte Volumen-Analyse",
      author: "mmw-solutions",
      rating: 1,
      category: "Volume",
      description: "Advanced volume analysis tool",
      isProtected: true,
      type: "volume-analysis"
    },
    {
      name: "Pivot Point Supertrend",
      author: "LonesomeTheBlue",
      rating: "21.9K",
      category: "Trend",
      description: "Enhanced Supertrend with pivot points",
      isPremium: true,
      type: "pivot-supertrend"
    },
    {
      name: "Range Detector [LuxAlgo]",
      author: "LuxAlgo",
      rating: "9.2K",
      category: "Range",
      description: "Automatic range detection and analysis",
      type: "range-detector"
    },
    {
      name: "RSI Candles",
      author: "glaz",
      rating: "17.5K",
      category: "RSI",
      description: "RSI-based candlestick coloring system",
      type: "rsi-candles"
    },
  ];

  const toggleFavorite = (indicatorName: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(indicatorName)) {
      newFavorites.delete(indicatorName);
    } else {
      newFavorites.add(indicatorName);
    }
    setFavorites(newFavorites);
  };

  const handleIndicatorClick = (indicator: any) => {
    if (onIndicatorSelect) {
      onIndicatorSelect(indicator.type);
    }
    // Don't close modal automatically - let user select multiple indicators
  };

  const filteredIndicators = indicatorsList.filter(
    (indicator) =>
      indicator.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      indicator.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
      indicator.category.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const renderIndicatorsList = () => {
    let displayList = filteredIndicators;

    if (activeSection === "Favoriten") {
      displayList = filteredIndicators.filter((indicator) =>
        favorites.has(indicator.name),
      );
    }

    return (
      <div className="flex-1 flex flex-col h-full">
        {/* Search Bar - Fixed at top */}
        <div className="p-6 pb-4 flex-shrink-0">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Suche"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Table Header - Fixed */}
        <div className="px-6 pb-2 flex-shrink-0">
          <div className="grid grid-cols-12 gap-4 text-xs text-gray-400 font-medium pb-2 border-b border-gray-600">
            <div className="col-span-1"></div>
            <div className="col-span-5">SKRIPTNAME</div>
            <div className="col-span-3"></div>
            <div className="col-span-3 text-right"></div>
          </div>
        </div>

        {/* Scrollable Indicators List */}
        <div className="flex-1 overflow-y-auto px-6 pb-6">
          <div className="space-y-1">
            {displayList.map((indicator, index) => (
              <div
                key={index}
                className="grid grid-cols-12 gap-4 py-3 hover:bg-gray-700 rounded transition-colors cursor-pointer group"
                onClick={() => handleIndicatorClick(indicator)}
              >
                {/* Star */}
                <div className="col-span-1 flex items-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFavorite(indicator.name);
                    }}
                    className={`transition-colors ${
                      favorites.has(indicator.name)
                        ? "text-yellow-400"
                        : "text-gray-500 hover:text-yellow-400"
                    }`}
                  >
                    <Star
                      className="w-4 h-4"
                      fill={
                        favorites.has(indicator.name) ? "currentColor" : "none"
                      }
                    />
                  </button>
                </div>

                {/* Indicator Name & Tags */}
                <div className="col-span-5 flex items-center space-x-2">
                  <span className="text-white font-medium">
                    {indicator.name}
                  </span>
                  {indicator.isPremium && (
                    <span className="bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded font-medium">
                      EP
                    </span>
                  )}
                  {indicator.isProtected && (
                    <div className="w-3 h-3 bg-green-500 rounded-full flex items-center justify-center">
                      <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                    </div>
                  )}
                  {indicator.type === "candlestick" && (
                    <span className="bg-green-600 text-white text-xs px-1.5 py-0.5 rounded font-medium">
                      CHART
                    </span>
                  )}
                  {indicator.type === "volume" && (
                    <span className="bg-purple-600 text-white text-xs px-1.5 py-0.5 rounded font-medium">
                      VOL
                    </span>
                  )}
                </div>

                {/* Author */}
                <div className="col-span-3 flex items-center">
                  <span className="text-blue-400 text-sm hover:text-blue-300 transition-colors">
                    {indicator.author}
                  </span>
                </div>

                {/* Rating */}
                <div className="col-span-3 flex items-center justify-end">
                  <span className="text-gray-300 text-sm">
                    {indicator.rating}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {displayList.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <p>Keine Indikatoren gefunden</p>
              {activeSection === "Favoriten" && (
                <p className="text-sm mt-2">
                  Füge Indikatoren zu deinen Favoriten hinzu, um sie hier zu
                  sehen.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderDefaultSection = () => (
    <div className="flex-1 p-6 h-full overflow-y-auto">
      <h3 className="text-lg font-medium text-white mb-4">{activeSection}</h3>
      <p className="text-gray-400">
        Inhalte für {activeSection.toLowerCase()} sind noch nicht verfügbar.
      </p>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case "Favoriten":
      case "TechnischeDaten":
        return renderIndicatorsList();
      default:
        return renderDefaultSection();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-lg shadow-xl w-full max-w-6xl h-[700px] flex font-['Inter']">
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-lg font-medium text-white">
            Indikatoren, Metriken und Strategien
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-1 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex w-full mt-16 h-[calc(100%-4rem)]">
          {/* Sidebar */}
          <div className="w-64 bg-gray-700 border-r border-gray-600 flex-shrink-0">
            <div className="p-0">
              {sidebarItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full flex items-center px-4 py-3 text-left text-sm transition-colors border-b border-gray-600 last:border-b-0 ${
                    activeSection === item.id
                      ? "bg-blue-600 text-white"
                      : "text-gray-300 hover:bg-gray-600 hover:text-white"
                  }`}
                >
                  <span className="mr-3 text-base">{item.icon}</span>
                  {item.name}
                </button>
              ))}
            </div>
          </div>

          {/* Main Content */}
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default IndicatorsModal;