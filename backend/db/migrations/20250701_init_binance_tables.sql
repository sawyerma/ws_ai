-- Binance-spezifische Tabellen
CREATE TABLE IF NOT EXISTS binance_coin_settings (
    symbol           LowCardinality(String),
    market           LowCardinality(String),
    store_live       UInt8 DEFAULT 1,
    load_history     UInt8 DEFAULT 1,
    history_until    Nullable(DateTime64(3, 'UTC')),
    favorite         UInt8 DEFAULT 0,
    db_resolutions   Array(UInt16) DEFAULT [60, 300, 900],
    chart_resolution UInt16 DEFAULT 60,
    updated_at       DateTime64(3, 'UTC') DEFAULT now64(3),
    _version UInt64 DEFAULT toUnixTimestamp64Nano(now64(9))
ENGINE = ReplacingMergeTree(_version)
ORDER BY (symbol, market)
PRIMARY KEY (symbol, market)
SETTINGS index_granularity = 128;

CREATE TABLE IF NOT EXISTS binance_trades (
    trade_id String,
    symbol   LowCardinality(String),
    market   LowCardinality(String),
    price    Float64 CODEC(Gorilla, LZ4),
    size     Float32 CODEC(Gorilla, LZ4),
    side     Enum8('buy' = 1, 'sell' = 2),
    ts       DateTime64(3, 'UTC') CODEC(Delta, LZ4),
    _shard_key UInt32 DEFAULT cityHash64(trade_id)
ENGINE = ReplacingMergeTree()
ORDER BY (symbol, market, toStartOfMinute(ts), trade_id)
PARTITION BY toYYYYMM(ts)
TTL ts + INTERVAL 6 MONTH
SETTINGS index_granularity = 1024, min_bytes_for_wide_part = 10000000;

CREATE TABLE IF NOT EXISTS binance_bars (
    symbol     LowCardinality(String) CODEC(ZSTD(1)),
    market     LowCardinality(String) CODEC(ZSTD(1)),
    resolution UInt16 CODEC(T64, LZ4),
    open       Float32 CODEC(Gorilla, ZSTD(1)),
    high       Float32 CODEC(Gorilla, ZSTD(1)),
    low        Float32 CODEC(Gorilla, ZSTD(1)),
    close      Float32 CODEC(Gorilla, ZSTD(1)),
    volume     Float64 CODEC(DoubleDelta, ZSTD(1)),
    trades     UInt32 CODEC(Delta, ZSTD(1)),
    ts         DateTime64(3, 'UTC') CODEC(Delta, LZ4),
    _resolution_minutes UInt16 MATERIALIZED resolution / 60
)
ENGINE = ReplacingMergeTree()
ORDER BY (symbol, market, resolution, ts)
PARTITION BY (symbol, toYYYYMM(ts))
TTL ts + INTERVAL 2 YEAR
SETTINGS index_granularity = 256, allow_nullable_key = 1;
