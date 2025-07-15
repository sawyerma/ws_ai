import React, { useMemo, useCallback } from 'react';
import { VirtualizedList } from './virtualized-list';
import { useMemoizedTradeStats } from '../../hooks/use-memoized-calculations';
import { useDebouncedCallback } from '../../hooks/use-debounce';

interface Trade {
  id: string;
  price: number;
  size: number;
  side: 'buy' | 'sell';
  time: string;
  ts: string;
}

interface OptimizedTradesListProps {
  trades: Trade[];
  onTradeClick?: (trade: Trade) => void;
}

const OptimizedTradesList: React.FC<OptimizedTradesListProps> = ({
  trades,
  onTradeClick
}) => {
  // Memoized trade statistics
  const tradeStats = useMemoizedTradeStats(trades);

  // Debounced click handler
  const debouncedTradeClick = useDebouncedCallback((trade: Trade) => {
    onTradeClick?.(trade);
  }, 100);

  // Memoized render function für Trade-Einträge
  const renderTradeEntry = useCallback((trade: Trade, index: number) => {
    return (
      <div
        key={trade.id}
        className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        onClick={() => debouncedTradeClick(trade)}
      >
        <div className="grid grid-cols-3 text-xs py-1 px-4">
          <div className={`font-medium flex items-center ${
            trade.side === 'buy' ? 'text-green-500' : 'text-red-500'
          }`}>
            <span>{trade.price.toFixed(2)}</span>
            <span className="ml-1 text-xs">
              {trade.side === 'buy' ? '↑' : '↓'}
            </span>
          </div>
          <div className="text-center text-gray-600 dark:text-white font-medium">
            {trade.size.toFixed(6)}
          </div>
          <div className="text-right text-gray-600 dark:text-white text-xs font-medium">
            {new Date(trade.ts).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  }, [debouncedTradeClick]);

  return (
    <div className="h-full flex flex-col">
      {/* Trade Statistics Header */}
      {tradeStats && (
        <div className="p-2 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
          <div className="grid grid-cols-3 text-xs text-gray-600 dark:text-gray-400">
            <div>Total: {tradeStats.totalTrades}</div>
            <div>Buy: {tradeStats.buyPressure.toFixed(1)}%</div>
            <div>Avg: {tradeStats.avgPrice.toFixed(2)}</div>
          </div>
        </div>
      )}

      {/* Virtualized Trades List */}
      <div className="flex-1">
        <VirtualizedList
          items={trades}
          itemHeight={24}
          containerHeight={300}
          renderItem={renderTradeEntry}
          overscan={10}
        />
      </div>
    </div>
  );
};

export default OptimizedTradesList;