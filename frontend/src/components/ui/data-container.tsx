import { useState, useEffect } from "react";

interface DataContainerProps {
  children: React.ReactNode;
  className?: string;
}

const DataContainer = ({ children, className = "" }: DataContainerProps) => {
  return (
    <div
      className={`h-full overflow-y-auto ${className}`}
      style={{
        fontFamily: "'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'",
      }}
    >
      {children}
    </div>
  );
};

// Individual row component for easy data injection
interface DataRowProps {
  data: {
    col1: string | number;
    col2: string | number;
    col3: string | number;
    col1Color?: string;
    col2Color?: string;
    col3Color?: string;
    arrow?: "up" | "down" | null;
    backgroundColor?: string;
    volumeWidth?: number; // For orderbook volume bars
  };
  onClick?: () => void;
  layout?: "orderbook" | "trades";
}

export const DataRow = ({ data, onClick, layout = "trades" }: DataRowProps) => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    // Check initial dark mode state
    const checkDarkMode = () => {
      setIsDarkMode(document.documentElement.classList.contains("dark"));
    };

    // Check on mount
    checkDarkMode();

    // Create observer to watch for class changes
    const observer = new MutationObserver(checkDarkMode);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div
      className="relative cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
      onClick={onClick}
      style={{
        fontFamily: "'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'",
      }}
    >
      {/* Volume background for orderbook */}
      {layout === "orderbook" && data.volumeWidth && (
        <div
          className={`absolute right-0 top-0 h-full ${data.backgroundColor || "bg-gray-100"}`}
          style={{ width: `${data.volumeWidth}%` }}
        ></div>
      )}

      {/* Data Row */}
      <div className="relative grid grid-cols-3 text-xs py-1 px-4">
        <div
          className="font-medium"
          style={{
            color: data.col1Color?.includes("green")
              ? "#10b981"
              : data.col1Color?.includes("red")
                ? "#ef4444"
                : isDarkMode
                  ? "#ffffff"
                  : "#4b5563",
          }}
        >
          {layout === "trades" && data.arrow && (
            <span className="flex items-center">
              <span>{data.col1}</span>
              <span className="ml-1 text-xs">
                {data.arrow === "up" ? "↑" : "↓"}
              </span>
            </span>
          )}
          {(layout === "orderbook" || !data.arrow) && <span>{data.col1}</span>}
        </div>
        <div
          className="text-center font-medium"
          style={{ color: isDarkMode ? "#ffffff" : "#4b5563" }}
        >
          {data.col2}
        </div>
        <div
          className={`text-right ${layout === "orderbook" ? "font-medium" : "text-xs font-medium"}`}
          style={{ color: isDarkMode ? "#ffffff" : "#4b5563" }}
        >
          {data.col3}
        </div>
      </div>
    </div>
  );
};

export default DataContainer;
