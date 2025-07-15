-- Use main ML/Trading-Datenbank
CREATE DATABASE IF NOT EXISTS websocket_ml;

-- Modelle/Registr y
CREATE TABLE IF NOT EXISTS websocket_ml.ml_models (
    id String,
    name String,
    engine String,
    type String,
    version String,
    path String,
    features Array(String),
    metrics String,
    status String,
    user String,
    created_at DateTime,
    updated_at DateTime
) ENGINE = MergeTree()
ORDER BY id;

-- Einzelne Indikator-/Signalwerte (z. B. „Trend“, „BullTrap“, „WhaleImpact“, etc.)
CREATE TABLE IF NOT EXISTS websocket_ml.ml_signals (
    id String,
    timestamp DateTime,
    symbol String,
    interval String,
    indicator String,
    value Float64,
    model_id String,
    engine String,
    confidence Float64,
    meta String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY (symbol, interval, indicator, timestamp);

-- Ghostlines/Forecasts (jeder Step als eigene Row, kein Array!)
CREATE TABLE IF NOT EXISTS websocket_ml.ghost_lines (
    id String,
    symbol String,
    interval String,
    model_id String,
    engine String,
    time DateTime,
    value Float64,
    meta String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY (symbol, interval, model_id, time);

-- Snapshots (Modellstände, z. B. nach Training/Epochs)
CREATE TABLE IF NOT EXISTS websocket_ml.ml_snapshots (
    id String,
    model_id String,
    engine String,
    path String,
    metrics String,
    params String,
    user String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY (model_id, created_at);

-- Templates (Model-/Feature-/Config-Templates)
CREATE TABLE IF NOT EXISTS websocket_ml.ml_templates (
    id String,
    name String,
    engine String,
    config String,
    user String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY (engine, name);

-- AutoML-Jobs
CREATE TABLE IF NOT EXISTS websocket_ml.automl_jobs (
    id String,
    engine String,
    config String,
    status String,
    result String,
    started_at DateTime,
    finished_at DateTime
) ENGINE = MergeTree()
ORDER BY (engine, started_at);

-- Indikatorwerte (optional – falls du Spalten statt Rows willst; die Hauptzeitreihen immer in bars!)
CREATE TABLE IF NOT EXISTS websocket_ml.indicator_values (
    id String,
    timestamp DateTime,
    symbol String,
    interval String,
    indicator String,
    value Float64,
    meta String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY (symbol, interval, indicator, timestamp);

-- Whale Events (für Feature-Engineering, kann von allen genutzt werden)
CREATE TABLE IF NOT EXISTS websocket_ml.whale_events (
    id String,
    timestamp DateTime,
    symbol String,
    type String,
    impact Float64,
    meta String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY (symbol, timestamp);

-- Bars/Trades (nur Referenz, falls KI-Training direkt darauf arbeitet)
CREATE TABLE IF NOT EXISTS websocket_ml.bars (
    time DateTime,
    symbol String,
    interval String,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    alma Float64,
    spectral_power Float64,
    six_sigma_upper Float64,
    six_sigma_lower Float64,
    whale_impact Float64,
    elliott_wave Float64,
    -- beliebig viele weitere Feature-Spalten
    meta String
) ENGINE = MergeTree()
ORDER BY (symbol, interval, time);

-- User (für Rechte, Ownership, etc.)
CREATE TABLE IF NOT EXISTS websocket_ml.users (
    id String,
    username String,
    email String,
    role String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY id;
