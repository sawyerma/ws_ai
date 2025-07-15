import { useState, useRef, useEffect } from "react";
import {
  ChevronUp,
  ChevronDown,
  Play,
  Save,
  Folder,
  FileText,
  Terminal,
  Code,
  Plus,
  X,
} from "lucide-react";

interface TradingTerminalProps {
  className?: string;
}

const TradingTerminal = ({ className = "" }: TradingTerminalProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState("editor");
  const [activeFile, setActiveFile] = useState("main.py");
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    "Trading Terminal v1.0.0",
    "Python 3.11.0 | Indicators Framework Ready",
    "Type 'help' for available commands",
    "",
  ]);
  const [terminalInput, setTerminalInput] = useState("");
  const [code, setCode] = useState(`# Trading Indicator Script
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class CustomIndicator:
    def __init__(self, name: str, period: int = 14):
        self.name = name
        self.period = period

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate your custom indicator
        data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        returns: Series with indicator values
        """
        # Example: Simple Moving Average
        return data['close'].rolling(window=self.period).mean()

    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals
        returns: Dictionary with signal information
        """
        indicator_values = self.calculate(data)

        signals = {
            'buy_signal': indicator_values > data['close'],
            'sell_signal': indicator_values < data['close'],
            'strength': abs(indicator_values - data['close']) / data['close']
        }

        return signals

# Create and test your indicator
indicator = CustomIndicator("My SMA", period=20)

# To add to indicators database, use:
# register_indicator(indicator)
`);

  const terminalRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  const files = [
    { name: "main.py", type: "python", active: true },
    { name: "rsi_custom.py", type: "python", active: false },
    { name: "macd_enhanced.py", type: "python", active: false },
    { name: "volume_profile.py", type: "python", active: false },
  ];

  const tabs = [
    { id: "editor", name: "Code Editor", icon: Code },
    { id: "terminal", name: "Terminal", icon: Terminal },
    { id: "output", name: "Output", icon: FileText },
    { id: "problems", name: "Problems", icon: FileText },
  ];

  const handleTerminalCommand = (command: string) => {
    const newOutput = [...terminalOutput, `> ${command}`];

    // Simulate command processing
    switch (command.toLowerCase().trim()) {
      case "help":
        newOutput.push("Available commands:");
        newOutput.push("  run          - Execute current script");
        newOutput.push("  test         - Test indicator with sample data");
        newOutput.push("  register     - Add indicator to database");
        newOutput.push("  list         - Show available indicators");
        newOutput.push("  clear        - Clear terminal");
        break;
      case "run":
        newOutput.push("Executing script...");
        newOutput.push("✓ Script executed successfully");
        newOutput.push("CustomIndicator initialized with period=20");
        break;
      case "test":
        newOutput.push("Testing indicator with sample BTC/USDT data...");
        newOutput.push("✓ Indicator test passed");
        newOutput.push("Generated 100 data points");
        newOutput.push("Buy signals: 23, Sell signals: 18");
        break;
      case "register":
        newOutput.push("Registering indicator in database...");
        newOutput.push("✓ CustomIndicator added to indicators database");
        newOutput.push("Available in Indicators modal");
        break;
      case "list":
        newOutput.push("Available custom indicators:");
        newOutput.push("  - CustomIndicator (SMA-based)");
        newOutput.push("  - RSI_Enhanced");
        newOutput.push("  - MACD_Advanced");
        newOutput.push("  - VolumeProfile");
        break;
      case "clear":
        setTerminalOutput([
          "Trading Terminal v1.0.0",
          "Type 'help' for available commands",
          "",
        ]);
        return;
      default:
        newOutput.push(`Command not found: ${command}`);
        newOutput.push("Type 'help' for available commands");
    }

    newOutput.push("");
    setTerminalOutput(newOutput);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleTerminalCommand(terminalInput);
      setTerminalInput("");
    }
  };

  const handleTextareaScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalOutput]);

  const renderEditor = () => (
    <div className="flex h-full">
      {/* File Explorer */}
      <div className="w-64 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-2 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <Folder size={16} />
              Indicators
            </h4>
            <button className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
              <Plus size={16} />
            </button>
          </div>
        </div>
        <div className="flex-1 p-2">
          {files.map((file, index) => (
            <div
              key={index}
              onClick={() => setActiveFile(file.name)}
              className={`flex items-center gap-2 px-2 py-1 rounded text-xs cursor-pointer transition-colors ${
                activeFile === file.name
                  ? "bg-blue-600 text-white"
                  : "text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
              }`}
            >
              <FileText size={14} />
              {file.name}
            </div>
          ))}
        </div>
      </div>

      {/* Code Editor */}
      <div className="flex-1 flex flex-col">
        {/* Editor Tabs */}
        <div className="flex items-center bg-gray-100 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm border-r border-gray-200 dark:border-gray-700">
            <FileText size={14} className="mr-2" />
            {activeFile}
            <button className="ml-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
              <X size={12} />
            </button>
          </div>
        </div>

        {/* Code Area */}
        <div className="flex-1 relative overflow-hidden">
          <div className="flex h-full">
            {/* Line Numbers */}
            <div
              ref={lineNumbersRef}
              className="w-10 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-3 font-mono text-xs text-gray-500 dark:text-gray-500 flex-shrink-0 overflow-hidden"
            >
              {Array.from(
                { length: Math.max(100, code.split("\n").length + 10) },
                (_, i) => (
                  <div key={i} style={{ lineHeight: "1.4", height: "16.8px" }}>
                    {i + 1}
                  </div>
                ),
              )}
            </div>

            {/* Code Editor */}
            <textarea
              ref={textareaRef}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onScroll={handleTextareaScroll}
              className="flex-1 h-full bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-3 font-mono text-xs resize-none focus:outline-none border-none"
              style={{ lineHeight: "1.4" }}
              spellCheck={false}
            />
          </div>
        </div>

        {/* Status Bar */}
        <div className="flex items-center justify-end p-2 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Python 3.11 • UTF-8 • Ln 42, Col 1
          </div>
        </div>
      </div>
    </div>
  );

  const renderTerminal = () => (
    <div className="h-full bg-white dark:bg-gray-900 flex flex-col">
      {/* Terminal Output */}
      <div
        ref={terminalRef}
        className="flex-1 p-3 font-mono text-xs text-gray-900 dark:text-gray-100 overflow-y-auto"
        style={{ minHeight: "200px" }}
      >
        {terminalOutput.map((line, index) => (
          <div key={index} className="whitespace-pre-wrap">
            {line}
          </div>
        ))}
      </div>

      {/* Terminal Input */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-3">
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-green-600 dark:text-green-400">
            trading@terminal:~$
          </span>
          <input
            type="text"
            value={terminalInput}
            onChange={(e) => setTerminalInput(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1 bg-transparent text-gray-900 dark:text-gray-100 focus:outline-none"
            placeholder="Enter command..."
            autoFocus
          />
        </div>
      </div>
    </div>
  );

  const renderOutput = () => (
    <div className="h-full bg-white dark:bg-gray-900 p-3 font-mono text-xs text-gray-900 dark:text-gray-100">
      <div className="text-green-600 dark:text-green-400 mb-2">
        Script Output:
      </div>
      <div className="text-gray-700 dark:text-gray-300">
        ✓ CustomIndicator initialized successfully
        <br />
        ✓ Period: 20
        <br />
        ✓ Ready for data processing
        <br />
        <br />
        <span className="text-blue-600 dark:text-blue-400">
          Sample calculation results:
        </span>
        <br />
        Data points processed: 1000
        <br />
        Moving average calculated for BTC/USDT
        <br />
        Signal strength: High (0.85)
        <br />
        <br />
        <span className="text-yellow-600 dark:text-yellow-400">
          Indicator registered in database ✓
        </span>
      </div>
    </div>
  );

  const renderProblems = () => (
    <div className="h-full bg-white dark:bg-gray-900 p-3 text-xs">
      <div className="text-green-600 dark:text-green-400 mb-2">
        ✓ No problems detected
      </div>
      <div className="text-gray-600 dark:text-gray-400">
        Your indicator code is syntactically correct and follows best practices.
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case "editor":
        return renderEditor();
      case "terminal":
        return renderTerminal();
      case "output":
        return renderOutput();
      case "problems":
        return renderProblems();
      default:
        return renderEditor();
    }
  };

  return (
    <div className={className}>
      {!isExpanded ? (
        // Minimal collapsed state - just like price data text
        <button
          onClick={() => setIsExpanded(true)}
          className="text-xs text-[#666] dark:text-gray-400 hover:text-[#333] dark:hover:text-gray-200 transition-colors"
        >
          Trading Terminal
        </button>
      ) : (
        // Full expanded terminal
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          {/* Header Bar */}
          <div className="flex items-center justify-between bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsExpanded(false)}
                className="flex items-center gap-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                <ChevronDown size={16} />
                <span className="font-medium">Trading Terminal</span>
              </button>

              <div className="flex items-center">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-2 px-3 py-1 text-sm transition-colors ${
                        activeTab === tab.id
                          ? "text-gray-900 dark:text-white bg-gray-200 dark:bg-gray-700"
                          : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                      }`}
                    >
                      <Icon size={14} />
                      {tab.name}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-1 px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition-colors">
                  <Play size={12} />
                  Run Script
                </button>
                <button className="flex items-center gap-1 px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors">
                  <Save size={12} />
                  Save
                </button>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Ready
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="h-96">{renderContent()}</div>
        </div>
      )}
    </div>
  );
};

export default TradingTerminal;
