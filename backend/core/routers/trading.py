from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import uuid
import json
import logging

from models.trading import (
    StrategyCreate, StrategyResponse, StrategyUpdate,
    OrderResponse, PositionResponse, PerformanceResponse,
    RiskAlert, GridCalculationResponse, PortfolioMetrics,
    EmergencyStopResponse
)
from ..services.trading_service import TradingService
from ..services.grid_service import GridService
from ..services.risk_service import RiskService
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trading", tags=["trading"])

# Dependency injection for services
async def get_trading_service():
    return TradingService()

async def get_grid_service():
    return GridService()

async def get_risk_service():
    return RiskService()

@router.get("/health")
async def health_check():
    """Health check for trading system"""
    return {
        "status": "healthy" if settings.TRADING_ENABLED else "disabled",
        "timestamp": datetime.utcnow(),
        "services": {
            "grid_engine": "active" if settings.TRADING_ENABLED else "disabled",
            "risk_management": "active" if settings.TRADING_ENABLED else "disabled",
            "market_data": "active"
        },
        "config": {
            "max_strategies": settings.MAX_CONCURRENT_STRATEGIES,
            "max_position_size": settings.MAX_POSITION_SIZE,
            "max_drawdown": settings.MAX_DRAWDOWN
        }
    }

# Strategy Management
@router.post("/strategies", response_model=StrategyResponse)
async def create_strategy(
    strategy: StrategyCreate,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Create a new trading strategy"""
    if not settings.TRADING_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trading system is disabled"
        )
    
    try:
        # Validate grid levels
        if strategy.grid_levels < settings.MIN_GRID_LEVELS or strategy.grid_levels > settings.MAX_GRID_LEVELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Grid levels must be between {settings.MIN_GRID_LEVELS} and {settings.MAX_GRID_LEVELS}"
            )
        
        strategy_id = await trading_service.create_strategy(strategy.dict())
        strategy_response = await trading_service.get_strategy(strategy_id)
        
        if not strategy_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Strategy was created but could not be retrieved"
            )
        
        return strategy_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create strategy: {str(e)}"
        )

@router.get("/strategies", response_model=List[StrategyResponse])
async def get_strategies(
    active_only: bool = False,
    symbol: Optional[str] = None,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get all trading strategies"""
    try:
        return await trading_service.get_strategies(
            active_only=active_only,
            symbol=symbol
        )
    except Exception as e:
        logger.error(f"Failed to get strategies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategies"
        )

@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get specific strategy"""
    try:
        strategy = await trading_service.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategy"
        )

@router.put("/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    strategy_update: StrategyUpdate,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Update strategy configuration"""
    if not settings.TRADING_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trading system is disabled"
        )
    
    try:
        success = await trading_service.update_strategy(
            strategy_id, 
            strategy_update.dict(exclude_unset=True)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        
        return await trading_service.get_strategy(strategy_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update strategy"
        )

@router.post("/strategies/{strategy_id}/activate")
async def activate_strategy(
    strategy_id: str,
    background_tasks: BackgroundTasks,
    trading_service: TradingService = Depends(get_trading_service),
    risk_service: RiskService = Depends(get_risk_service)
):
    """Activate a trading strategy"""
    if not settings.TRADING_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trading system is disabled"
        )
    
    try:
        # Check risk limits before activation
        strategy = await trading_service.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        
        risk_check = await risk_service.check_strategy_activation(strategy_id)
        if not risk_check["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy activation blocked: {risk_check['reason']}"
            )
        
        success = await trading_service.activate_strategy(strategy_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to activate strategy"
            )
        
        # Start monitoring in background
        background_tasks.add_task(trading_service.monitor_strategy, strategy_id)
        
        return {"message": "Strategy activated successfully", "strategy_id": strategy_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate strategy"
        )

