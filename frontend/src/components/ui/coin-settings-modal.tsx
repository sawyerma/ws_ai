import React, { useState, useEffect } from 'react';
import { X, Save, Calendar, Database, Zap, Clock, AlertCircle } from 'lucide-react';
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
      history_until: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
      favorite: false,
      db_resolution: 1, // 1 second
      chart_resolution: '1m',
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

  // Get all unique symbols/markets from settings
  const allSymbols = Array.from(new Set(settings.map(s => `${s.symbol}_${s.market}`)))
    .map(key => {
      const [symbol, market] = key.split('_');
      return { symbol, market };
    })
    .sort((a, b) => a.symbol.localeCompare(b.symbol));

  // Add current selected symbol if not in list
  if (selectedSymbol && !allSymbols.some(s => s.symbol === selectedSymbol && s.market === selectedMarket)) {
    allSymbols.unshift({ symbol: selectedSymbol, market: selectedMarket });
  }

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
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
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

          {/* Loading State */}
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading settings...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Quick Actions */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Quick Actions
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    onClick={() => {
                      allSymbols.forEach(({ symbol, market }) => {
                        updateSetting(symbol, market, { store_live: true });
                      });
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <Zap size={16} />
                    Enable Live for All
                  </button>
                  <button
                    onClick={() => {
                      allSymbols.forEach(({ symbol, market }) => {
                        updateSetting(symbol, market, { store_live: false });
                      });
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <X size={16} />
                    Disable Live for All
                  </button>
                  <button
                    onClick={() => {
                      allSymbols.forEach(({ symbol, market }) => {
                        updateSetting(symbol, market, { 
                          load_history: true,
                          history_until: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
                        });
                      });
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Database size={16} />
                    Load 7 Days History
                  </button>
                </div>
              </div>

              {/* Settings Table */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Symbol
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Market
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Live Data
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          History
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          History Until
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Resolution
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
                            <td className="px-6 py-4 whitespace-nowrap">
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
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="relative">
                                <Calendar size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                <input
                                  type="date"
                                  value={setting.history_until || ''}
                                  onChange={(e) => updateSetting(symbol, market, { history_until: e.target.value })}
                                  disabled={!setting.load_history}
                                  className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                                />
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <select
                                value={setting.chart_resolution}
                                onChange={(e) => updateSetting(symbol, market, { chart_resolution: e.target.value })}
                                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                              >
                                <option value="1s">1 Second</option>
                                <option value="5s">5 Seconds</option>
                                <option value="15s">15 Seconds</option>
                                <option value="30s">30 Seconds</option>
                                <option value="1m">1 Minute</option>
                                <option value="5m">5 Minutes</option>
                                <option value="15m">15 Minutes</option>
                                <option value="30m">30 Minutes</option>
                                <option value="1h">1 Hour</option>
                                <option value="4h">4 Hours</option>
                                <option value="1d">1 Day</option>
                              </select>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Rate Limiting Info */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Clock size={20} className="text-yellow-600 dark:text-yellow-400 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800 dark:text-yellow-200">
                      Rate Limiting Information
                    </h4>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                      Bitget API allows 15 requests per second for historical data. Large backfills may take time.
                      Live data uses WebSocket connections which have no rate limits.
                    </p>
                  </div>
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
