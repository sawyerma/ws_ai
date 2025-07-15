import { useState } from "react";
import IndicatorsModal from "./indicators-modal";

const TimeButtons = ({ onIntervalChange, onIndicatorSelect }: { 
  onIntervalChange?: (interval: string) => void;
  onIndicatorSelect?: (indicator: string) => void;
}) => {
  const [activeTime, setActiveTime] = useState("1m");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedIntervals, setSelectedIntervals] = useState(
    new Set(["1s", "5s", "15s", "1m", "1h"]),
  );
  const [isIndicatorsModalOpen, setIsIndicatorsModalOpen] = useState(false);
  const [isGridView, setIsGridView] = useState(false);

  const displayIntervals = Array.from(selectedIntervals);

  const allIntervals = [
    { label: "1s", value: "1s" },
    { label: "5s", value: "5s" },
    { label: "10s", value: "10s" },
    { label: "15s", value: "15s" },
    { label: "30s", value: "30s" },
    { label: "1m", value: "1m" },
    { label: "2m", value: "2m" },
    { label: "5m", value: "5m" },
    { label: "10m", value: "10m" },
    { label: "15m", value: "15m" },
    { label: "30m", value: "30m" },
    { label: "1h", value: "1h" },
    { label: "2h", value: "2h" },
    { label: "4h", value: "4h" },
    { label: "6h", value: "6h" },
    { label: "12h", value: "12h" },
    { label: "1d", value: "1d" },
    { label: "1w", value: "1w" },
    { label: "1M", value: "1M" },
    { label: "6M", value: "6M" },
  ];

  const handleTimeSelect = (interval: string) => {
    setActiveTime(interval);
    setIsDropdownOpen(false);
    
    // Callback an Parent-Komponente
    if (onIntervalChange) {
      onIntervalChange(interval);
    }
  };

  const handleEditToggle = () => {
    setIsEditMode(!isEditMode);
  };

  const handleIntervalToggle = (interval: string) => {
    const newSelected = new Set(selectedIntervals);
    if (newSelected.has(interval)) {
      newSelected.delete(interval);
    } else {
      newSelected.add(interval);
    }
    setSelectedIntervals(newSelected);
  };

  const handleSave = () => {
    setIsEditMode(false);
    // Optional: callback to parent component
  };

  const handleIndicatorSelect = (indicator: string) => {
    if (onIndicatorSelect) {
      onIndicatorSelect(indicator);
    }
  };

  return (
    <div className="flex items-center gap-3 my-3 text-sm">
      <label className="font-medium text-[#444] dark:text-gray-300 mr-2">
        Zeit
      </label>

      {/* Display Buttons */}
      {displayIntervals.map((interval) => (
        <div
          key={interval}
          className={`cursor-pointer select-none ${
            activeTime === interval
              ? "bg-[#1a48d8] text-white"
              : "bg-gray-100 dark:bg-gray-700 text-[#222] dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600"
          }`}
          style={{
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "12.8px",
            border: "none",
            outline: "none",
            boxShadow: "none",
            borderWidth: "0",
            borderStyle: "none",
            borderColor: "transparent",
          }}
          onClick={() => handleTimeSelect(interval)}
        >
          {interval}
        </div>
      ))}

      {/* Dropdown Button */}
      <div className="relative">
        <div
          className="bg-gray-100 dark:bg-gray-700 text-[#222] dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600 cursor-pointer select-none"
          style={{
            padding: "2px 8px",
            borderRadius: "4px",
            display: "flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "12.8px",
            border: "none",
            outline: "none",
            boxShadow: "none",
            borderWidth: "0",
            borderStyle: "none",
            borderColor: "transparent",
          }}
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        >
          ▽
        </div>

        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div className="absolute top-full right-0 mt-1 z-50 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-xl">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Intervall auswählen
                </h3>
                <button
                  className="text-blue-500 text-sm font-medium"
                  onClick={isEditMode ? handleSave : handleEditToggle}
                >
                  {isEditMode ? "Speichern" : "Bearbeiten"}
                </button>
              </div>

              {/* Grid of time intervals */}
              <div className="grid grid-cols-4 gap-2">
                {allIntervals.map((interval) => (
                  <div
                    key={interval.value}
                    className={`h-10 rounded text-sm font-medium transition-colors relative flex items-center justify-center cursor-pointer ${
                      activeTime === interval.value && !isEditMode
                        ? "bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600"
                    }`}
                    onClick={() =>
                      isEditMode
                        ? handleIntervalToggle(interval.value)
                        : handleTimeSelect(interval.value)
                    }
                  >
                    {interval.label}

                    {/* Checkbox in edit mode */}
                    {isEditMode && (
                      <div className="absolute top-1 right-1">
                        <div
                          className={`w-4 h-4 rounded-full flex items-center justify-center text-xs ${
                            selectedIntervals.has(interval.value)
                              ? "bg-blue-500 text-white"
                              : "bg-gray-300 text-gray-600"
                          }`}
                        >
                          {selectedIntervals.has(interval.value) ? "✓" : ""}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Overlay to close dropdown */}
        {isDropdownOpen && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsDropdownOpen(false)}
          />
        )}
      </div>

      {/* Separator */}
      <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2"></div>

      {/* Indicators Button */}
      <div
        className="bg-gray-100 dark:bg-gray-700 text-[#222] dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600 cursor-pointer select-none flex items-center gap-2"
        style={{
          padding: "4px 12px",
          borderRadius: "4px",
          fontSize: "12.8px",
          border: "none",
          outline: "none",
          boxShadow: "none",
          borderWidth: "0",
          borderStyle: "none",
          borderColor: "transparent",
        }}
        onClick={() => setIsIndicatorsModalOpen(true)}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 14 14"
          fill="none"
          className="opacity-80"
        >
          <path
            d="M2 12L5 9L8 11L12 7"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M12 4V7H9"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span>
          <p>Indikatoren</p>
        </span>
      </div>

      {/* Grid View Button */}
      <div
        className={`cursor-pointer select-none flex items-center justify-center ${
          isGridView
            ? "bg-[#1a48d8] text-white"
            : "bg-gray-100 dark:bg-gray-700 text-[#222] dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600"
        }`}
        style={{
          padding: "4px 8px",
          borderRadius: "4px",
          fontSize: "12.8px",
          border: "none",
          outline: "none",
          boxShadow: "none",
          borderWidth: "0",
          borderStyle: "none",
          borderColor: "transparent",
          width: "28px",
          height: "24px",
        }}
        onClick={() => setIsGridView(!isGridView)}
        title="Grid View"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <rect
            x="1"
            y="1"
            width="5"
            height="5"
            rx="1"
            stroke="currentColor"
            strokeWidth="1.2"
            fill="none"
          />
          <rect
            x="8"
            y="1"
            width="5"
            height="5"
            rx="1"
            stroke="currentColor"
            strokeWidth="1.2"
            fill="none"
          />
          <rect
            x="1"
            y="8"
            width="5"
            height="5"
            rx="1"
            stroke="currentColor"
            strokeWidth="1.2"
            fill="none"
          />
          <rect
            x="8"
            y="8"
            width="5"
            height="5"
            rx="1"
            stroke="currentColor"
            strokeWidth="1.2"
            fill="none"
          />
        </svg>
      </div>

      {/* Alarm Button */}
      <div
        className="bg-gray-100 dark:bg-gray-700 text-[#222] dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600 cursor-pointer select-none flex items-center gap-2"
        style={{
          padding: "4px 12px",
          borderRadius: "4px",
          fontSize: "12.8px",
          border: "none",
          outline: "none",
          boxShadow: "none",
          borderWidth: "0",
          borderStyle: "none",
          borderColor: "transparent",
        }}
        onClick={() => {
          // Handle alarm functionality
          console.log("Alarm clicked");
        }}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 14 14"
          fill="none"
          className="opacity-80"
        >
          <path
            d="M7 13C10.3137 13 13 10.3137 13 7C13 3.68629 10.3137 1 7 1C3.68629 1 1 3.68629 1 7C1 10.3137 3.68629 13 7 13Z"
            stroke="currentColor"
            strokeWidth="1.2"
            fill="none"
          />
          <path
            d="M7 4V7L9 9"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
        </svg>
        Alarm
      </div>

      {/* Indicators Modal */}
      <IndicatorsModal
        isOpen={isIndicatorsModalOpen}
        onClose={() => setIsIndicatorsModalOpen(false)}
        onIndicatorSelect={handleIndicatorSelect}
      />
    </div>
  );
};

export default TimeButtons;