import React, { useState, useEffect, useMemo } from 'react';
import { Search, RefreshCw, Settings } from 'lucide-react';
import { getSymbols, ApiSymbol, clearCache } from '../../api/symbols';

interface AdvancedCoinSelectorProps {
  selectedSymbol: string;
  onSymbolSelect: (symbol: string, market: string) => void;
  onSettingsClick?: () => void;
  maxHeight?: number;
}

const AdvancedCoinSelector: React.FC<AdvancedCoinSelectorProps> = ({
  selectedSymbol,
  onSymbolSelect,
  onSettingsClick,
  maxHeight = 500,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [symbols, setSymbols] = useState<ApiSymbol[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  // Load favorites from localStorage
  useEffect(() => {
    const savedFavorites = localStorage.getItem('coin-favorites');
    if (savedFavorites) {
      try {
        const favArray = JSON.parse(savedFavorites);
        setFavorites(new Set(favArray));
      } catch (error) {
        console.error('Error loading favorites:', error);
      }
    }
  }, []);

  // Save favorites to localStorage
  const saveFavorites = (newFavorites: Set<string>) => {
    localStorage.setItem('coin-favorites', JSON.stringify(Array.from(newFavorites)));
    setFavorites(newFavorites);
  };

  // Load symbols from API
  const loadSymbols = async (forceRefresh = false) => {
    if (forceRefresh) {
      clearCache();
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getSymbols();
      setSymbols(response.symbols);
      console.log(`[CoinSelector] Loaded ${response.symbols.length} symbols`);
    } catch (err) {
      setError('Failed to load symbols');
      console.error('Error loading symbols:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load symbols on mount
  useEffect(() => {
    loadSymbols();
  }, []);

  // Filter and sort symbols
  const filteredSymbols = useMemo(() => {
    let filtered = symbols;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(symbol =>
        symbol.symbol.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Sort symbols
    filtered.sort((a, b) => {
      // Favorites first
      const aFav = favorites.has(a.symbol);
      const bFav = favorites.has(b.symbol);
      if (aFav && !bFav) return -1;
      if (!aFav && bFav) return 1;

      // Then by symbol name
      return a.symbol.localeCompare(b.symbol);
    });

    return filtered;
  }, [symbols, searchTerm, favorites]);

  // Toggle favorite
  const toggleFavorite = (symbol: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newFavorites = new Set(favorites);
    if (newFavorites.has(symbol)) {
      newFavorites.delete(symbol);
    } else {
      newFavorites.add(symbol);
    }
    saveFavorites(newFavorites);
  };

  // Handle symbol selection
  const handleSymbolSelect = (symbol: ApiSymbol) => {
    const cleanSymbol = symbol.symbol.replace('/', '');
    onSymbolSelect(cleanSymbol, symbol.market);
    setIsOpen(false);
  };

  // Get display symbol for current selection
  const displaySymbol = selectedSymbol.includes('/') ? selectedSymbol : 
    symbols.find(s => s.symbol.replace('/', '') === selectedSymbol)?.symbol || selectedSymbol;

  return (
    <div className="relative">
      {/* Selected Symbol Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between px-3 py-2 bg-[#111827] dark:bg-[#111827] border border-gray-700 dark:border-gray-700 rounded-lg hover:bg-gray-800 dark:hover:bg-gray-800 transition-colors min-w-[150px]"
      >
        <span className="font-bold text-white dark:text-white text-sm">
          {displaySymbol}
        </span>
        <svg
          className={`w-3 h-3 ml-auto transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-[#1e2433] dark:bg-[#1e2433] border border-gray-700 dark:border-gray-700 rounded-lg shadow-lg z-50 overflow-hidden w-[377px]">
          {/* Search */}
          <div className="p-2 border-b border-gray-700">
            <div className="relative">
              <Search size={12} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search symbols"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs border border-gray-600 rounded-lg bg-[#111827] text-white placeholder-gray-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Header Row */}
          <div className="flex items-center px-3 py-2 bg-[#1e2433] border-b border-gray-700 text-gray-400 text-xs">
            <div className="flex items-center w-[130px]">
              <span className="text-yellow-500 mr-2 text-xs">★</span>
              <span className="text-xs">COIN</span>
              <span className="ml-1">↑</span>
            </div>
            <div className="w-[110px] text-right text-xs">PRICE</div>
            <div className="w-[90px] text-right text-xs">24H</div>
            <div className="w-[35px] text-center text-xs">L</div>
            <div className="w-[12px] text-center text-xs">H</div>
          </div>

          {/* Coins list */}
          <div className="max-h-[300px] overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-gray-400">
                <RefreshCw size={12} className="animate-spin mx-auto mb-2" />
                <span className="text-xs">Loading...</span>
              </div>
            ) : filteredSymbols.length > 0 ? (
              filteredSymbols.map((coin) => (
                <div
                  key={`${coin.symbol}_${coin.market}`}
                  className={`flex items-center px-3 py-2 cursor-pointer transition-colors border-b border-gray-700 ${
                    coin.symbol === displaySymbol
                      ? "bg-[#1a2035]"
                      : "hover:bg-[#1a2035]"
                  }`}
                  onClick={() => handleSymbolSelect(coin)}
                >
                  <div className="flex items-center w-[130px]">
                    <span
                      className={`text-sm mr-2 ${
                        favorites.has(coin.symbol) ? "text-yellow-500" : "text-gray-600"
                      }`}
                      onClick={(e) => toggleFavorite(coin.symbol, e)}
                    >
                      ★
                    </span>
                    <span className="font-bold text-white text-sm">{coin.symbol}</span>
                  </div>
                  <div className="w-[110px] text-right font-mono text-white text-sm">
                    {coin.price}
                  </div>
                  <div
                    className={`w-[90px] text-right font-bold text-sm ${
                      (coin.changePercent || 0) >= 0 ? "text-green-500" : "text-red-500"
                    }`}
                  >
                    {coin.change}
                  </div>
                  <div className="w-[35px] text-center">
                    <span
                      className="inline-block w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: "rgb(34, 197, 94)"
                      }}
                    ></span>
                  </div>
                  <div className="w-[12px] text-center">
                    <span
                      className="inline-block w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: coin.market === "spot" ? "rgb(34, 197, 94)" : "rgb(239, 68, 68)"
                      }}
                    ></span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-gray-400">
                <span className="text-xs">No symbols found</span>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-1.5 border-t border-gray-700 text-xs text-gray-400 flex justify-between items-center">
            <div>
              <span className="text-[10px]">{filteredSymbols.length} symbols</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => loadSymbols(true)}
                disabled={loading}
                className="p-0.5 text-gray-400 hover:text-white disabled:opacity-50"
                title="Refresh symbols"
              >
                <RefreshCw size={10} className={loading ? 'animate-spin' : ''} />
              </button>
              {onSettingsClick && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSettingsClick();
                    setIsOpen(false);
                  }}
                  className="p-0.5 text-gray-400 hover:text-white"
                  title="Settings"
                >
                  <Settings size={10} />
                </button>
              )}
            </div>
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

export default AdvancedCoinSelector;