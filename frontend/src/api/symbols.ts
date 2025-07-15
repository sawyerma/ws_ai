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
const API_BASE = 'http://localhost:8100';
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

// Fallback mock data (only used if API fails)
const fallbackSymbols: ApiSymbol[] = [
  {
    symbol: "BTC/USDT",
    market: "spot",
    price: "104,911.62",
    change: "-3.56%",
    changePercent: -3.56,
  },
  {
    symbol: "ETH/USDT",
    market: "spot",
    price: "3,252.10",
    change: "+1.20%",
    changePercent: 1.2,
  },
  {
    symbol: "SOL/USDT",
    market: "spot",
    price: "134.51",
    change: "+0.30%",
    changePercent: 0.3,
  },
];

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

// Fetch symbols from backend
export async function fetchSymbols(): Promise<BackendSymbolsResponse> {
  const cached = getCached<BackendSymbolsResponse>('symbols');
  if (cached) return cached;
  
  try {
    const response = await fetch(`${API_BASE}/symbols`, {
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
    setCache('symbols', data, CACHE_TTL);
    
    console.log(`[SymbolsAPI] Fetched ${data.symbols?.length || 0} symbols from backend`);
    return data;
  } catch (error) {
    console.error('[SymbolsAPI] Failed to fetch symbols:', error);
    throw error;
  }
}

// Fetch tickers from backend
export async function fetchTickers(): Promise<BackendTicker[]> {
  const cached = getCached<BackendTicker[]>('tickers');
  if (cached) return cached;
  
  try {
    const response = await fetch(`${API_BASE}/ticker`, {
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
    setCache('tickers', data, TICKER_CACHE_TTL);
    
    console.log(`[SymbolsAPI] Fetched ${data.length} tickers from backend`);
    return data;
  } catch (error) {
    console.error('[SymbolsAPI] Failed to fetch tickers:', error);
    throw error;
  }
}

// Main function to get symbols with prices
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
    
    // Return fallback data
    console.warn('[SymbolsAPI] Using fallback data');
    return {
      symbols: fallbackSymbols,
    };
  }
}

// Settings API functions
export interface CoinSetting {
  symbol: string;
  market: string;
  store_live: boolean;
  load_history: boolean;
  history_until?: string;
  favorite: boolean;
  db_resolution: number;
  chart_resolution: string;
}

export async function getSettings(): Promise<CoinSetting[]> {
  try {
    const response = await fetch(`${API_BASE}/settings`, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[SymbolsAPI] Fetched ${data.length} settings from backend`);
    return data;
  } catch (error) {
    console.error('[SymbolsAPI] Failed to fetch settings:', error);
    return [];
  }
}

export async function saveSettings(settings: CoinSetting[]): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
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

// Clear cache function for manual refresh
export function clearCache(): void {
  cache.clear();
  console.log('[SymbolsAPI] Cache cleared');
}
