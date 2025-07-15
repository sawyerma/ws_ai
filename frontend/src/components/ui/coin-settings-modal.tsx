import React, { useState, useEffect } from 'react';
import { X, Save, Calendar, Clock, AlertCircle } from 'lucide-react';
import { CoinSetting, getSettings, saveSettings } from '../../api/symbols';

interface CoinSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedSymbol?: string;
  selectedMarket?: string;
}

const CoinSettingsModal: React.FC<CoinSettingsModalProps> = ({
  isOpen,
  onClose,
  selectedSymbol,
  selectedMarket = 'spot',
}) => {
  const [settings, setSettings] = useState<CoinSetting[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimit, setRateLimit] = useState<number>(15);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load settings from backend
  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getSettings();
      setSettings(data);
    } catch (err) {
      setError('Failed to load settings');
      console.error('Error loading settings:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load settings when modal opens
  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  // Clear messages after delay
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  // Get current setting for symbol/market
  const getCurrentSetting = (symbol: string, market: string): CoinSetting => {
    const existing = settings.find(s => s.symbol === symbol && s.market === market);
    return existing || {
      symbol,
      market,
      store_live: false,
      load_history: false,
      history_until: '',
      favorite: false
    };
  };

  // Update setting
  const updateSetting = (symbol: string, market: string, updates: Partial<CoinSetting>) => {
    setSettings(prev => {
      const existingIndex = prev.findIndex(s => s.symbol === symbol && s.market === market);
      const newSetting = { ...getCurrentSetting(symbol, market), ...updates };
      
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = newSetting;
        return updated;
      } else {
        return [...prev, newSetting];
      }
    });
  };

  // Save settings to backend
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      const success = await saveSettings(settings);
      if (success) {
        setSuccessMessage('Settings saved successfully!');
      } else {
        setError('Failed to save settings');
      }
    } catch (err) {
      setError('Failed to save settings');
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  // Check if a symbol is favorited in the coin selector
  useEffect(() => {
    if (isOpen) {
      // Get favorites from localStorage
      const savedFavorites = localStorage.getItem('coin-favorites');
      if (savedFavorites) {
        try {
          const favSymbols = JSON.parse(savedFavorites);
          
          // Add favorited symbols to settings if they don't exist
          const newSettings = [...settings];
          let hasChanges = false;
          
          favSymbols.forEach((symbol: string) => {
            // Extract market from symbol format (e.g., "BTC/USDT" -> "spot")
            // This is a simplification - you might need more logic based on your symbol format
            const market = symbol.includes('/USDT') ? 'spot' : 
                          symbol.includes('/USD') ? 'coin-m-perp' : 'spot';
            
            // Check if this symbol/market combo already exists in settings
            const exists = settings.some(s => s.symbol === symbol && s.market === market);
            
            if (!exists) {
              newSettings.push({
                symbol,
                market,
                store_live: false,
                load_history: false,
                favorite: true,
                chart_resolution: '1m',
              });
              hasChanges = true;
            }
          });
          
          if (hasChanges) {
            setSettings(newSettings);
          }
        } catch (err) {
          console.error('Error processing favorites:', err);
        }
      }
    }
  }, [isOpen, settings]);

  // Get all unique symbols/markets from settings
  const allSymbols = Array.from(new Set(settings.map(s => `${s.symbol}_${s.market}`)))
    .map(key => {
      const parts = key.split('_');
      const market = parts.pop() || '';
      const symbol = parts.join('_');
      return { symbol, market };
    })
    .sort((a, b) => a.symbol.localeCompare(b.symbol));

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Coin Settings
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-150px)]">
          {/* Error/Success Messages */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
                <AlertCircle size={16} />
                {error}
              </div>
            </div>
          )}

          {successMessage && (
            <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-center gap-2 text-green-800 dark:text-green-200">
                <Save size={16} />
                {successMessage}
              </div>
            </div>
          )}

          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading settings...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Quick Actions */}
              {/* Settings Table */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          COIN
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Market
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          LIVE
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          HISTORIC
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          UNTIL
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {allSymbols.map(({ symbol, market }) => {
                        const setting = getCurrentSetting(symbol, market);
                        return (
                          <tr key={`${symbol}_${market}`} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-sm font-medium text-gray-900 dark:text-white">
                                  {symbol}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-600 text-gray-800 dark:text-gray-200">
                                {market}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                  type="checkbox"
                                  className="sr-only peer"
                                  checked={setting.store_live}
                                  onChange={(e) => updateSetting(symbol, market, { store_live: e.target.checked })}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                              </label>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                  type="checkbox"
                                  className="sr-only peer"
                                  checked={setting.load_history}
                                  onChange={(e) => updateSetting(symbol, market, { load_history: e.target.checked })}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                              </label>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <div className="relative">
                                <Calendar size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                <input
                                  type="date"
                                  value={setting.history_until || ''}
                                  onChange={(e) => {
                                    updateSetting(symbol, market, { 
                                      history_until: e.target.value 
                                    });
                                  }}
                                  disabled={!setting.load_history}
                                  className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm w-full disabled:opacity-50 disabled:cursor-not-allowed"
                                />
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Rate Limiting Info */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-2 mt-4">
                <div className="flex items-center gap-2">
                  <Clock size={12} className="text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
                  <span className="text-xs text-yellow-700 dark:text-yellow-300 whitespace-nowrap">
                    API requests per second:
                  </span>
                  <input
                    type="number"
                    value={rateLimit}
                    onChange={(e) => setRateLimit(parseInt(e.target.value) || 15)}
                    min="1"
                    max="100"
                    className="w-14 px-2 py-0.5 text-xs border border-yellow-300 dark:border-yellow-600 rounded bg-white dark:bg-gray-700 text-yellow-800 dark:text-yellow-200"
                  />
                  <span className="text-xs text-yellow-700 dark:text-yellow-300 ml-1">
                    Large backfills may take time. Live data uses WebSocket connections which have no rate limits.
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {settings.length} symbols configured
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <Save size={16} />
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoinSettingsModal;