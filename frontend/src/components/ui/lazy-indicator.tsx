import React, { useState, useEffect, Suspense } from 'react';

interface LazyIndicatorProps {
  indicatorType: string;
  data: any[];
  isVisible: boolean;
  onLoad?: () => void;
}

// Lazy loading für verschiedene Indikatoren
const IndicatorComponents = {
  rsi: React.lazy(() => import('./indicators/RSIIndicator')),
  macd: React.lazy(() => import('./indicators/MACDIndicator')),
  bollinger: React.lazy(() => import('./indicators/BollingerIndicator')),
  ema: React.lazy(() => import('./indicators/EMAIndicator')),
  sma: React.lazy(() => import('./indicators/SMAIndicator')),
  volume: React.lazy(() => import('./indicators/VolumeIndicator')),
};

const LazyIndicator: React.FC<LazyIndicatorProps> = ({
  indicatorType,
  data,
  isVisible,
  onLoad
}) => {
  const [shouldLoad, setShouldLoad] = useState(false);

  useEffect(() => {
    if (isVisible && !shouldLoad) {
      // Delay loading um Performance zu verbessern
      const timer = setTimeout(() => {
        setShouldLoad(true);
        onLoad?.();
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [isVisible, shouldLoad, onLoad]);

  if (!shouldLoad || !isVisible) {
    return (
      <div className="h-32 bg-gray-100 dark:bg-gray-800 rounded flex items-center justify-center">
        <div className="text-gray-500 dark:text-gray-400 text-sm">
          {shouldLoad ? 'Loading indicator...' : 'Indicator ready to load'}
        </div>
      </div>
    );
  }

  const IndicatorComponent = IndicatorComponents[indicatorType as keyof typeof IndicatorComponents];

  if (!IndicatorComponent) {
    return (
      <div className="h-32 bg-red-50 dark:bg-red-900 rounded flex items-center justify-center">
        <div className="text-red-600 dark:text-red-400 text-sm">
          Unknown indicator: {indicatorType}
        </div>
      </div>
    );
  }

  return (
    <Suspense fallback={
      <div className="h-32 bg-gray-100 dark:bg-gray-800 rounded flex items-center justify-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    }>
      <IndicatorComponent data={data} />
    </Suspense>
  );
};

export default LazyIndicator;