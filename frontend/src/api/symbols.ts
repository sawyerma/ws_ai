// API endpoint for symbols data
export interface ApiSymbol {
  symbol: string;
  market: string;
  price: string;
  change: string;
  changePercent: number;
}

export interface ApiResponse {
  symbols: ApiSymbol[];
}

// Backend API interfaces
interface BackendSymbol {
  symbol: string;
  market_type: string;
  status: string;
  baseAsset: string;
  quoteAsset: string;
}

interface BackendTicker {
  symbol: string;
  last: number;
  high24h: number;
  low24h: number;
  changeRate: number;
  baseVol: number;
  quoteVol: number;
  market_type: string;
}

interface BackendSymbolsResponse {
  symbols: BackendSymbol[];
  db_symbols: any[];
}

// Configuration
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8100';
const CACHE_TTL = 300000; // 5 minutes for symbols
const TICKER_CACHE_TTL = 10000; // 10 seconds for tickers

// Cache storage
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

const cache = new Map<string, CacheEntry<any>>();

// Cache utilities
function getCached<T>(key: string): T | null {
  const entry = cache.get(key);
  if (!entry) return null;
  
  if (Date.now() - entry.timestamp > entry.ttl) {
    cache.delete(key);
    return null;
  }
  
  return entry.data;
}

function setCache<T>(key: string, data: T, ttl: number): void {
  cache.set(key, {
    data,
    timestamp: Date.now(),
    ttl,
  });
}


// Format symbol for display (BTCUSDT -> BTC/USDT)
function formatSymbol(symbol: string): string {
  // Handle futures symbols with underscores
  if (symbol.includes('_')) {
    return symbol.replace('_', '/').toUpperCase();
  }
  
  // Handle spot symbols (BTCUSDT -> BTC/USDT)
  if (symbol.endsWith('USDT')) {
    const base = symbol.slice(0, -4);
    return `${base}/USDT`;
  }
  
  if (symbol.endsWith('USDC')) {
    const base = symbol.slice(0, -4);
    return `${base}/USDC`;
  }
  
  if (symbol.endsWith('BTC')) {
    const base = symbol.slice(0, -3);
    return `${base}/BTC`;
  }
  
  return symbol;
}

// Format market type for display
function formatMarketType(marketType: string): string {
  const marketMap: { [key: string]: string } = {
    'spot': 'spot',
    'usdtm': 'USDT-M',
    'coinm': 'COIN-M',
    'usdcm': 'USDC-M',
    'USDT-FUTURES': 'USDT-M',
    'COIN-FUTURES': 'COIN-M',
    'USDC-FUTURES': 'USDC-M',
  };
  
  return marketMap[marketType] || marketType;
}

// Format price for display
function formatPrice(price: number): string {
  if (price === 0) return '0.00';
  
  if (price < 1) {
    return price.toFixed(6);
  } else if (price < 100) {
    return price.toFixed(4);
  } else if (price < 1000) {
    return price.toFixed(2);
  } else {
    return price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
}

// Format change percentage
function formatChangePercent(changeRate: number): { change: string; changePercent: number } {
  const changePercent = changeRate * 100;
  const sign = changePercent >= 0 ? '+' : '';
  return {
    change: `${sign}${changePercent.toFixed(2)}%`,
    changePercent: changePercent,
  };
}

// Exchange configuration
export type Exchange = 'binance' | 'bitget';
export const DEFAULT_EXCHANGE: Exchange = 'bitget'; // Legacy compatibility

// Fetch symbols from backend with exchange support
export async function fetchSymbols(exchange: Exchange = DEFAULT_EXCHANGE): Promise<BackendSymbolsResponse> {
  const cacheKey = `symbols_${exchange}`;
  const cached = getCached<BackendSymbolsResponse>(cacheKey);
  if (cached) return cached;
  
  try {
    const response = await fetch(`${API_BASE}/symbols?exchange=${exchange}`, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    } as any);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    setCache(cacheKey, data, CACHE_TTL);
    
    console.log(`[SymbolsAPI] Fetched ${data.symbols?.length || 0} symbols from ${exchange}`);
    return data;
  } catch (error) {
    console.error(`[SymbolsAPI] Failed to fetch symbols from ${exchange}:`, error);
    throw error;
  }
}

