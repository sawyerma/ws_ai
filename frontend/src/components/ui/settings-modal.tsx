import { useState } from "react";
import { X } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Farbpalette wie im Bild
const COLOR_PALETTE = [
  // Graustufen
  "#ffffff", "#f3f4f6", "#e5e7eb", "#d1d5db", "#9ca3af", "#6b7280", "#4b5563", "#374151", "#1f2937", "#111827",
  // Rot-Töne
  "#fef2f2", "#fecaca", "#fca5a5", "#f87171", "#ef4444", "#dc2626", "#b91c1c", "#991b1b", "#7f1d1d", "#450a0a",
  // Orange-Töne
  "#fff7ed", "#fed7aa", "#fdba74", "#fb923c", "#f97316", "#ea580c", "#c2410c", "#9a3412", "#7c2d12", "#431407",
  // Gelb-Töne
  "#fefce8", "#fef3c7", "#fde68a", "#fcd34d", "#facc15", "#eab308", "#ca8a04", "#a16207", "#854d0e", "#422006",
  // Grün-Töne
  "#f0fdf4", "#bbf7d0", "#86efac", "#4ade80", "#22c55e", "#16a34a", "#15803d", "#166534", "#14532d", "#052e16",
  // Türkis-Töne
  "#f0fdfa", "#ccfbf1", "#99f6e4", "#5eead4", "#2dd4bf", "#14b8a6", "#0d9488", "#0f766e", "#115e59", "#042f2e",
  // Blau-Töne
  "#eff6ff", "#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8", "#1e40af", "#1e3a8a",
  // Indigo-Töne
  "#eef2ff", "#e0e7ff", "#c7d2fe", "#a5b4fc", "#818cf8", "#6366f1", "#4f46e5", "#4338ca", "#3730a3", "#312e81",
  // Lila-Töne
  "#faf5ff", "#e9d5ff", "#d8b4fe", "#c084fc", "#a855f7", "#9333ea", "#7c3aed", "#6d28d9", "#5b21b6", "#4c1d95",
  // Pink-Töne
  "#fdf2f8", "#fce7f3", "#fbcfe8", "#f9a8d4", "#f472b6", "#ec4899", "#db2777", "#be185d", "#9d174d", "#831843",
];

