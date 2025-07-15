import React, { useState, useEffect, useMemo } from 'react';
import { Search, Star, TrendingUp, TrendingDown, RefreshCw, Settings } from 'lucide-react';
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
  const [selectedMarket, setSelectedMarket] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'symbol' | 'change' | 'volume'>('symbol');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
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

  // Get available markets
  const availableMarkets = useMemo(() => {
    const markets = new Set(symbols.map(s => s.market).filter(Boolean));
    return ['all', ...Array.from(markets).sort()];
  }, [symbols]);

  // Filter and sort symbols
  const filteredSymbols = useMemo(() => {
    let filtered = symbols;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(symbol =>
        symbol.symbol.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by market
    if (selectedMarket !== 'all') {
      filtered = filtered.filter(symbol => symbol.market === selectedMarket);
    }

    // Sort symbols
    filtered.sort((a, b) => {
      // Favorites first
      const aFav = favorites.has(a.symbol);
      const bFav = favorites.has(b.symbol);
      if (aFav && !bFav) return -1;
      if (!aFav && bFav) return 1;

      // Then by selected sort
      let comparison = 0;
      switch (sortBy) {
        case 'symbol':
          comparison = a.symbol.localeCompare(b.symbol);
          break;
        case 'change':
          comparison = a.changePercent - b.changePercent;
          break;
        default:
          comparison = a.symbol.localeCompare(b.symbol);
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [symbols, searchTerm, selectedMarket, sortBy, sortOrder, favorites]);

  // Toggle favorite
  const toggleFavorite = (symbol: string) => {
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
        className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors min-w-[200px]"
      >
        <span className="font-medium text-gray-900 dark:text-white">
          {displaySymbol}
        </span>
        {favorites.has(displaySymbol) && (
          <Star size={16} className="text-yellow-500 fill-current" />
        )}
        <svg
          className={`w-4 h-4 ml-auto transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-50">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Select Symbol
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => loadSymbols(true)}
                  disabled={loading}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
                  title="Refresh symbols"
                >
                  <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                </button>
                {onSettingsClick && (
                  <button
                    onClick={onSettingsClick}
                    className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    title="Settings"
                  >
                    <Settings size={16} />
                  </button>
                )}
              </div>
            </div>

            {/* Search */}
            <div className="relative mb-3">
              <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search symbols..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Filters */}
            <div className="flex items-center gap-3 text-sm">
              <select
                value={selectedMarket}
                onChange={(e) => setSelectedMarket(e.target.value)}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {availableMarkets.map(market => (
                  <option key={market} value={market}>
                    {market === 'all' ? 'All Markets' : (market || '').toUpperCase()}
                  </option>
                ))}
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="symbol">Symbol</option>
                <option value="change">Change</option>
              </select>

              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>

          {/* Error State */}
          {error && (
            <div className="p-4 text-red-600 dark:text-red-400 text-sm">
              {error}
              <button
                onClick={() => loadSymbols(true)}
                className="ml-2 underline hover:no-underline"
              >
                Retry
              </button>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="p-4 text-gray-500 dark:text-gray-400 text-sm flex items-center gap-2">
              <RefreshCw size={16} className="animate-spin" />
              Loading symbols...
            </div>
          )}

          {/* Symbol List */}
          {!loading && !error && (
            <div className="max-h-96 overflow-y-auto">
              {filteredSymbols.length === 0 ? (
                <div className="p-4 text-gray-500 dark:text-gray-400 text-sm text-center">
                  No symbols found
                </div>
              ) : (
                <div className="p-2">
                  {filteredSymbols.map((symbol) => (
                    <div
                      key={`${symbol.symbol}_${symbol.market}`}
                      className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer group"
                      onClick={() => handleSymbolSelect(symbol)}
                    >
                      <div className="flex items-center gap-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorite(symbol.symbol);
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Star
                            size={16}
                            className={`${
                              favorites.has(symbol.symbol)
                                ? 'text-yellow-500 fill-current'
                                : 'text-gray-400 hover:text-yellow-500'
                            }`}
                          />
                        </button>

                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 dark:text-white">
                              {symbol.symbol}
                            </span>
                            <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded">
                              {symbol.market}
                            </span>
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            ${symbol.price}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className={`text-sm font-medium ${
                          symbol.changePercent >= 0 
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}>
                          {symbol.changePercent >= 0 ? (
                            <TrendingUp size={14} className="inline mr-1" />
                          ) : (
                            <TrendingDown size={14} className="inline mr-1" />
                          )}
                          {symbol.change}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
            {filteredSymbols.length} symbols • Updated every 10 seconds
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedCoinSelector;
