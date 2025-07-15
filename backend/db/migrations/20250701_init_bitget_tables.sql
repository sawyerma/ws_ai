-- Table: coin_settings
CREATE TABLE IF NOT EXISTS coin_settings (
    symbol           String,
    market           String,
    store_live       UInt8,
    load_history     UInt8,
    history_until    Nullable(DateTime),
    favorite         UInt8,
    db_resolution    UInt16,
    chart_resolution String,
    updated_at       DateTime
)
ENGINE = MergeTree()
ORDER BY (symbol, market);


-- Table: trades
CREATE TABLE IF NOT EXISTS trades (
    symbol   String,
    market   String,
    price    Float64,
    size     Float64,
    side     String,
    ts       DateTime
)
ENGINE = MergeTree()
ORDER BY (symbol, market, ts);

-- Table: bars
CREATE TABLE IF NOT EXISTS bars (
    symbol   String,
    market   String,
    open     Float64,
    high     Float64,
    low      Float64,
    close    Float64,
    volume   Float64,
    ts       DateTime
)
ENGINE = MergeTree()
ORDER BY (symbol, market, ts);
