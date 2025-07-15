-- Trading strategies table
CREATE TABLE IF NOT EXISTS trading_strategies (
    id String CODEC(ZSTD),
    name String CODEC(ZSTD),
    symbol String CODEC(ZSTD),
    strategy_type String CODEC(ZSTD),
    min_price Float64 CODEC(Gorilla),
    max_price Float64 CODEC(Gorilla),
    grid_levels UInt16 CODEC(ZSTD),
    quantity_per_level Float64 CODEC(Gorilla),
    spread_percentage Float64 CODEC(Gorilla),
    active UInt8 CODEC(ZSTD),
    created_at DateTime64(3) CODEC(DoubleDelta),
    updated_at DateTime64(3) CODEC(DoubleDelta),
    total_pnl Float64 CODEC(Gorilla),
    config String CODEC(ZSTD)  -- JSON config
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY id
SETTINGS index_granularity = 8192;

-- Trading orders table
CREATE TABLE IF NOT EXISTS trading_orders (
    id String CODEC(ZSTD),
    strategy_id String CODEC(ZSTD),
    symbol String CODEC(ZSTD),
    side Enum8('buy' = 1, 'sell' = 2) CODEC(ZSTD),
    order_type Enum8('market' = 1, 'limit' = 2, 'stop' = 3) CODEC(ZSTD),
    quantity Float64 CODEC(Gorilla),
    price Float64 CODEC(Gorilla),
    filled_quantity Float64 CODEC(Gorilla),
    status Enum8('pending' = 1, 'filled' = 2, 'cancelled' = 3, 'rejected' = 4) CODEC(ZSTD),
    exchange_order_id String CODEC(ZSTD),
    created_at DateTime64(3) CODEC(DoubleDelta),
    filled_at Nullable(DateTime64(3)) CODEC(DoubleDelta),
    commission Float64 CODEC(Gorilla)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (strategy_id, created_at)
SETTINGS index_granularity = 8192;

-- Trading positions table
CREATE TABLE IF NOT EXISTS trading_positions (
    id String CODEC(ZSTD),
    strategy_id String CODEC(ZSTD),
    symbol String CODEC(ZSTD),
    side Enum8('long' = 1, 'short' = 2) CODEC(ZSTD),
    size Float64 CODEC(Gorilla),
    entry_price Float64 CODEC(Gorilla),
    current_price Float64 CODEC(Gorilla),
    unrealized_pnl Float64 CODEC(Gorilla),
    realized_pnl Float64 CODEC(Gorilla),
    opened_at DateTime64(3) CODEC(DoubleDelta),
    updated_at DateTime64(3) CODEC(DoubleDelta)
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (strategy_id, symbol)
SETTINGS index_granularity = 8192;

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    strategy_id String CODEC(ZSTD),
    timestamp DateTime64(3) CODEC(DoubleDelta),
    total_pnl Float64 CODEC(Gorilla),
    unrealized_pnl Float64 CODEC(Gorilla),
    realized_pnl Float64 CODEC(Gorilla),
    drawdown Float64 CODEC(Gorilla),
    win_rate Float64 CODEC(Gorilla),
    sharpe_ratio Float64 CODEC(Gorilla),
    total_trades UInt32 CODEC(ZSTD),
    winning_trades UInt32 CODEC(ZSTD)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (strategy_id, timestamp)
SETTINGS index_granularity = 8192;

-- Risk alerts table
CREATE TABLE IF NOT EXISTS risk_alerts (
    id String CODEC(ZSTD),
    strategy_id String CODEC(ZSTD),
    alert_type String CODEC(ZSTD),
    severity Enum8('low' = 1, 'medium' = 2, 'high' = 3, 'critical' = 4) CODEC(ZSTD),
    message String CODEC(ZSTD),
    current_value Float64 CODEC(Gorilla),
    threshold_value Float64 CODEC(Gorilla),
    acknowledged UInt8 CODEC(ZSTD),
    created_at DateTime64(3) CODEC(DoubleDelta),
    acknowledged_at Nullable(DateTime64(3)) CODEC(DoubleDelta)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (strategy_id, created_at)
SETTINGS index_granularity = 8192;

-- Create materialized views for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_strategy_performance
ENGINE = AggregatingMergeTree()
ORDER BY (strategy_id, hour)
AS
SELECT
    strategy_id,
    toStartOfHour(timestamp) AS hour,
    max(total_pnl) AS max_pnl,
    min(total_pnl) AS min_pnl,
    argMax(total_pnl, timestamp) AS latest_pnl,
    avg(total_pnl) AS avg_pnl
FROM performance_metrics
GROUP BY strategy_id, hour;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trading_orders_status ON trading_orders (status) TYPE set(0) GRANULARITY 8192;
CREATE INDEX IF NOT EXISTS idx_trading_positions_pnl ON trading_positions (unrealized_pnl) TYPE minmax GRANULARITY 8192;
CREATE INDEX IF NOT EXISTS idx_performance_pnl ON performance_metrics (total_pnl) TYPE minmax GRANULARITY 8192;
CREATE INDEX IF NOT EXISTS idx_risk_alerts_severity ON risk_alerts (severity) TYPE set(0) GRANULARITY 8192;
