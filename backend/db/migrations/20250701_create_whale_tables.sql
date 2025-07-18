CREATE TABLE IF NOT EXISTS whale_events (
    event_id UUID DEFAULT generateUUIDv4(),
    ts DateTime,
    chain String,
    tx_hash String,
    from_addr String,
    to_addr String,
    token String,
    symbol String,
    amount Float64,
    is_native UInt8,
    exchange String,
    amount_usd Float64 DEFAULT 0.0,
    from_exchange String DEFAULT '',
    from_country String DEFAULT '',
    from_city String DEFAULT '',
    to_exchange String DEFAULT '',
    to_country String DEFAULT '',
    to_city String DEFAULT '',
    is_cross_border UInt8 DEFAULT 0,
    source String DEFAULT 'direct_collector',
    created_at DateTime DEFAULT now(),
    
    -- Coin-spezifische Metadaten
    threshold_usd Float64 DEFAULT 0.0,
    coin_rank UInt16 DEFAULT 0,
    
    -- Backfill-Tracking (minimal)
    backfill_block UInt64 DEFAULT 0,
    is_backfill UInt8 DEFAULT 0
)
ENGINE = ReplacingMergeTree()
ORDER BY (ts, chain, symbol)
PARTITION BY toYYYYMM(ts);

CREATE TABLE IF NOT EXISTS coin_config (
    symbol String,
    chain String,
    contract_addr String,
    coingecko_id String,
    decimals UInt8,
    threshold_usd Float64,
    priority UInt8,  -- 1=High, 2=Medium, 3=Low
    active UInt8 DEFAULT 1,
    last_updated DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree()
ORDER BY (symbol, chain);