const SettingsModal = ({ isOpen, onClose }: SettingsModalProps) => {
  const [activeSection, setActiveSection] = useState("Chart");

  // Chart-Styling States - aus localStorage laden
  const [chartSettings, setChartSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('chartSettings');
      return saved ? JSON.parse(saved) : {
        backgroundColor: "#ffffff",
        darkBackgroundColor: "#1f2937",
        gridColor: "#e5e7eb",
        darkGridColor: "#374151",
        textColor: "#111827",
        darkTextColor: "#f9fafb",
        upCandleColor: "#22c55e",
        downCandleColor: "#ef4444",
        upWickColor: "#22c55e",
        downWickColor: "#ef4444",
        borderVisible: false,
        timeScaleVisible: true,
        priceScaleVisible: true,
        crosshairVisible: true,
        volumeVisible: false,
        // Symbol settings
        logoVisible: true,
        titleVisible: true,
        titleFormat: "description", // description, symbol, full
        chartValuesVisible: true,
        barChangesVisible: true,
        volumeSymbolVisible: false,
        lastDayChangesVisible: false,
        // Indicator settings
        indicatorTitleVisible: true,
        indicatorInputsVisible: true,
        indicatorValuesVisible: true,
        indicatorBackgroundVisible: true,
        indicatorBackgroundOpacity: 80,
        // Candle settings
        colorByPreviousClose: false,
        // Data modification
        session: "regular", // regular, extended
        precision: "standard", // standard, high, maximum
        timezone: "berlin", // berlin, london, newyork
        // Scale and lines
        scalingMode: "auto", // auto, percentage, logarithmic
        lockPriceToBar: false,
        scalePosition: "auto", // auto, left, right
        noOverlappingLabels: true,
        orderManagementButtons: false,
        nextBarCountdown: false,
        // Canvas settings
        backgroundType: "solid", // solid, gradient
        gridLinesType: "both", // both, vertical, horizontal, none
        sessionBreaks: false,
        windowSeparators: false,
        crosshairType: "normal", // normal, magnet, none
        watermarkVisible: false,
        // Scaling
        textSize: 12,
        lineWidth: 1,
      };
    } catch {
      return {
        backgroundColor: "#ffffff",
        darkBackgroundColor: "#1f2937",
        gridColor: "#e5e7eb",
        darkGridColor: "#374151",
        textColor: "#111827",
        darkTextColor: "#f9fafb",
        upCandleColor: "#22c55e",
        downCandleColor: "#ef4444",
        upWickColor: "#22c55e",
        downWickColor: "#ef4444",
        borderVisible: false,
        timeScaleVisible: true,
        priceScaleVisible: true,
        crosshairVisible: true,
        volumeVisible: false,
        logoVisible: true,
        titleVisible: true,
        titleFormat: "description",
        chartValuesVisible: true,
        barChangesVisible: true,
        volumeSymbolVisible: false,
        lastDayChangesVisible: false,
        indicatorTitleVisible: true,
        indicatorInputsVisible: true,
        indicatorValuesVisible: true,
        indicatorBackgroundVisible: true,
        indicatorBackgroundOpacity: 80,
        colorByPreviousClose: false,
        session: "regular",
        precision: "standard",
        timezone: "berlin",
        scalingMode: "auto",
        lockPriceToBar: false,
        scalePosition: "auto",
        noOverlappingLabels: true,
        orderManagementButtons: false,
        nextBarCountdown: false,
        backgroundType: "solid",
        gridLinesType: "both",
        sessionBreaks: false,
        windowSeparators: false,
        crosshairType: "normal",
        watermarkVisible: false,
        textSize: 12,
        lineWidth: 1,
      };
    }
  });

  if (!isOpen) return null;

  const sidebarItems = [
    { id: "Symbol", name: "Symbol", icon: "🔧" },
    { id: "Chart", name: "Chart Styling", icon: "🎨" },
    { id: "StatusZeile", name: "Status Zeile", icon: "📊" },
    { id: "SkalaLinien", name: "Skala und Linien", icon: "📏" },
    { id: "Canvas", name: "Canvas", icon: "🖼️" },
    { id: "Trading", name: "Trading", icon: "💹" },
    { id: "Alarme", name: "Alarme", icon: "⏰" },
    { id: "Ereignisse", name: "Ereignisse", icon: "📅" },
  ];

  const handleChartSettingChange = (key: string, value: any) => {
    const newSettings = {
      ...chartSettings,
      [key]: value
    };
    
    setChartSettings(newSettings);
    
    // Speichere in localStorage
    localStorage.setItem('chartSettings', JSON.stringify(newSettings));
    
    // Dispatch custom event für Chart-Updates
    window.dispatchEvent(new CustomEvent('chartSettingsChanged', { 
      detail: newSettings 
    }));
  };

  // Color Picker Component
  const ColorPicker = ({ 
    currentColor, 
    onColorChange, 
    label 
  }: { 
    currentColor: string; 
    onColorChange: (color: string) => void; 
    label: string;
  }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <div className="relative">
        <label className="block text-sm text-gray-300 mb-2">{label}</label>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-12 h-8 rounded border border-gray-600 flex items-center justify-center"
          style={{ backgroundColor: currentColor }}
        >
          <div 
            className="w-8 h-6 rounded border border-gray-400"
            style={{ backgroundColor: currentColor }}
          />
        </button>

        {isOpen && (
          <>
            {/* Overlay */}
            <div 
              className="fixed inset-0 z-40" 
              onClick={() => setIsOpen(false)} 
            />
            
            {/* Color Palette */}
            <div className="absolute top-full left-0 mt-2 z-50 bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-xl">
              <div className="grid grid-cols-10 gap-1 w-64">
                {COLOR_PALETTE.map((color, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      onColorChange(color);
                      setIsOpen(false);
                    }}
                    className={`w-6 h-6 rounded border-2 hover:scale-110 transition-transform ${
                      currentColor === color ? 'border-white' : 'border-gray-500'
                    }`}
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    );
  };

  const renderChartStylingSection = () => (
    <div className="flex-1 p-6 overflow-y-auto">
      <h3 className="text-sm font-medium text-gray-400 dark:text-gray-500 mb-4 tracking-wider">
        CHART APPEARANCE
      </h3>

      <div className="space-y-6">
        {/* Background Colors */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-white">Background</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <ColorPicker
              currentColor={chartSettings.backgroundColor}
              onColorChange={(color) => handleChartSettingChange('backgroundColor', color)}
              label="Light Mode"
            />
            
            <ColorPicker
              currentColor={chartSettings.darkBackgroundColor}
              onColorChange={(color) => handleChartSettingChange('darkBackgroundColor', color)}
              label="Dark Mode"
            />
          </div>
        </div>

        {/* Grid Colors */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-white">Grid Lines</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <ColorPicker
              currentColor={chartSettings.gridColor}
              onColorChange={(color) => handleChartSettingChange('gridColor', color)}
              label="Light Grid"
            />
            
            <ColorPicker
              currentColor={chartSettings.darkGridColor}
              onColorChange={(color) => handleChartSettingChange('darkGridColor', color)}
              label="Dark Grid"
            />
          </div>
        </div>

        {/* Candle Colors */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-white">Candlestick Colors</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <ColorPicker
              currentColor={chartSettings.upCandleColor}
              onColorChange={(color) => {
                handleChartSettingChange('upCandleColor', color);
                handleChartSettingChange('upWickColor', color);
              }}
              label="Bullish (Up)"
            />
            
            <ColorPicker
              currentColor={chartSettings.downCandleColor}
              onColorChange={(color) => {
                handleChartSettingChange('downCandleColor', color);
                handleChartSettingChange('downWickColor', color);
              }}
              label="Bearish (Down)"
            />
          </div>
        </div>

        {/* Chart Elements */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-white">Chart Elements</h4>
          
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="timeScale"
                checked={chartSettings.timeScaleVisible}
                onChange={(e) => handleChartSettingChange('timeScaleVisible', e.target.checked)}
                className="w-4 h-4 rounded border-gray-600"
              />
              <label htmlFor="timeScale" className="text-white text-sm">
                Time Scale
              </label>
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="priceScale"
                checked={chartSettings.priceScaleVisible}
                onChange={(e) => handleChartSettingChange('priceScaleVisible', e.target.checked)}
                className="w-4 h-4 rounded border-gray-600"
              />
              <label htmlFor="priceScale" className="text-white text-sm">
                Price Scale
              </label>
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="crosshair"
                checked={chartSettings.crosshairVisible}
                onChange={(e) => handleChartSettingChange('crosshairVisible', e.target.checked)}
                className="w-4 h-4 rounded border-gray-600"
              />
              <label htmlFor="crosshair" className="text-white text-sm">
                Crosshair
              </label>
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="volume"
                checked={chartSettings.volumeVisible}
                onChange={(e) => handleChartSettingChange('volumeVisible', e.target.checked)}
                className="w-4 h-4 rounded border-gray-600"
              />
              <label htmlFor="volume" className="text-white text-sm">
                Volume Bars
              </label>
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="borders"
                checked={chartSettings.borderVisible}
                onChange={(e) => handleChartSettingChange('borderVisible', e.target.checked)}
                className="w-4 h-4 rounded border-gray-600"
              />
              <label htmlFor="borders" className="text-white text-sm">
                Candle Borders
              </label>
            </div>
          </div>
        </div>

        {/* Reset Button */}
        <div className="pt-4 border-t border-gray-600">
          <button
            onClick={() => {
              const defaultSettings = {
                backgroundColor: "#ffffff",
                darkBackgroundColor: "#1f2937",
                gridColor: "#e5e7eb",
                darkGridColor: "#374151",
                textColor: "#111827",
                darkTextColor: "#f9fafb",
                upCandleColor: "#22c55e",
                downCandleColor: "#ef4444",
                upWickColor: "#22c55e",
                downWickColor: "#ef4444",
                borderVisible: false,
                timeScaleVisible: true,
                priceScaleVisible: true,
                crosshairVisible: true,
                volumeVisible: false,
              };
              setChartSettings(defaultSettings);
              localStorage.setItem('chartSettings', JSON.stringify(defaultSettings));
              window.dispatchEvent(new CustomEvent('chartSettingsChanged', { 
                detail: defaultSettings 
              }));
            }}
            className="px-4 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-500 transition-colors"
          >
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  );

  const renderSymbolSection = () => (
    <div className="flex-1 p-6 overflow-y-auto">
      <h3 className="text-sm font-medium text-gray-400 dark:text-gray-500 mb-4 tracking-wider">
        SYMBOL
      </h3>

      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="logo"
            checked={chartSettings.logoVisible}
            onChange={(e) => handleChartSettingChange('logoVisible', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="logo" className="text-white text-sm">
            Logo
          </label>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="titel"
              checked={chartSettings.titleVisible}
              onChange={(e) => handleChartSettingChange('titleVisible', e.target.checked)}
              className="w-4 h-4 rounded border-gray-600"
            />
            <label htmlFor="titel" className="text-white text-sm">
              Titel
            </label>
          </div>
          <select 
            value={chartSettings.titleFormat}
            onChange={(e) => handleChartSettingChange('titleFormat', e.target.value)}
            className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600 min-w-[120px]"
          >
            <option value="description">Beschreibung</option>
            <option value="symbol">Symbol</option>
            <option value="full">Vollständig</option>
          </select>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="chartwerte"
            checked={chartSettings.chartValuesVisible}
            onChange={(e) => handleChartSettingChange('chartValuesVisible', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="chartwerte" className="text-white text-sm">
            Chartwerte
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="balken"
            checked={chartSettings.barChangesVisible}
            onChange={(e) => handleChartSettingChange('barChangesVisible', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="balken" className="text-white text-sm">
            Balken Änderungswerte
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="volumen"
            checked={chartSettings.volumeSymbolVisible}
            onChange={(e) => handleChartSettingChange('volumeSymbolVisible', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="volumen" className="text-white text-sm">
            Volumen
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="werte"
            checked={chartSettings.lastDayChangesVisible}
            onChange={(e) => handleChartSettingChange('lastDayChangesVisible', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="werte" className="text-white text-sm">
            Werte von Veränderungen am letzten Handelstag
          </label>
        </div>
      </div>

      <h3 className="text-sm font-medium text-gray-400 dark:text-gray-500 mb-4 mt-8 tracking-wider">
        INDIKATOREN
      </h3>

      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="ind-titel"
            checked={chartSettings.indicatorTitleVisible}
            onChange={(e) => handleChartSettingChange('indicatorTitleVisible', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="ind-titel" className="text-white text-sm">
            Titel
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="eingaben"
            checked={chartSettings.indicatorInputsVisible}
            onChange={(e) => handleChartSettingChange('indicatorInputsVisible', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="eingaben" className="text-white text-sm">
            Eingaben
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="werte-ind"
            checked={chartSettings.indicatorValuesVisible}
            onChange={(e) => handleChartSettingChange('indicatorValuesVisible', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="werte-ind" className="text-white text-sm">
            Werte
          </label>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="hintergrund"
              checked={chartSettings.indicatorBackgroundVisible}
              onChange={(e) => handleChartSettingChange('indicatorBackgroundVisible', e.target.checked)}
              className="w-4 h-4 rounded border-gray-600"
            />
            <label htmlFor="hintergrund" className="text-white text-sm">
              Hintergrund
            </label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="range"
              min="0"
              max="100"
              value={chartSettings.indicatorBackgroundOpacity}
              onChange={(e) => handleChartSettingChange('indicatorBackgroundOpacity', parseInt(e.target.value))}
              className="w-32 h-2 bg-blue-600 rounded-lg appearance-none slider"
            />
            <span className="text-white text-xs w-8">{chartSettings.indicatorBackgroundOpacity}%</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStatusZeileSection = () => (
    <div className="flex-1 p-6 overflow-y-auto">
      <h3 className="text-sm font-medium text-gray-400 dark:text-gray-500 mb-4 tracking-wider">
        KERZEN
      </h3>

      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="balken-farben"
            checked={chartSettings.colorByPreviousClose}
            onChange={(e) => handleChartSettingChange('colorByPreviousClose', e.target.checked)}
            className="w-4 h-4 rounded border-gray-600"
          />
          <label htmlFor="balken-farben" className="text-white text-sm">
            Balken gemäß des vorherigen Schlusskurs färben
          </label>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="korper"
                checked={true}
                readOnly
                className="w-4 h-4 rounded border-gray-600"
              />
              <label htmlFor="korper" className="text-white text-sm">
                Körper
              </label>
            </div>
            <div className="flex space-x-2">
              <ColorPicker
                currentColor={chartSettings.upCandleColor}
                onColorChange={(color) => handleChartSettingChange('upCandleColor', color)}
                label=""
              />
              <ColorPicker
                currentColor={chartSettings.downCandleColor}
                onColorChange={(color) => handleChartSettingChange('downCandleColor', color)}
                label=""
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="rahmen"
                checked={chartSettings.borderVisible}
                onChange={(e) => handleChartSettingChange('borderVisible', e.target.checked)}
                className="w-4 h-4 rounded border-gray-600"
              />
              <label htmlFor="rahmen" className="text-white text-sm">
                Rahmen
              </label>
            </div>
            <div className="flex space-x-2">
              <ColorPicker
                currentColor={chartSettings.upCandleColor}
                onColorChange={(color) => handleChartSettingChange('upCandleColor', color)}
                label=""
              />
              <ColorPicker
                currentColor={chartSettings.downCandleColor}
                onColorChange={(color) => handleChartSettingChange('downCandleColor', color)}
                label=""
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="docht"
                checked={true}
                readOnly
                className="w-4 h-4 rounded border-gray-600"
              />
              <label htmlFor="docht" className="text-white text-sm">
                Docht
              </label>
            </div>
            <div className="flex space-x-2">
              <ColorPicker
                currentColor={chartSettings.upWickColor}
                onColorChange={(color) => handleChartSettingChange('upWickColor', color)}
                label=""
              />
              <ColorPicker
                currentColor={chartSettings.downWickColor}
                onColorChange={(color) => handleChartSettingChange('downWickColor', color)}
                label=""
              />
            </div>
          </div>
        </div>
      </div>

      <h3 className="text-sm font-medium text-gray-400 dark:text-gray-500 mb-4 mt-8 tracking-wider">
        MODIFIZIERUNG DER DATEN
      </h3>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-white text-sm">Sitzung</label>
          <select 
            value={chartSettings.session}
            onChange={(e) => handleChartSettingChange('session', e.target.value)}
            className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600 min-w-[140px]"
          >
            <option value="regular">Reguläre Handelszeiten</option>
            <option value="extended">Erweiterte Handelszeiten</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <label className="text-white text-sm">Präzision</label>
          <select 
            value={chartSettings.precision}
            onChange={(e) => handleChartSettingChange('precision', e.target.value)}
            className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600 min-w-[100px]"
          >
            <option value="standard">Standard</option>
            <option value="high">Hoch</option>
            <option value="maximum">Maximum</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <label className="text-white text-sm">Zeitzone</label>
          <select 
            value={chartSettings.timezone}
            onChange={(e) => handleChartSettingChange('timezone', e.target.value)}
            className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600 min-w-[120px]"
          >
            <option value="berlin">(UTC+2) Berlin</option>
            <option value="london">(UTC+0) London</option>
            <option value="newyork">(UTC-5) New York</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderDefaultSection = () => (
    <div className="flex-1 p-6">
      <h3 className="text-lg font-medium text-white mb-4">{activeSection}</h3>
      <p className="text-gray-400">
        Einstellungen für {activeSection.toLowerCase()} sind noch nicht
        verfügbar.
      </p>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case "Symbol":
        return renderSymbolSection();
      case "Chart":
        return renderChartStylingSection();
      case "StatusZeile":
        return renderStatusZeileSection();
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
          <h2 className="text-lg font-medium text-white">Einstellungen</h2>
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
          <div className="w-64 bg-gray-700 border-r border-gray-600">
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

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between p-4 border-t border-gray-700 bg-gray-800">
          <select className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600">
            <option>Vorlage</option>
            <option>Standard</option>
            <option>Dunkel</option>
            <option>Hell</option>
          </select>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              Abbrechen
            </button>
            <button
              onClick={onClose}
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

export default SettingsModal;