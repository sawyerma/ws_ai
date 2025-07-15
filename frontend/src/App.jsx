import { useState, useEffect } from "react";
import ChartView from "./components/ChartView";
import MarketTrades from "./components/MarketTrades";
import Orderbook from "./components/OrderBook";
import AdvancedCoinSelector from "./components/ui/advanced-coin-selector";
import CoinSettingsModal from "./components/ui/coin-settings-modal";
import { getSymbols } from "./api/symbols";

export default function App() {
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  const [selectedMarket, setSelectedMarket] = useState("spot");
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [symbols, setSymbols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load symbols on mount
  useEffect(() => {
    const loadSymbols = async () => {
      try {
        const response = await getSymbols();
        setSymbols(response.symbols);
        console.log(`[App] Loaded ${response.symbols.length} symbols`);
      } catch (err) {
        setError('Failed to load symbols');
        console.error('Error loading symbols:', err);
      } finally {
        setLoading(false);
      }
    };

    loadSymbols();
  }, []);

  // Handle symbol selection
  const handleSymbolSelect = (symbol, market) => {
    setSelectedSymbol(symbol);
    setSelectedMarket(market);
    console.log(`[App] Selected: ${symbol} (${market})`);
  };

  // Get current symbol data
  const currentSymbol = symbols.find(s => 
    s.symbol.replace('/', '') === selectedSymbol && s.market === selectedMarket
  );

  // Format display symbol
  const displaySymbol = selectedSymbol.includes('/') ? selectedSymbol : 
    currentSymbol?.symbol || selectedSymbol;

  return (
    <div className="min-h-screen bg-[#17181c] text-white">
      {/* Header */}
      <div className="bg-[#1e1f23] border-b border-gray-700 p-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">WS_KI Trading System</h1>
            
            {/* Symbol Selector */}
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">Symbol:</span>
              <AdvancedCoinSelector
                selectedSymbol={displaySymbol}
                onSymbolSelect={handleSymbolSelect}
                onSettingsClick={() => setSettingsModalOpen(true)}
              />
            </div>
          </div>

          {/* Market Info */}
          <div className="flex items-center gap-4">
            {currentSymbol && (
              <div className="flex items-center gap-2">
                <span className="text-gray-400 text-sm">Market:</span>
                <span className="text-blue-400 font-semibold">{selectedMarket.toUpperCase()}</span>
                <span className="text-gray-400 text-sm">Price:</span>
                <span className="text-green-400 font-semibold">{currentSymbol.price}</span>
                <span className={`text-sm font-medium ${
                  currentSymbol.changePercent >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {currentSymbol.change}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading symbols...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Chart Section */}
            <div className="mb-8">
              <div className="bg-[#1e1f23] rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">
                    {displaySymbol} - {selectedMarket.toUpperCase()}
                  </h2>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">Lightweight Charts</span>
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  </div>
                </div>
                
                <ChartView
                  wsUrl={`ws://localhost:8100/ws/${selectedSymbol}/${selectedMarket}`}
                  width={900}
                  height={480}
                  symbol={selectedSymbol}
                  market={selectedMarket}
                />
              </div>
            </div>

            {/* Trading Data Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-[#1e1f23] rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4">Market Trades</h3>
                <MarketTrades 
                  symbol={selectedSymbol} 
                  market={selectedMarket} 
                  wsBase="ws://localhost:8100" 
                />
              </div>

              <div className="bg-[#1e1f23] rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4">Orderbook</h3>
                <Orderbook 
                  symbol={selectedSymbol} 
                  market={selectedMarket} 
                  apiBase="http://localhost:8100" 
                />
              </div>
            </div>

            {/* Statistics Section */}
            <div className="mt-8 bg-[#1e1f23] rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-4">System Statistics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{symbols.length}</div>
                  <div className="text-sm text-gray-400">Available Symbols</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">
                    {symbols.filter(s => s.market === 'spot').length}
                  </div>
                  <div className="text-sm text-gray-400">Spot Markets</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">
                    {symbols.filter(s => s.market.includes('USDT')).length}
                  </div>
                  <div className="text-sm text-gray-400">USDT Futures</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">
                    {symbols.filter(s => s.market.includes('COIN')).length}
                  </div>
                  <div className="text-sm text-gray-400">Coin Futures</div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Settings Modal */}
      <CoinSettingsModal
        isOpen={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
        selectedSymbol={selectedSymbol}
        selectedMarket={selectedMarket}
      />
    </div>
  );
}
