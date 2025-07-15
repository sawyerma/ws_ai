import { useState } from "react";
import { X, HelpCircle } from "lucide-react";

interface IndicatorSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  indicatorType: string;
  panelId: string;
  onSave?: (settings: any) => void;
}

const IndicatorSettingsModal = ({ 
  isOpen, 
  onClose, 
  indicatorType, 
  panelId,
  onSave 
}: IndicatorSettingsModalProps) => {
  const [activeTab, setActiveTab] = useState("Eingaben");
  const [settings, setSettings] = useState({
    // EMA Settings
    length: 20,
    source: "Schließ...",
    offset: 0,
    // Glättung
    type: "Ohne",
    smoothLength: 14,
    bbStdDev: 2,
    // Berechnung
    timeframe: "Chart",
    waitForTimeframeClose: true,
    // Eingabewerte
    showInputsInStatusLine: true,
  });

  if (!isOpen) return null;

  const getIndicatorTitle = () => {
    const titles: { [key: string]: string } = {
      "ema": "EMA",
      "sma": "SMA", 
      "rsi": "RSI",
      "macd": "MACD",
      "bollinger": "Bollinger Bands",
      "volume": "Volume",
      "candlestick": "Candlestick Chart",
      "main": "Candlestick Chart"
    };
    return titles[indicatorType] || indicatorType.toUpperCase();
  };

  const handleSave = () => {
    if (onSave) {
      onSave(settings);
    }
    onClose();
  };

  const renderEingabenTab = () => (
    <div className="space-y-6">
      {/* Länge */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-white text-sm">Länge</label>
          <input
            type="number"
            value={settings.length}
            onChange={(e) => setSettings(prev => ({ ...prev, length: parseInt(e.target.value) }))}
            className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Quelle */}
        <div className="flex items-center justify-between">
          <label className="text-white text-sm">Quelle</label>
          <select
            value={settings.source}
            onChange={(e) => setSettings(prev => ({ ...prev, source: e.target.value }))}
            className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
          >
            <option>Schließ...</option>
            <option>Öffnen</option>
            <option>Hoch</option>
            <option>Tief</option>
            <option>HL2</option>
            <option>HLC3</option>
            <option>OHLC4</option>
          </select>
        </div>

        {/* Offset */}
        <div className="flex items-center justify-between">
          <label className="text-white text-sm">Offset</label>
          <input
            type="number"
            value={settings.offset}
            onChange={(e) => setSettings(prev => ({ ...prev, offset: parseInt(e.target.value) }))}
            className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* GLÄTTUNG Section */}
      <div className="space-y-3">
        <h3 className="text-gray-400 text-xs uppercase tracking-wider font-medium">GLÄTTUNG</h3>
        
        {/* Typ */}
        <div className="flex items-center justify-between">
          <label className="text-white text-sm">Typ</label>
          <select
            value={settings.type}
            onChange={(e) => setSettings(prev => ({ ...prev, type: e.target.value }))}
            className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
          >
            <option>Ohne</option>
            <option>SMA</option>
            <option>EMA</option>
            <option>WMA</option>
          </select>
        </div>

        {/* Länge */}
        <div className="flex items-center justify-between">
          <label className="text-white text-sm">Länge</label>
          <input
            type="number"
            value={settings.smoothLength}
            onChange={(e) => setSettings(prev => ({ ...prev, smoothLength: parseInt(e.target.value) }))}
            className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* BB-StdDev */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <label className="text-white text-sm">BB-StdDev</label>
            <button className="text-gray-400 hover:text-white">
              <HelpCircle size={14} />
            </button>
          </div>
          <input
            type="number"
            value={settings.bbStdDev}
            onChange={(e) => setSettings(prev => ({ ...prev, bbStdDev: parseInt(e.target.value) }))}
            className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* BERECHNUNG Section */}
      <div className="space-y-3">
        <h3 className="text-gray-400 text-xs uppercase tracking-wider font-medium">BERECHNUNG</h3>
        
        {/* Zeitrahmen */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <label className="text-white text-sm">Zeitrahmen</label>
            <button className="text-gray-400 hover:text-white">
              <HelpCircle size={14} />
            </button>
          </div>
          <select
            value={settings.timeframe}
            onChange={(e) => setSettings(prev => ({ ...prev, timeframe: e.target.value }))}
            className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
          >
            <option>Chart</option>
            <option>1m</option>
            <option>5m</option>
            <option>15m</option>
            <option>1h</option>
            <option>4h</option>
            <option>1d</option>
          </select>
        </div>

        {/* Checkbox */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="waitForClose"
            checked={settings.waitForTimeframeClose}
            onChange={(e) => setSettings(prev => ({ ...prev, waitForTimeframeClose: e.target.checked }))}
            className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="waitForClose" className="text-white text-sm">
            Auf die Zeitrahmenschließung warten
          </label>
        </div>
      </div>

      {/* EINGABEWERTE Section */}
      <div className="space-y-3">
        <h3 className="text-gray-400 text-xs uppercase tracking-wider font-medium">EINGABEWERTE</h3>
        
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="showInputs"
            checked={settings.showInputsInStatusLine}
            onChange={(e) => setSettings(prev => ({ ...prev, showInputsInStatusLine: e.target.checked }))}
            className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="showInputs" className="text-white text-sm">
            Eingaben in der Statuszeile
          </label>
        </div>
      </div>
    </div>
  );

  const renderStilTab = () => (
    <div className="space-y-6">
      <div className="text-center py-12">
        <p className="text-gray-400">Stil-Einstellungen werden hier angezeigt</p>
      </div>
    </div>
  );

  const renderSichtbarkeitTab = () => (
    <div className="space-y-6">
      <div className="text-center py-12">
        <p className="text-gray-400">Sichtbarkeits-Einstellungen werden hier angezeigt</p>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-lg font-medium text-white">
            {getIndicatorTitle()}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-1 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          {["Eingaben", "Stil", "Sichtbarkeit"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "text-white border-b-2 border-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-4 max-h-96 overflow-y-auto">
          {activeTab === "Eingaben" && renderEingabenTab()}
          {activeTab === "Stil" && renderStilTab()}
          {activeTab === "Sichtbarkeit" && renderSichtbarkeitTab()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-700">
          {/* Preset Dropdown */}
          <select className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500">
            <option>Standard...</option>
            <option>Schnell</option>
            <option>Langsam</option>
            <option>Benutzerdefiniert</option>
          </select>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              Abbrechen
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
            >
              Ok
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IndicatorSettingsModal;