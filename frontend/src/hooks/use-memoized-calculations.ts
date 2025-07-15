import { useMemo } from 'react';

interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TradeData {
  price: number;
  size: number;
  side: 'buy' | 'sell';
  time: string;
}

export function useMemoizedAggregations(candles: CandleData[]) {
  return useMemo(() => {
    if (!candles.length) return null;

    const prices = candles.map(c => c.close);
    const volumes = candles.map(c => c.volume);
    
    const high24h = Math.max(...candles.map(c => c.high));
    const low24h = Math.min(...candles.map(c => c.low));
    const volume24h = volumes.reduce((sum, vol) => sum + vol, 0);
    
    const firstPrice = candles[0]?.close || 0;
    const lastPrice = candles[candles.length - 1]?.close || 0;
    const change24h = lastPrice - firstPrice;
    const changePercent = firstPrice > 0 ? (change24h / firstPrice) * 100 : 0;

    // Simple Moving Average (last 20 periods)
    const sma20 = prices.length >= 20 
      ? prices.slice(-20).reduce((sum, price) => sum + price, 0) / 20
      : null;

    // Volume Weighted Average Price
    const vwap = candles.length > 0
      ? candles.reduce((sum, candle) => sum + (candle.close * candle.volume), 0) / volume24h
      : null;

    return {
      high24h,
      low24h,
      volume24h,
      change24h,
      changePercent,
      sma20,
      vwap,
      candleCount: candles.length
    };
  }, [candles]);
}

export function useMemoizedTradeStats(trades: TradeData[]) {
  return useMemo(() => {
    if (!trades.length) return null;

    const buyTrades = trades.filter(t => t.side === 'buy');
    const sellTrades = trades.filter(t => t.side === 'sell');
    
    const buyVolume = buyTrades.reduce((sum, trade) => sum + trade.size, 0);
    const sellVolume = sellTrades.reduce((sum, trade) => sum + trade.size, 0);
    const totalVolume = buyVolume + sellVolume;
    
    const buyPressure = totalVolume > 0 ? (buyVolume / totalVolume) * 100 : 50;
    
    const avgPrice = trades.length > 0
      ? trades.reduce((sum, trade) => sum + trade.price, 0) / trades.length
      : 0;

    return {
      totalTrades: trades.length,
      buyTrades: buyTrades.length,
      sellTrades: sellTrades.length,
      buyVolume,
      sellVolume,
      totalVolume,
      buyPressure,
      avgPrice
    };
  }, [trades]);
}