import { useState, useRef, useEffect } from "react";
import { 
  ChevronUp, 
  ChevronDown, 
  X, 
  Minimize2, 
  Maximize2,
  GripHorizontal,
  Settings,
  Plus,
  MoreHorizontal
} from "lucide-react";
import ChartView from "../ChartView";
import IndicatorSettingsModal from "./indicator-settings-modal";

interface ChartPanel {
  id: string;
  type: "main" | "volume" | "indicator";
  title: string;
  height: number; // in percentage
  minimized: boolean;
  maximized: boolean;
  indicators: string[]; // Indicators shown in this panel
}

interface TradingChartProps {
  selectedCoin?: string;
  selectedMarket?: string;
  selectedInterval?: string;
  selectedIndicators?: string[];
  onIndicatorRemove?: (indicator: string) => void;
}

const TradingChart = ({
  selectedCoin = "BTC/USDT",
  selectedMarket = "spot",
  selectedInterval = "1m",
  selectedIndicators = [],
  onIndicatorRemove
}: TradingChartProps) => {
  const [panels, setPanels] = useState<ChartPanel[]>([
    {
      id: "main",
      type: "main",
      title: "Price Chart",
      height: 100,
      minimized: false,
      maximized: false,
      indicators: []
    }
  ]);

  const [dragState, setDragState] = useState<{
    isDragging: boolean;
    panelId: string | null;
    startY: number;
    startHeight: number;
  }>({
    isDragging: false,
    panelId: null,
    startY: 0,
    startHeight: 0,
  });

  const [contextMenu, setContextMenu] = useState<{
    isOpen: boolean;
    x: number;
    y: number;
    panelId: string;
    indicatorType: string;
  }>({
    isOpen: false,
    x: 0,
    y: 0,
    panelId: "",
    indicatorType: ""
  });

  const [settingsModal, setSettingsModal] = useState<{
    isOpen: boolean;
    indicatorType: string;
    panelId: string;
  }>({
    isOpen: false,
    indicatorType: "",
    panelId: ""
  });

  const containerRef = useRef<HTMLDivElement>(null);

  // Handle indicator selection - Smart placement logic
  useEffect(() => {
    if (selectedIndicators.length === 0) return;

    const latestIndicator = selectedIndicators[selectedIndicators.length - 1];
    
    // Check if indicator already exists in any panel
    const existsInPanel = panels.some(panel => 
      panel.indicators.includes(latestIndicator)
    );
    
    if (existsInPanel) return; // Don't add duplicates

    // Smart placement logic
    if (latestIndicator === "candlestick") {
      // Candlestick creates a new panel
      const newPanelId = `panel-${Date.now()}`;
      setPanels(prev => {
        const visiblePanels = prev.filter(p => !p.minimized);
        const newHeight = 100 / (visiblePanels.length + 1);
        const updatedPanels = prev.map(panel => ({
          ...panel,
          height: panel.minimized ? panel.height : newHeight
        }));
        
        return [
          ...updatedPanels,
          {
            id: newPanelId,
            type: "indicator",
            title: "Candlestick Chart",
            height: newHeight,
            minimized: false,
            maximized: false,
            indicators: [latestIndicator]
          }
        ];
      });
    } else if (latestIndicator === "volume") {
      // Volume creates a new panel
      const newPanelId = `panel-${Date.now()}`;
      setPanels(prev => {
        const visiblePanels = prev.filter(p => !p.minimized);
        const newHeight = 100 / (visiblePanels.length + 1);
        const updatedPanels = prev.map(panel => ({
          ...panel,
          height: panel.minimized ? panel.height : newHeight
        }));
        
        return [
          ...updatedPanels,
          {
            id: newPanelId,
            type: "volume",
            title: "Volume",
            height: newHeight,
            minimized: false,
            maximized: false,
            indicators: [latestIndicator]
          }
        ];
      });
    } else {
      // Other indicators go to main chart
      setPanels(prev => prev.map(panel => {
        if (panel.id === "main") {
          return {
            ...panel,
            indicators: [...panel.indicators, latestIndicator]
          };
        }
        return panel;
      }));
    }
  }, [selectedIndicators]);

  const movePanel = (panelId: string, direction: "up" | "down") => {
    setPanels(prev => {
      const currentIndex = prev.findIndex(p => p.id === panelId);
      if (currentIndex === -1) return prev;

      const newPanels = [...prev];
      const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;

      if (targetIndex >= 0 && targetIndex < newPanels.length) {
        [newPanels[currentIndex], newPanels[targetIndex]] = 
        [newPanels[targetIndex], newPanels[currentIndex]];
      }

      return newPanels;
    });
  };

  const deletePanel = (panelId: string) => {
    setPanels(prev => {
      if (prev.length <= 1 || panelId === "main") return prev; // Keep main panel
      
      const panelToDelete = prev.find(p => p.id === panelId);
      if (panelToDelete && onIndicatorRemove) {
        // Remove all indicators from this panel from the global state
        panelToDelete.indicators.forEach(indicator => {
          onIndicatorRemove(indicator);
        });
      }
      
      const filtered = prev.filter(p => p.id !== panelId);
      
      // Redistribute height proportionally among visible panels
      const visiblePanels = filtered.filter(p => !p.minimized);
      const totalHeight = 100;
      const heightPerPanel = totalHeight / visiblePanels.length;
      
      return filtered.map(panel => ({
        ...panel,
        height: panel.minimized ? panel.height : heightPerPanel
      }));
    });
  };

  const removeIndicator = (panelId: string, indicator: string) => {
    // Remove from global state
    if (onIndicatorRemove) {
      onIndicatorRemove(indicator);
    }

    // Remove from panel
    setPanels(prev => prev.map(panel => {
      if (panel.id === panelId) {
        const newIndicators = panel.indicators.filter(i => i !== indicator);
        
        // If panel becomes empty and it's not the main panel, delete it
        if (newIndicators.length === 0 && panel.id !== "main") {
          return null; // Mark for deletion
        }
        
        return {
          ...panel,
          indicators: newIndicators
        };
      }
      return panel;
    }).filter(Boolean) as ChartPanel[]); // Remove null panels
  };

  const toggleMinimize = (panelId: string) => {
    setPanels(prev => {
      const updatedPanels = prev.map(panel => {
        if (panel.id === panelId) {
          return {
            ...panel,
            minimized: !panel.minimized,
            maximized: false
          };
        }
        return panel;
      });

      // Redistribute height among visible panels
      const visiblePanels = updatedPanels.filter(p => !p.minimized);
      const totalHeight = 100;
      const heightPerPanel = visiblePanels.length > 0 ? totalHeight / visiblePanels.length : 100;
      
      return updatedPanels.map(panel => ({
        ...panel,
        height: panel.minimized ? panel.height : heightPerPanel
      }));
    });
  };

  const toggleMaximize = (panelId: string) => {
    setPanels(prev => prev.map(panel => {
      if (panel.id === panelId) {
        return {
          ...panel,
          maximized: !panel.maximized,
          minimized: false
        };
      }
      return {
        ...panel,
        maximized: false,
        minimized: false
      };
    }));
  };

  const addNewPanel = () => {
    const newPanelId = `panel-${Date.now()}`;
    setPanels(prev => {
      const visiblePanels = prev.filter(p => !p.minimized);
      const newHeight = 100 / (visiblePanels.length + 1);
      const updatedPanels = prev.map(panel => ({
        ...panel,
        height: panel.minimized ? panel.height : newHeight
      }));
      
      return [
        ...updatedPanels,
        {
          id: newPanelId,
          type: "indicator",
          title: "New Panel",
          height: newHeight,
          minimized: false,
          maximized: false,
          indicators: []
        }
      ];
    });
  };

  const handleContextMenu = (e: React.MouseEvent, panelId: string, indicatorType: string) => {
    e.preventDefault();
    setContextMenu({
      isOpen: true,
      x: e.clientX,
      y: e.clientY,
      panelId,
      indicatorType
    });
  };

  const closeContextMenu = () => {
    setContextMenu(prev => ({ ...prev, isOpen: false }));
  };

  const openSettingsModal = (indicatorType: string, panelId: string) => {
    setSettingsModal({
      isOpen: true,
      indicatorType,
      panelId
    });
    closeContextMenu();
  };

  const closeSettingsModal = () => {
    setSettingsModal({
      isOpen: false,
      indicatorType: "",
      panelId: ""
    });
  };

  const handleSettingsSave = (settings: any) => {
    console.log("Indicator settings saved:", settings);
    // Here you would apply the settings to the indicator
  };

  const handleResizeStart = (e: React.MouseEvent, panelId: string) => {
    e.preventDefault();
    const panel = panels.find(p => p.id === panelId);
    if (!panel) return;

    setDragState({
      isDragging: true,
      panelId,
      startY: e.clientY,
      startHeight: panel.height,
    });
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!dragState.isDragging || !dragState.panelId || !containerRef.current) return;

      const containerHeight = containerRef.current.getBoundingClientRect().height;
      const deltaY = e.clientY - dragState.startY;
      const deltaPercentage = (deltaY / containerHeight) * 100;
      
      const newHeight = Math.max(15, Math.min(85, dragState.startHeight + deltaPercentage));

      setPanels(prev => prev.map(panel => {
        if (panel.id === dragState.panelId) {
          return { ...panel, height: newHeight };
        }
        return panel;
      }));
    };

    const handleMouseUp = () => {
      setDragState({
        isDragging: false,
        panelId: null,
        startY: 0,
        startHeight: 0,
      });
    };

    const handleClickOutside = () => {
      closeContextMenu();
    };

    if (dragState.isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    if (contextMenu.isOpen) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [dragState, contextMenu.isOpen]);

  const getVisiblePanels = () => {
    const maximizedPanel = panels.find(p => p.maximized);
    if (maximizedPanel) {
      return [{ ...maximizedPanel, height: 100 }];
    }
    return panels.filter(p => !p.minimized);
  };

  const getMinimizedPanels = () => {
    return panels.filter(p => p.minimized);
  };

  const getIndicatorDisplayName = (indicator: string): string => {
    const names: { [key: string]: string } = {
      "candlestick": "Candlestick Chart",
      "volume": "Volume",
      "rsi": "RSI (14)",
      "macd": "MACD (12, 26, 9)",
      "ema": "EMA (20)",
      "sma": "SMA (20)",
      "bollinger": "Bollinger Bands (20, 2)",
      "andean": "Andean Oscillator 50 9",
      "elliott": "Elliott Wave Oscillator",
      "momentum": "Momentum"
    };
    return names[indicator] || indicator.toUpperCase();
  };

  const renderContextMenu = () => {
    if (!contextMenu.isOpen) return null;

    return (
      <div
        className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg py-1 min-w-[160px]"
        style={{
          left: contextMenu.x,
          top: contextMenu.y,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
          onClick={() => openSettingsModal(contextMenu.indicatorType, contextMenu.panelId)}
        >
          <Settings size={14} />
          Settings
        </button>
        
        <button
          className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
          onClick={() => {
            movePanel(contextMenu.panelId, "up");
            closeContextMenu();
          }}
          disabled={panels.findIndex(p => p.id === contextMenu.panelId) === 0}
        >
          <ChevronUp size={14} />
          Move Up
        </button>
        
        <button
          className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
          onClick={() => {
            movePanel(contextMenu.panelId, "down");
            closeContextMenu();
          }}
          disabled={panels.findIndex(p => p.id === contextMenu.panelId) === panels.length - 1}
        >
          <ChevronDown size={14} />
          Move Down
        </button>
        
        <div className="border-t border-gray-200 dark:border-gray-600 my-1"></div>
        
        <button
          className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
          onClick={() => {
            toggleMinimize(contextMenu.panelId);
            closeContextMenu();
          }}
        >
          <Minimize2 size={14} />
          Minimize
        </button>
        
        <button
          className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
          onClick={() => {
            toggleMaximize(contextMenu.panelId);
            closeContextMenu();
          }}
        >
          <Maximize2 size={14} />
          Maximize
        </button>
        
        {contextMenu.indicatorType !== "main" && (
          <>
            <div className="border-t border-gray-200 dark:border-gray-600 my-1"></div>
            
            <button
              className="w-full px-3 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
              onClick={() => {
                removeIndicator(contextMenu.panelId, contextMenu.indicatorType);
                closeContextMenu();
              }}
            >
              <X size={14} />
              Remove
            </button>
          </>
        )}
      </div>
    );
  };

  const renderChart = (panel: ChartPanel) => {
    const wsUrl = `ws://localhost:8100/ws/${selectedCoin.replace("/", "")}/${selectedMarket}`;
    
    return (
      <div className="relative h-full">
        <ChartView
          key={`${panel.id}-${selectedCoin}-${selectedInterval}-${panel.indicators.join(",")}`}
          wsUrl={wsUrl}
          symbol={selectedCoin.replace("/", "")}
          market={selectedMarket}
          interval={selectedInterval}
          width={800}
          height={400}
        />
        
        {/* Main Chart Label (always show for main panel) */}
        {panel.id === "main" && (
          <div className="absolute top-2 left-2 flex flex-wrap gap-1 z-10">
            <div
              className="flex items-center gap-1 bg-black bg-opacity-60 text-white px-2 py-1 rounded text-xs group"
              onContextMenu={(e) => handleContextMenu(e, panel.id, "main")}
            >
              <span>Candlestick Chart</span>
              
              {/* Indicator Controls */}
              <div className="flex items-center gap-1 ml-1">
                {/* Settings */}
                <button
                  onClick={() => openSettingsModal("main", panel.id)}
                  className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                  title="Settings"
                >
                  <Settings size={10} />
                </button>
                
                {/* Move Up */}
                <button
                  onClick={() => movePanel(panel.id, "up")}
                  className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                  title="Move Up"
                  disabled={panels.findIndex(p => p.id === panel.id) === 0}
                >
                  <ChevronUp size={10} />
                </button>
                
                {/* Move Down */}
                <button
                  onClick={() => movePanel(panel.id, "down")}
                  className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                  title="Move Down"
                  disabled={panels.findIndex(p => p.id === panel.id) === panels.length - 1}
                >
                  <ChevronDown size={10} />
                </button>
                
                {/* Minimize */}
                <button
                  onClick={() => toggleMinimize(panel.id)}
                  className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                  title="Minimize"
                >
                  <Minimize2 size={10} />
                </button>
                
                {/* Maximize */}
                <button
                  onClick={() => toggleMaximize(panel.id)}
                  className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                  title="Maximize"
                >
                  <Maximize2 size={10} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Indicator Labels Overlay (for additional indicators) */}
        {panel.indicators.length > 0 && (
          <div className="absolute top-2 left-2 flex flex-wrap gap-1 z-10" style={{ marginTop: panel.id === "main" ? "32px" : "0" }}>
            {panel.indicators.map((indicator, index) => (
              <div
                key={indicator}
                className="flex items-center gap-1 bg-black bg-opacity-60 text-white px-2 py-1 rounded text-xs group"
                onContextMenu={(e) => handleContextMenu(e, panel.id, indicator)}
              >
                <span>{getIndicatorDisplayName(indicator)}</span>
                
                {/* Indicator Controls */}
                <div className="flex items-center gap-1 ml-1">
                  {/* Settings */}
                  <button
                    onClick={() => openSettingsModal(indicator, panel.id)}
                    className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                    title="Settings"
                  >
                    <Settings size={10} />
                  </button>
                  
                  {/* Move Up */}
                  <button
                    onClick={() => movePanel(panel.id, "up")}
                    className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                    title="Move Up"
                    disabled={panels.findIndex(p => p.id === panel.id) === 0}
                  >
                    <ChevronUp size={10} />
                  </button>
                  
                  {/* Move Down */}
                  <button
                    onClick={() => movePanel(panel.id, "down")}
                    className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                    title="Move Down"
                    disabled={panels.findIndex(p => p.id === panel.id) === panels.length - 1}
                  >
                    <ChevronDown size={10} />
                  </button>
                  
                  {/* Delete */}
                  <button
                    onClick={() => removeIndicator(panel.id, indicator)}
                    className="p-0.5 hover:bg-red-500 hover:bg-opacity-60 rounded"
                    title="Remove"
                  >
                    <X size={10} />
                  </button>
                  
                  {/* Minimize */}
                  <button
                    onClick={() => toggleMinimize(panel.id)}
                    className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                    title="Minimize"
                  >
                    <Minimize2 size={10} />
                  </button>
                  
                  {/* Maximize */}
                  <button
                    onClick={() => toggleMaximize(panel.id)}
                    className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                    title="Maximize"
                  >
                    <Maximize2 size={10} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Panel Controls (top right) */}
        <div className="absolute top-2 right-2 flex items-center gap-1 z-10">
          {/* Delete Panel (only for non-main panels) */}
          {panel.id !== "main" && (
            <button
              onClick={() => deletePanel(panel.id)}
              className="p-1 bg-black bg-opacity-60 text-white hover:bg-red-500 hover:bg-opacity-60 rounded"
              title="Delete Panel"
            >
              <X size={12} />
            </button>
          )}
        </div>
      </div>
    );
  };

  const visiblePanels = getVisiblePanels();
  const minimizedPanels = getMinimizedPanels();
  const totalVisibleHeight = visiblePanels.reduce((sum, panel) => sum + panel.height, 0);

  return (
    <div className="chart-container bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-600 h-full w-full overflow-hidden">
      {/* Chart Panels Container */}
      <div ref={containerRef} className="flex-1 flex flex-col h-full">
        {/* Visible Panels */}
        {visiblePanels.map((panel, index) => {
          const heightPercentage = totalVisibleHeight > 0 
            ? (panel.height / totalVisibleHeight) * 100 
            : 100 / visiblePanels.length;

          return (
            <div
              key={panel.id}
              className="relative flex flex-col border-b border-gray-200 dark:border-gray-600 last:border-b-0"
              style={{ height: `${heightPercentage}%` }}
            >
              {/* Chart Content */}
              <div className="flex-1 relative">
                {renderChart(panel)}
              </div>

              {/* Resize Handle */}
              {index < visiblePanels.length - 1 && !panel.maximized && (
                <div
                  className="absolute bottom-0 left-0 right-0 h-2 cursor-row-resize bg-transparent hover:bg-blue-500 hover:bg-opacity-20 flex items-center justify-center group z-20"
                  onMouseDown={(e) => handleResizeStart(e, panel.id)}
                >
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <GripHorizontal size={16} className="text-gray-400" />
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {/* Minimized Panels Bar - Styled like Panel Labels */}
        {minimizedPanels.length > 0 && (
          <div className="flex-shrink-0 bg-gray-800 dark:bg-gray-900 p-2">
            <div className="flex items-center gap-2 overflow-x-auto">
              {minimizedPanels.map(panel => (
                <div
                  key={panel.id}
                  className="flex items-center gap-1 bg-black bg-opacity-60 text-white px-2 py-1 rounded text-xs group flex-shrink-0"
                  onContextMenu={(e) => handleContextMenu(e, panel.id, panel.id === "main" ? "main" : panel.indicators[0] || "indicator")}
                >
                  <span>
                    {panel.id === "main" ? "Candlestick Chart" : 
                     panel.indicators.length > 0 ? getIndicatorDisplayName(panel.indicators[0]) : 
                     panel.title}
                  </span>
                  
                  {/* Minimized Panel Controls */}
                  <div className="flex items-center gap-1 ml-1">
                    {/* Settings */}
                    <button
                      onClick={() => openSettingsModal(
                        panel.id === "main" ? "main" : panel.indicators[0] || "indicator", 
                        panel.id
                      )}
                      className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                      title="Settings"
                    >
                      <Settings size={10} />
                    </button>
                    
                    {/* Restore (ChevronUp) */}
                    <button
                      onClick={() => toggleMinimize(panel.id)}
                      className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                      title="Restore"
                    >
                      <ChevronUp size={10} />
                    </button>
                    
                    {/* Move Down */}
                    <button
                      onClick={() => movePanel(panel.id, "down")}
                      className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                      title="Move Down"
                      disabled={panels.findIndex(p => p.id === panel.id) === panels.length - 1}
                    >
                      <ChevronDown size={10} />
                    </button>
                    
                    {/* Delete (only for non-main panels) */}
                    {panel.id !== "main" && (
                      <button
                        onClick={() => removeIndicator(panel.id, panel.indicators[0] || "")}
                        className="p-0.5 hover:bg-red-500 hover:bg-opacity-60 rounded"
                        title="Remove"
                      >
                        <X size={10} />
                      </button>
                    )}
                    
                    {/* Maximize */}
                    <button
                      onClick={() => {
                        toggleMinimize(panel.id); // First restore
                        setTimeout(() => toggleMaximize(panel.id), 50); // Then maximize
                      }}
                      className="p-0.5 hover:bg-white hover:bg-opacity-20 rounded"
                      title="Maximize"
                    >
                      <Maximize2 size={10} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Controls */}
      <div className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600">
        {/* Add Panel Button */}
        <button
          onClick={addNewPanel}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          <Plus size={12} />
          Add Panel
        </button>

        {/* Panel Count Info */}
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {visiblePanels.length} visible, {minimizedPanels.length} minimized
        </div>
      </div>

      {/* Context Menu */}
      {renderContextMenu()}

      {/* Settings Modal */}
      <IndicatorSettingsModal
        isOpen={settingsModal.isOpen}
        onClose={closeSettingsModal}
        indicatorType={settingsModal.indicatorType}
        panelId={settingsModal.panelId}
        onSave={handleSettingsSave}
      />
    </div>
  );
};

export default TradingChart;