@router.post("/strategies/{strategy_id}/deactivate")
async def deactivate_strategy(
    strategy_id: str,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Deactivate a trading strategy"""
    try:
        success = await trading_service.deactivate_strategy(strategy_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found or already inactive"
            )
        
        return {"message": "Strategy deactivated successfully", "strategy_id": strategy_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate strategy"
        )

@router.delete("/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Delete a trading strategy"""
    try:
        success = await trading_service.delete_strategy(strategy_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        
        return {"message": "Strategy deleted successfully", "strategy_id": strategy_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete strategy"
        )

# Orders
@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    strategy_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get trading orders"""
    try:
        return await trading_service.get_orders(
            strategy_id=strategy_id,
            status=status,
            limit=min(limit, 1000)  # Cap at 1000
        )
    except Exception as e:
        logger.error(f"Failed to get orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders"
        )

# Positions
@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    strategy_id: Optional[str] = None,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get current positions"""
    try:
        return await trading_service.get_positions(strategy_id=strategy_id)
    except Exception as e:
        logger.error(f"Failed to get positions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve positions"
        )

# Performance
@router.get("/performance/{strategy_id}", response_model=List[PerformanceResponse])
async def get_strategy_performance(
    strategy_id: str,
    days: int = 7,
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get strategy performance metrics"""
    try:
        return await trading_service.get_performance_metrics(
            strategy_id, 
            max(1, min(days, 365))  # Cap between 1 and 365 days
        )
    except Exception as e:
        logger.error(f"Failed to get performance for strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )

@router.get("/portfolio/metrics", response_model=PortfolioMetrics)
async def get_portfolio_metrics(
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get portfolio-level metrics"""
    try:
        return await trading_service.get_portfolio_metrics()
    except Exception as e:
        logger.error(f"Failed to get portfolio metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio metrics"
        )

# Risk Management
@router.get("/risk/alerts", response_model=List[RiskAlert])
async def get_risk_alerts(
    strategy_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 100,
    risk_service: RiskService = Depends(get_risk_service)
):
    """Get risk alerts"""
    try:
        return await risk_service.get_alerts(
            strategy_id=strategy_id,
            severity=severity,
            acknowledged=acknowledged,
            limit=min(limit, 1000)
        )
    except Exception as e:
        logger.error(f"Failed to get risk alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk alerts"
        )

@router.post("/risk/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    risk_service: RiskService = Depends(get_risk_service)
):
    """Acknowledge a risk alert"""
    try:
        success = await risk_service.acknowledge_alert(alert_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {"message": "Alert acknowledged", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )

# Grid Trading Specific
@router.post("/grid/calculate-levels", response_model=GridCalculationResponse)
async def calculate_grid_levels(
    min_price: float,
    max_price: float,
    levels: int,
    total_quantity: float,
    spread_factor: float = 0.001,
    grid_service: GridService = Depends(get_grid_service)
):
    """Calculate grid levels for strategy planning"""
    if min_price >= max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price must be less than max_price"
        )
    
    if levels < settings.MIN_GRID_LEVELS or levels > settings.MAX_GRID_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grid levels must be between {settings.MIN_GRID_LEVELS} and {settings.MAX_GRID_LEVELS}"
        )
    
    try:
        return await grid_service.calculate_grid_levels(
            min_price, max_price, levels, total_quantity, spread_factor
        )
    except Exception as e:
        logger.error(f"Failed to calculate grid levels: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to calculate grid levels: {str(e)}"
        )

# Emergency Controls
@router.post("/emergency/stop-all", response_model=EmergencyStopResponse)
async def emergency_stop_all(
    trading_service: TradingService = Depends(get_trading_service)
):
    """Emergency stop all trading activities"""
    try:
        result = await trading_service.emergency_stop_all()
        logger.warning(f"Emergency stop executed: {result}")
        return result
    except Exception as e:
        logger.error(f"Emergency stop failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emergency stop failed: {str(e)}"
        )

# System Status
@router.get("/status")
async def get_system_status(
    trading_service: TradingService = Depends(get_trading_service)
):
    """Get comprehensive system status"""
    try:
        return await trading_service.get_system_status()
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )
