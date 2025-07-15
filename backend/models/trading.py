from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class StrategyType(str, Enum):
    GRID = "grid"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    ARBITRAGE = "arbitrage"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class StrategyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., pattern=r'^[A-Z]+/[A-Z]+$')
    strategy_type: StrategyType = StrategyType.GRID
    min_price: float = Field(..., gt=0)
    max_price: float = Field(..., gt=0)
    grid_levels: int = Field(..., ge=3, le=100)
    total_quantity: float = Field(..., gt=0)
    spread_percentage: float = Field(default=0.1, ge=0.01, le=10.0)
    
    # Risk management
    max_position_size: Optional[float] = Field(default=10.0, gt=0)
    stop_loss: Optional[float] = Field(default=None, ge=0, le=1)
    take_profit: Optional[float] = Field(default=None, ge=0, le=1)
    max_drawdown: Optional[float] = Field(default=0.05, ge=0, le=1)
    
    # Advanced options
    auto_rebalance: bool = Field(default=True)
    compound_profits: bool = Field(default=False)
    emergency_stop: bool = Field(default=True)
    notes: Optional[str] = Field(default="", max_length=500)

    @validator('max_price')
    def max_price_must_be_greater_than_min_price(cls, v, values):
        if 'min_price' in values and v <= values['min_price']:
            raise ValueError('max_price must be greater than min_price')
        return v

class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    min_price: Optional[float] = Field(None, gt=0)
    max_price: Optional[float] = Field(None, gt=0)
    grid_levels: Optional[int] = Field(None, ge=3, le=100)
    total_quantity: Optional[float] = Field(None, gt=0)
    spread_percentage: Optional[float] = Field(None, ge=0.01, le=10.0)
    max_position_size: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = Field(None, ge=0, le=1)
    take_profit: Optional[float] = Field(None, ge=0, le=1)
    max_drawdown: Optional[float] = Field(None, ge=0, le=1)
    auto_rebalance: Optional[bool] = None
    compound_profits: Optional[bool] = None
    emergency_stop: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)

class StrategyResponse(BaseModel):
    id: str
    name: str
    symbol: str
    strategy_type: str
    min_price: float
    max_price: float
    grid_levels: int
    quantity_per_level: float
    spread_percentage: float
    active: bool
    created_at: datetime
    updated_at: datetime
    total_pnl: float
    config: Optional[Dict[str, Any]] = None

class OrderResponse(BaseModel):
    id: str
    strategy_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float
    filled_quantity: float
    status: str
    exchange_order_id: Optional[str]
    created_at: datetime
    filled_at: Optional[datetime]
    commission: float

class PositionResponse(BaseModel):
    id: str
    strategy_id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    opened_at: datetime
    updated_at: datetime

class PerformanceResponse(BaseModel):
    strategy_id: str
    timestamp: datetime
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    drawdown: float
    win_rate: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int

class RiskAlert(BaseModel):
    id: str
    strategy_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    current_value: float
    threshold_value: float
    acknowledged: bool
    created_at: datetime
    acknowledged_at: Optional[datetime]

class GridLevelCalculation(BaseModel):
    price: float
    quantity: float
    side: str
    order_value: float

class GridCalculationResponse(BaseModel):
    levels: List[GridLevelCalculation]
    total_investment: float
    price_range: float
    price_step: float
    levels_count: int

class PortfolioMetrics(BaseModel):
    total_value: float
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    active_strategies: int
    total_strategies: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    updated_at: datetime

class EmergencyStopResponse(BaseModel):
    message: str
    strategies_stopped: int
    orders_cancelled: int
    timestamp: datetime

# WebSocket Messages
class WSMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PriceUpdate(BaseModel):
    symbol: str
    price: float
    volume: float
    change_24h: Optional[float]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StrategyUpdate(BaseModel):
    strategy_id: str
    action: str  # 'created', 'activated', 'deactivated', 'updated', 'deleted'
    data: Optional[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OrderUpdate(BaseModel):
    order_id: str
    strategy_id: str
    status: str
    filled_quantity: Optional[float]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RiskAlertUpdate(BaseModel):
    alert_id: str
    strategy_id: str
    severity: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
