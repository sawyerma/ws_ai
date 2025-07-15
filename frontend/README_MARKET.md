# Market Dashboard Documentation

This document provides a comprehensive guide to the Market Dashboard application, explaining all components, variables, and interaction points.

## Table of Contents

1. [Overview](#overview)
2. [Main Components](#main-components)
3. [Navigation & Layout](#navigation--layout)
4. [Chart & Trading Components](#chart--trading-components)
5. [Settings & Configuration](#settings--configuration)
6. [Whale Tracker](#whale-tracker)
7. [Data Structure & API](#data-structure--api)

## Overview

The Market Dashboard is a comprehensive trading interface with real-time data visualization, market analysis, and trading tools. The application is built with React, TypeScript, and Tailwind CSS.

## Main Components

### App Structure

- **App.tsx**: Main application container that sets up routing and providers
- **Index.tsx**: Main trading dashboard page
- **Database.tsx**: Database management interface
- **AI.tsx**: AI analysis tools
- **ML.tsx**: Machine learning models
- **Whales.tsx**: Whale transaction tracker
- **News.tsx**: Crypto news aggregator
- **TradingBot.tsx**: Automated trading interface

## Navigation & Layout

### Trading Navigation (`src/components/ui/trading-nav.tsx`)

The main navigation component that allows switching between different views:

- **Trading Mode Selection**: 
  - Variable: `tradingMode` 
  - Options: "Spot", "USDT-M Futures", "Coin-M Perpetual-Futures", "Coin-M Delivery-Futures", "USDC-M Futures"
  - Function: `onTradingModeChange` callback when a mode is selected

- **View Navigation**:
  - Variable: `viewMode`
  - Options: "trading", "database", "ai", "ml", "whales", "news", "bot"
  - Function: `onViewChange` callback when a view is selected

### Coin Selector (`src/components/ui/advanced-coin-selector.tsx`)

Dropdown for selecting trading pairs:

- **Variables**:
  - `selectedSymbol`: Currently selected trading pair (e.g., "BTC/USDT")
  - `onSymbolSelect`: Callback function when a symbol is selected, passes `symbol` and `market`
  - `onSettingsClick`: Opens the coin settings modal

- **Features**:
  - Search functionality via `searchTerm` state
  - Favorites toggling via `favorites` state (stored in localStorage as 'coin-favorites')
  - Price and change display for each coin
  - Live status indicators

### Price Display (`src/components/ui/price-display.tsx`)

Shows current price and market data:

- **Variables**:
  - `currentCoinData`: Object containing current coin information
    - `symbol`: Trading pair (e.g., "BTC/USDT")
    - `price`: Current price
    - `change`: Price change (e.g., "+1.20%")
    - `changePercent`: Numeric change percentage
  - `marketData`: Object containing market statistics
    - `change24h`: 24-hour change percentage
    - `high24h`: 24-hour high price
    - `low24h`: 24-hour low price
    - `volume24h`: 24-hour volume
    - `turnover24h`: 24-hour turnover
    - `category`: Coin category
  - `tradingMode`: Current trading mode (e.g., "Spot")

## Chart & Trading Components

### Time Buttons (`src/components/ui/time-buttons.tsx`)

Controls chart timeframe:

- **Variables**:
  - `onIntervalChange`: Callback when interval is changed
  - `onIndicatorSelect`: Callback when an indicator is selected

- **Features**:
  - Time interval selection (1s, 5s, 15s, 1m, 1h, etc.)
  - Indicators modal access
  - Grid view toggle

### Chart Section (`src/components/ui/chart-section.tsx`)

Main chart display area:

- **Variables**:
  - `selectedCoin`: Current trading pair
  - `selectedMarket`: Current market type
  - `selectedInterval`: Current time interval
  - `selectedIndicators`: Array of active indicators
  - `onIndicatorRemove`: Callback to remove an indicator

- **Components**:
  - `TradingChart`: Main price chart
  - `Orderbook`: Order book display
  - `TradingTerminal`: Trading interface

### Chart View (`src/components/ChartView.jsx`)

The actual chart implementation:

- **Variables**:
  - `wsUrl`: WebSocket URL for real-time data
  - `symbol`: Trading pair
  - `market`: Market type
  - `interval`: Time interval
  - `width`: Chart width
  - `height`: Chart height

- **Features**:
  - Real-time price updates via WebSocket
  - Candlestick chart with customizable appearance
  - Volume display option
  - Technical indicators

### Orderbook (`src/components/OrderBook.jsx`)

Displays market depth:

- **Variables**:
  - `symbol`: Trading pair
  - `market`: Market type
  - `apiBase`: API endpoint base URL
  - `limit`: Number of orders to display

- **Features**:
  - Bid and ask orders
  - Price and size display
  - Visual depth representation

### Market Trades (`src/components/MarketTrades.jsx`)

Shows recent trades:

- **Variables**:
  - `symbol`: Trading pair
  - `market`: Market type
  - `wsBase`: WebSocket base URL
  - `maxLength`: Maximum number of trades to display

- **Features**:
  - Real-time trade updates
  - Buy/sell indicators
  - Time, price, and amount display

## Settings & Configuration

### Coin Settings Modal (`src/components/ui/coin-settings-modal.tsx`)

Configure data collection for symbols:

- **Variables**:
  - `isOpen`: Controls modal visibility
  - `onClose`: Callback when modal is closed
  - `selectedSymbol`: Currently selected symbol
  - `selectedMarket`: Currently selected market

- **Features**:
  - Enable/disable live data collection via `store_live` toggle
  - Enable/disable historical data loading via `load_history` toggle
  - Set historical data cutoff date via `history_until` field
  - API rate limit configuration via `rateLimit` state

- **Data Structure**:
  ```typescript
  interface CoinSetting {
    symbol: string;
    market: string;
    store_live: boolean;
    load_history: boolean;
    history_until?: string;
    favorite: boolean;
    chart_resolution?: string;
  }
  ```

### Settings Modal (`src/components/ui/settings-modal.tsx`)

General application settings:

- **Variables**:
  - `isOpen`: Controls modal visibility
  - `onClose`: Callback when modal is closed

- **Features**:
  - Chart appearance customization
  - Theme settings
  - Indicator display preferences
  - Grid and scale options

## Whale Tracker

The Whale Tracker (`src/pages/Whales.tsx`) monitors large transactions on various exchanges.

### Main Components

- **Filters**:
  - `timeFilter`: Time range filter (1h, 6h, 24h, 7d)
  - `symbolFilter`: Coin filter (All, BTC, ETH, etc.)
  - `exchangeFilter`: Exchange filter (All, Coinbase, Binance, etc.)
  - `tradeFilter`: Trade type filter (All, Buy Only, Sell Only)

- **Transaction Table**:
  - Sortable by any column via `sortField` and `sortDirection`
  - Favorite coins can be toggled and filtered

- **Chart Visualization**:
  - Shows buy/sell volume over time
  - Data structure: `{ time: string; buy: number; sell: number }`

### Whale Transaction Data Structure

```typescript
interface WhaleTransaction {
  id: number;
  coin: string;         // e.g., "BTC-USD"
  exchange: string;     // e.g., "Coinbase Pro"
  quantity: string;     // e.g., "2.00000 BTC"
  total: string;        // e.g., "236,686.00 USD"
  side: "BUY" | "SELL";
  date: string;         // e.g., "2024-01-19"
  time: string;         // e.g., "14:23:45"
  marketcap: string;    // e.g., "$2.1T"
  maker: string;        // Wallet address
  timestamp: number;    // Unix timestamp
}
```

### Interaction Points

- **Favorite Toggling**:
  - Function: `toggleCoinSelection(coin: string)`
  - State: `favoriteCoins` (Set<string>)

- **Sorting**:
  - Function: `handleSort(field: keyof WhaleTransaction)`
  - States: `sortField` and `sortDirection`

- **Filtering**:
  - Dropdown selectors for time, symbol, exchange, and trade type
  - Search input for text-based filtering

## Data Structure & API

### Symbol Data (`src/api/symbols.ts`)

- **API Endpoints**:
  - `/symbols`: Get all available symbols
  - `/ticker`: Get current prices
  - `/settings`: Get/save symbol settings
  - `/ohlc`: Get historical candlestick data
  - `/orderbook`: Get order book data

- **Data Structures**:
  ```typescript
  // Symbol data
  interface ApiSymbol {
    symbol: string;
    market: string;
    price: string;
    change: string;
    changePercent: number;
  }

  // Symbol settings
  interface CoinSetting {
    symbol: string;
    market: string;
    store_live: boolean;
    load_history: boolean;
    history_until?: string;
    favorite: boolean;
    db_resolution?: number;
    chart_resolution?: string;
  }
  ```

### WebSocket Connections

- **Endpoints**:
  - `ws://{host}/ws/{symbol}/{market}`: Price data
  - `ws://{host}/ws/{symbol}/{market}/trades`: Trade data

- **Message Types**:
  - `candle`: Candlestick updates
  - `trade`: Individual trade updates

## Component Relationships

1. **Index.tsx** (Main Page)
   - Contains `TradingNav` for navigation
   - Contains `AdvancedCoinSelector` for symbol selection
   - Contains `PriceDisplay` for price information
   - Contains `TimeButtons` for interval selection
   - Contains `ChartSection` for chart display
   - Contains `CoinSettingsModal` for settings

2. **ChartSection**
   - Contains `TradingChart` for price visualization
   - Contains `Orderbook` for market depth
   - Contains `TradingTerminal` for trading interface

3. **TradingChart**
   - Contains `ChartView` for the actual chart
   - Contains `IndicatorSettingsModal` for indicator configuration

## How to Access Key Features

1. **Change Trading Mode**:
   - Click on "Market" in the top navigation
   - Select desired mode from dropdown

2. **Select Trading Pair**:
   - Click on the current symbol (e.g., "BTC/USDT")
   - Search or select from the dropdown

3. **Configure Symbol Settings**:
   - Click the settings icon in the coin selector
   - Toggle live/historic data collection
   - Set historical data cutoff date

4. **Change Chart Timeframe**:
   - Click on time buttons (1m, 5m, 1h, etc.)
   - Click dropdown for more options

5. **Add Technical Indicators**:
   - Click "Indicators" button
   - Select indicator from the modal

6. **Access Whale Tracker**:
   - Click "Whales" in the top navigation
   - Use filters to customize the view
   - Click column headers to sort
   - Click star icon to favorite coins

## File to Component Mapping

- **src/App.tsx**: Main application container
- **src/pages/Index.tsx**: Main trading dashboard
- **src/pages/Database.tsx**: Database management interface
- **src/pages/Whales.tsx**: Whale transaction tracker
- **src/components/ui/advanced-coin-selector.tsx**: Trading pair selector
- **src/components/ui/coin-settings-modal.tsx**: Symbol settings configuration
- **src/components/ui/trading-nav.tsx**: Main navigation
- **src/components/ui/price-display.tsx**: Current price display
- **src/components/ui/time-buttons.tsx**: Timeframe selector
- **src/components/ui/chart-section.tsx**: Chart container
- **src/components/ui/trading-chart.tsx**: Chart with indicators
- **src/components/ChartView.jsx**: Actual chart implementation
- **src/components/OrderBook.jsx**: Order book display
- **src/components/MarketTrades.jsx**: Recent trades display
- **src/api/symbols.ts**: API functions for symbol data