// Fetch symbols from all exchanges
export async function fetchAllSymbols(): Promise<BackendSymbolsResponse> {
  const cacheKey = 'symbols_all';
  const cached = getCached<BackendSymbolsResponse>(cacheKey);
  if (cached) return cached;
  
  try {
    const [binanceData, bitgetData] = await Promise.all([
      fetchSymbols('binance').catch(() => ({ symbols: [], db_symbols: [] })),
      fetchSymbols('bitget').catch(() => ({ symbols: [], db_symbols: [] }))
    ]);
    
    const combinedData: BackendSymbolsResponse = {
      symbols: [
        ...binanceData.symbols.map(s => ({ ...s, exchange: 'binance' })), 
        ...bitgetData.symbols.map(s => ({ ...s, exchange: 'bitget' }))
      ],
      db_symbols: [...binanceData.db_symbols, ...bitgetData.db_symbols]
    };
    
    setCache(cacheKey, combinedData, CACHE_TTL);
    console.log(`[SymbolsAPI] Combined ${combinedData.symbols.length} symbols from all exchanges`);
    return combinedData;
  } catch (error) {
    console.error('[SymbolsAPI] Failed to fetch symbols from all exchanges:', error);
    throw error;
  }
}

// Fetch tickers from backend with exchange support
export async function fetchTickers(exchange: Exchange = DEFAULT_EXCHANGE): Promise<BackendTicker[]> {
  const cacheKey = `tickers_${exchange}`;
  const cached = getCached<BackendTicker[]>(cacheKey);
  if (cached) return cached;
  
  try {
    const response = await fetch(`${API_BASE}/ticker?exchange=${exchange}`, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    } as any);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    // Handle new unified backend response format
    const tickers = data.tickers || data; // Support both old and new format
    setCache(cacheKey, tickers, TICKER_CACHE_TTL);
    
    console.log(`[SymbolsAPI] Fetched ${tickers.length} tickers from ${exchange}`);
    return tickers;
  } catch (error) {
    console.error(`[SymbolsAPI] Failed to fetch tickers from ${exchange}:`, error);
    throw error;
  }
}

// Fetch tickers from all exchanges
export async function fetchAllTickers(): Promise<BackendTicker[]> {
  const cacheKey = 'tickers_all';
  const cached = getCached<BackendTicker[]>(cacheKey);
  if (cached) return cached;
  
  try {
    const [binanceTickers, bitgetTickers] = await Promise.all([
      fetchTickers('binance').catch(() => []),
      fetchTickers('bitget').catch(() => [])
    ]);
    
    const allTickers = [
      ...binanceTickers.map(t => ({ ...t, exchange: 'binance' })),
      ...bitgetTickers.map(t => ({ ...t, exchange: 'bitget' }))
    ];
    
    setCache(cacheKey, allTickers, TICKER_CACHE_TTL);
    console.log(`[SymbolsAPI] Combined ${allTickers.length} tickers from all exchanges`);
    return allTickers;
  } catch (error) {
    console.error('[SymbolsAPI] Failed to fetch tickers from all exchanges:', error);
    throw error;
  }
}

