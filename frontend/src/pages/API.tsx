import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Check, X, Eye, EyeOff, AlertCircle } from "lucide-react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";

interface APIProps {
  onBackToTrading?: () => void;
}

interface APIKeyConfig {
  name: string;
  key: string;
  url: string;
  description: string;
  registerUrl: string;
  status: "connected" | "error" | "pending" | "not_configured";
  lastChecked?: string;
}

const API = ({ onBackToTrading }: APIProps = {}) => {
  const [apiKeys, setApiKeys] = useState<Record<string, APIKeyConfig>>({
    etherscan: {
      name: "Etherscan",
      key: "",
      url: "https://api.etherscan.io/api",
      description: "Ethereum blockchain data for whale monitoring",
      registerUrl: "https://etherscan.io/apis",
      status: "not_configured"
    },
    bscscan: {
      name: "BSCScan",
      key: "",
      url: "https://api.bscscan.com/api",
      description: "Binance Smart Chain data for whale monitoring",
      registerUrl: "https://bscscan.com/apis",
      status: "not_configured"
    },
    polygonscan: {
      name: "PolygonScan",
      key: "",
      url: "https://api.polygonscan.com/api", 
      description: "Polygon blockchain data for whale monitoring",
      registerUrl: "https://polygonscan.com/apis",
      status: "not_configured"
    },
    coingecko: {
      name: "CoinGecko",
      key: "",
      url: "https://api.coingecko.com/api/v3",
      description: "Cryptocurrency price data and market information",
      registerUrl: "https://www.coingecko.com/en/api",
      status: "not_configured"
    }
  });

  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // API Base URL
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Load saved API keys on component mount
  useEffect(() => {
    loadAPIKeys();
  }, []);

  const loadAPIKeys = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/settings/api-keys`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setApiKeys(prev => {
          const updated = { ...prev };
          Object.keys(data.keys || {}).forEach(provider => {
            if (updated[provider]) {
              updated[provider].key = data.keys[provider];
              updated[provider].status = data.keys[provider] ? "connected" : "not_configured";
              updated[provider].lastChecked = data.lastChecked?.[provider];
            }
          });
          return updated;
        });
      }
    } catch (error) {
      console.error('Failed to load API keys:', error);
    }
  };

  const handleKeyChange = (provider: string, value: string) => {
    setApiKeys(prev => ({
      ...prev,
      [provider]: {
        ...prev[provider],
        key: value,
        status: value ? "pending" : "not_configured"
      }
    }));
  };

  const toggleKeyVisibility = (provider: string) => {
    setShowKeys(prev => ({
      ...prev,
      [provider]: !prev[provider]
    }));
  };

  const validateAPIKey = async (provider: string) => {
    const config = apiKeys[provider];
    if (!config.key.trim()) return;

    setLoading(prev => ({ ...prev, [provider]: true }));

    try {
      const response = await fetch(`${API_BASE}/api/settings/validate-api-key`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider,
          apiKey: config.key
        })
      });

      const data = await response.json();
      
      setApiKeys(prev => ({
        ...prev,
        [provider]: {
          ...prev[provider],
          status: data.valid ? "connected" : "error",
          lastChecked: new Date().toISOString()
        }
      }));

    } catch (error) {
      console.error(`Validation failed for ${provider}:`, error);
      setApiKeys(prev => ({
        ...prev,
        [provider]: {
          ...prev[provider],
          status: "error",
          lastChecked: new Date().toISOString()
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [provider]: false }));
    }
  };

  const saveAllKeys = async () => {
    setLoading(prev => ({ ...prev, save: true }));
    setSaveStatus(null);

    try {
      const keysToSave = Object.fromEntries(
        Object.entries(apiKeys).map(([provider, config]) => [provider, config.key])
      );

      const response = await fetch(`${API_BASE}/api/settings/api-keys`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ keys: keysToSave })
      });

      if (response.ok) {
        setSaveStatus("success");
        // Validate all non-empty keys
        Object.keys(apiKeys).forEach(provider => {
          if (apiKeys[provider].key.trim()) {
            validateAPIKey(provider);
          }
        });
      } else {
        setSaveStatus("error");
      }
    } catch (error) {
      console.error('Failed to save API keys:', error);
      setSaveStatus("error");
    } finally {
      setLoading(prev => ({ ...prev, save: false }));
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected": return "bg-green-500";
      case "error": return "bg-red-500";
      case "pending": return "bg-yellow-500";
      default: return "bg-gray-500";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "connected": return "Connected";
      case "error": return "Error";
      case "pending": return "Pending";
      default: return "Not Configured";
    }
  };

  return (
    <ThemeProvider>
      <div className="bg-gray-900 text-white min-h-screen font-['Inter']">
        {/* Header */}
        <div className="border-b border-gray-700">
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              {onBackToTrading && (
                <button
                  onClick={onBackToTrading}
                  className="px-3 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
                >
                  ← Back to Trading
                </button>
              )}
              <h1 className="text-2xl font-bold">API Configuration</h1>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
            </div>
          </div>
        </div>

        <div className="p-6">
          {/* Header Section */}
          <div className="mb-8">
            <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="text-blue-400 mt-1" size={20} />
                <div>
                  <h3 className="text-blue-400 font-semibold mb-2">Whale Monitoring API Keys Required</h3>
                  <p className="text-gray-300 text-sm">
                    To collect whale transaction data, you need to register for free API keys from blockchain explorers. 
                    These keys allow the system to access real-time blockchain data for whale detection.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold">Blockchain API Keys</h2>
                <p className="text-gray-400 text-sm">Configure your API keys for whale data collection</p>
              </div>
              <Button 
                onClick={saveAllKeys}
                disabled={loading.save}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading.save ? "Saving..." : "Save All Keys"}
              </Button>
            </div>

            {/* Save Status */}
            {saveStatus && (
              <div className={`mb-4 p-3 rounded-lg border ${
                saveStatus === "success" 
                  ? "bg-green-900/20 border-green-800 text-green-400" 
                  : "bg-red-900/20 border-red-800 text-red-400"
              }`}>
                <div className="flex items-center gap-2">
                  {saveStatus === "success" ? <Check size={16} /> : <X size={16} />}
                  {saveStatus === "success" ? "API keys saved successfully!" : "Failed to save API keys. Please try again."}
                </div>
              </div>
            )}
          </div>

          {/* API Keys Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Object.entries(apiKeys).map(([provider, config]) => (
              <Card key={provider} className="bg-gray-800 border-gray-700">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-700 rounded-lg flex items-center justify-center">
                        <span className="text-lg font-bold">{config.name[0]}</span>
                      </div>
                      <div>
                        <CardTitle className="text-white">{config.name}</CardTitle>
                        <CardDescription className="text-gray-400">
                          {config.description}
                        </CardDescription>
                      </div>
                    </div>
                    <Badge 
                      variant="secondary" 
                      className={`${getStatusColor(config.status)} text-white`}
                    >
                      {getStatusText(config.status)}
                    </Badge>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  {/* API Key Input */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                      API Key
                    </label>
                    <div className="relative">
                      <Input
                        type={showKeys[provider] ? "text" : "password"}
                        value={config.key}
                        onChange={(e) => handleKeyChange(provider, e.target.value)}
                        placeholder={`Enter your ${config.name} API key`}
                        className="bg-gray-700 border-gray-600 text-white pr-20"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                        <button
                          onClick={() => toggleKeyVisibility(provider)}
                          className="p-1 text-gray-400 hover:text-white transition-colors"
                        >
                          {showKeys[provider] ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                        <button
                          onClick={() => validateAPIKey(provider)}
                          disabled={!config.key.trim() || loading[provider]}
                          className="p-1 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                        >
                          {loading[provider] ? (
                            <div className="w-4 h-4 border-2 border-gray-400 border-t-white rounded-full animate-spin" />
                          ) : (
                            <Check size={16} />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* API URL */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                      API Endpoint
                    </label>
                    <div className="text-sm text-gray-400 bg-gray-700/50 p-2 rounded font-mono">
                      {config.url}
                    </div>
                  </div>

                  {/* Last Checked */}
                  {config.lastChecked && (
                    <div className="text-xs text-gray-500">
                      Last checked: {new Date(config.lastChecked).toLocaleString()}
                    </div>
                  )}

                  {/* Register Link */}
                  <div className="pt-2 border-t border-gray-700">
                    <a 
                      href={config.registerUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors text-sm"
                    >
                      <ExternalLink size={14} />
                      Get API Key from {config.name}
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Instructions Section */}
          <div className="mt-8">
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Setup Instructions</CardTitle>
                <CardDescription className="text-gray-400">
                  Follow these steps to configure your API keys
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <h4 className="font-semibold text-white">Step 1: Register for API Keys</h4>
                    <ul className="space-y-2 text-sm text-gray-300">
                      <li>• Visit each provider's registration page</li>
                      <li>• Create a free account</li>
                      <li>• Generate an API key in your dashboard</li>
                      <li>• Copy the API key securely</li>
                    </ul>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-semibold text-white">Step 2: Configure & Test</h4>
                    <ul className="space-y-2 text-sm text-gray-300">
                      <li>• Paste your API keys above</li>
                      <li>• Click the validate button (✓) to test</li>
                      <li>• Ensure all keys show "Connected" status</li>
                      <li>• Save all keys to start whale monitoring</li>
                    </ul>
                  </div>
                </div>

                <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-4 mt-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="text-yellow-400 mt-1" size={16} />
                    <div className="text-sm">
                      <p className="text-yellow-400 font-medium mb-1">Security Note</p>
                      <p className="text-gray-300">
                        API keys are stored securely and used only for blockchain data collection. 
                        Never share your API keys or enter them on untrusted websites.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default API;
