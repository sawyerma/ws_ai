import { useState } from "react";
import ThemeProvider from "../components/ui/theme-provider";
import ThemeToggle from "../components/ui/theme-toggle";

interface MLProps {
  onBackToTrading?: () => void;
}

const ML = ({ onBackToTrading }: MLProps = {}) => {
  const [activeAlgorithm, setActiveAlgorithm] = useState("regression");

  const sidebarItems = [
    { id: "regression", name: "Linear Regression", icon: "📈" },
    { id: "classification", name: "Classification", icon: "🏷️" },
    { id: "clustering", name: "Clustering", icon: "🔗" },
    { id: "neural", name: "Neural Networks", icon: "🧠" },
    { id: "random-forest", name: "Random Forest", icon: "🌳" },
    { id: "svm", name: "Support Vector Machine", icon: "⚙️" },
    { id: "lstm", name: "LSTM Networks", icon: "🔄" },
    { id: "ensemble", name: "Ensemble Methods", icon: "🎭" },
  ];

  const renderContent = () => (
    <div className="flex-1 p-6">
      <div className="text-center py-20">
        <div className="text-6xl mb-4">🧠</div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Machine Learning Lab
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
          Advanced machine learning algorithms for trading analysis
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          <div className="bg-indigo-50 dark:bg-indigo-900 p-4 rounded-lg">
            <div className="text-2xl mb-2">📈</div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Regression
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Price trend analysis
            </p>
          </div>
          <div className="bg-pink-50 dark:bg-pink-900 p-4 rounded-lg">
            <div className="text-2xl mb-2">🏷️</div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Classification
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Market state detection
            </p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900 p-4 rounded-lg">
            <div className="text-2xl mb-2">🧠</div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Neural Networks
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Deep learning models
            </p>
          </div>
          <div className="bg-teal-50 dark:bg-teal-900 p-4 rounded-lg">
            <div className="text-2xl mb-2">🔄</div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              LSTM
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Time series prediction
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <ThemeProvider>
      <div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white min-h-screen font-['Inter']">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              {onBackToTrading && (
                <button
                  onClick={onBackToTrading}
                  className="px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center gap-2"
                >
                  ← Back to Trading
                </button>
              )}
              <h1 className="text-2xl font-bold">Machine Learning</h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200">
                Deep Learning
              </span>
            </div>
            <div className="flex items-center gap-4">
              <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                Train Algorithm
              </button>
              <ThemeToggle />
            </div>
          </div>
        </div>

        <div className="flex h-[calc(100vh-73px)]">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
                ML Algorithms
              </h3>
              <nav className="space-y-1">
                {sidebarItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveAlgorithm(item.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeAlgorithm === item.id
                        ? "bg-purple-600 text-white"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                    }`}
                  >
                    <span className="mr-3">{item.icon}</span>
                    {item.name}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          {renderContent()}
        </div>
      </div>
    </ThemeProvider>
  );
};

export default ML;