// Main function to get symbols with price
export async function getSymbols(): Promise<ApiResponse> {
  try {
    // Fetch both symbols and tickers in parallel
    const [symbolsData, tickersData] = await Promise.all([
      fetchSymbols(),
      fetchTickers(),
    ]);
    
    // Create ticker lookup map
    const tickerMap = new Map<string, BackendTicker>();
    tickersData.forEach(ticker => {
      const key = `${ticker.symbol}_${ticker.market_type}`;
      tickerMap.set(key, ticker);
    });
    
    // Transform backend data to frontend format
    const symbols: ApiSymbol[] = symbolsData.symbols.map(symbol => {
      const tickerKey = `${symbol.symbol}_${symbol.market_type}`;
      const ticker = tickerMap.get(tickerKey);
      
      const { change, changePercent } = ticker 
        ? formatChangePercent(ticker.changeRate)
        : { change: '0.00%', changePercent: 0 };
      
      return {
        symbol: formatSymbol(symbol.symbol),
        market: formatMarketType(symbol.market_type),
        price: ticker ? formatPrice(ticker.last) : '0.00',
        change,
        changePercent,
      };
    });
    
    console.log(`[SymbolsAPI] Processed ${symbols.length} symbols with ticker data`);
    
    return {
      symbols: symbols.sort((a, b) => {
        // Sort by market type (spot first), then by symbol
        if (a.market !== b.market) {
          if (a.market === 'spot') return -1;
          if (b.market === 'spot') return 1;
          return a.market.localeCompare(b.market);
        }
        return a.symbol.localeCompare(b.symbol);
      }),
    };
    
  } catch (error) {
    console.error('[SymbolsAPI] Error in getSymbols:', error);
    
    // No fallback data - return empty array (live data only)
    return {
      symbols: [],
    };
  }
}

// Settings API functions
export interface CoinSetting {
  exchange?: string;  // New: Exchange parameter
  symbol: string;
  market: string;
  store_live: boolean;
  load_history: boolean;
  history_until?: string;
  favorite: boolean;
  db_resolutions: number[];  // Updated: Now array instead of single value
  chart_resolution: string;
}

// Fetch settings with exchange support
export async function getSettings(exchange?: Exchange, symbol?: string, market?: string): Promise<CoinSetting[]> {
  try {
    const params = new URLSearchParams();
    if (exchange) params.append('exchange', exchange);
    if (symbol) params.append('symbol', symbol);
    if (market) params.append('market', market);
    
    const queryString = params.toString();
    const url = `${API_BASE}/settings${queryString ? `?${queryString}` : ''}`;
    
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[SymbolsAPI] Fetched ${data.length} settings from backend (exchange: ${exchange || 'all'})`);
    return data;
  } catch (error) {
    console.error('[SymbolsAPI] Failed to fetch settings:', error);
    return [];
  }
}

// Get settings for all exchanges
export async function getAllSettings(): Promise<CoinSetting[]> {
  try {
    const [binanceSettings, bitgetSettings] = await Promise.all([
      getSettings('binance').catch(() => []),
      getSettings('bitget').catch(() => [])
    ]);
    
    const allSettings = [...binanceSettings, ...bitgetSettings];
    console.log(`[SymbolsAPI] Combined ${allSettings.length} settings from all exchanges`);
    return allSettings;
  } catch (error) {
    console.error('[SymbolsAPI] Failed to fetch settings from all exchanges:', error);
    return [];
  }
}

// Save settings with exchange support
export async function saveSettings(settings: CoinSetting[]): Promise<boolean> {
  try {
    // Ensure each setting has an exchange field (default to bitget for legacy compatibility)
    const settingsWithExchange = settings.map(setting => ({
      ...setting,
      exchange: setting.exchange || DEFAULT_EXCHANGE,
      // Convert single db_resolution to array for backward compatibility
      db_resolutions: Array.isArray(setting.db_resolutions) 
        ? setting.db_resolutions 
        : [(setting as any).db_resolution || 60]
    }));
    
    const response = await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settingsWithExchange),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log('[SymbolsAPI] Settings saved successfully:', result);
    return true;
  } catch (error) {
    console.error('[SymbolsAPI] Failed to save settings:', error);
    return false;
  }
}

// Exchange-specific settings functions
export async function getBinanceSettings(): Promise<CoinSetting[]> {
  return getSettings('binance');
}

export async function getBitgetSettings(): Promise<CoinSetting[]> {
  return getSettings('bitget');
}

// Clear cache function for manual refresh
export function clearCache(): void {
  cache.clear();
  console.log('[SymbolsAPI] Cache cleared');
}
