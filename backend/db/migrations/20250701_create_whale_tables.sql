-- Table: coins
CREATE TABLE IF NOT EXISTS coins (
    symbol        String,
    chain         String,
    contract_addr String,
    is_native     UInt8,
    exchange      String,   -- "bitget", "none", "binance", etc.
    active        UInt8
)
ENGINE = MergeTree()
ORDER BY (symbol, chain, contract_addr);

-- Table: whale_events
CREATE TABLE IF NOT EXISTS whale_events (
    event_id     UUID,
    ts           DateTime,
    chain        String,
    tx_hash      String,
    from_addr    String,
    to_addr      String,
    token        String,
    symbol       String,
    amount       Float64,
    is_native    UInt8,
    exchange     String    -- "bitget", "none", "binance", etc.
)
ENGINE = MergeTree()
ORDER BY (ts, symbol, exchange);
