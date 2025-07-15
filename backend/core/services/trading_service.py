import asyncio
import uuid
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from models.trading import (
    StrategyResponse, OrderResponse, PositionResponse, 
    PerformanceResponse, PortfolioMetrics, EmergencyStopResponse
)
from ..config import settings
from db.clickhouse import get_client as get_clickhouse_client

logger = logging.getLogger(__name__)

class TradingService:
    """Main trading service that orchestrates all trading operations"""
    
    def __init__(self):
        self.active_strategies = {}
        self.monitoring_tasks = {}
        self.db_client = None
        logger.info("Trading Service initialized")
    
    async def get_db_client(self):
        """Get ClickHouse database client"""
        if not self.db_client:
            self.db_client = get_clickhouse_client()
        return self.db_client
    
    async def create_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """Create a new trading strategy"""
        try:
            # Generate unique strategy ID
            strategy_id = str(uuid.uuid4())
            
            # Prepare strategy data for database
            db_data = {
                'id': strategy_id,
                'name': strategy_data['name'],
                'symbol': strategy_data['symbol'],
                'strategy_type': strategy_data['strategy_type'],
                'min_price': strategy_data['min_price'],
                'max_price': strategy_data['max_price'],
                'grid_levels': strategy_data['grid_levels'],
                'quantity_per_level': strategy_data['total_quantity'] / strategy_data['grid_levels'],
                'spread_percentage': strategy_data['spread_percentage'],
                'active': 0,  # Start inactive
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'total_pnl': 0.0,
                'config': json.dumps(strategy_data)
            }
            
            # Insert into database
            client = await self.get_db_client()
            client.insert('trading_strategies', [db_data])
            
            logger.info(f"Created strategy {strategy_id} for {strategy_data['symbol']}")
            return strategy_id
            
        except Exception as e:
            logger.error(f"Error creating strategy: {str(e)}")
            raise
    
    async def get_strategy(self, strategy_id: str) -> Optional[StrategyResponse]:
        """Get a specific strategy by ID"""
        try:
            client = await self.get_db_client()
            
            result = client.query(
                "SELECT * FROM trading_strategies WHERE id = {strategy_id:String}",
                parameters={'strategy_id': strategy_id}
            )
            
            if not result.result_rows:
                return None
            
            row = result.result_rows[0]
            columns = result.column_names
            strategy_data = dict(zip(columns, row))
            
            # Convert to response model
            return StrategyResponse(
                id=strategy_data['id'],
                name=strategy_data['name'],
                symbol=strategy_data['symbol'],
                strategy_type=strategy_data['strategy_type'],
                min_price=strategy_data['min_price'],
                max_price=strategy_data['max_price'],
                grid_levels=strategy_data['grid_levels'],
                quantity_per_level=strategy_data['quantity_per_level'],
                spread_percentage=strategy_data['spread_percentage'],
                active=bool(strategy_data['active']),
                created_at=strategy_data['created_at'],
                updated_at=strategy_data['updated_at'],
                total_pnl=strategy_data['total_pnl'],
                config=json.loads(strategy_data['config']) if strategy_data['config'] else None
            )
            
        except Exception as e:
            logger.error(f"Error getting strategy {strategy_id}: {str(e)}")
            raise
    
    async def get_strategies(
        self, 
        active_only: bool = False, 
        symbol: Optional[str] = None
    ) -> List[StrategyResponse]:
        """Get all strategies with optional filters"""
        try:
            client = await self.get_db_client()
            
            # Build query with filters
            query = "SELECT * FROM trading_strategies WHERE 1=1"
            params = {}
            
            if active_only:
                query += " AND active = 1"
            
            if symbol:
                query += " AND symbol = {symbol:String}"
                params['symbol'] = symbol
            
            query += " ORDER BY created_at DESC"
            
            result = client.query(query, parameters=params)
            
            strategies = []
            for row in result.result_rows:
                strategy_data = dict(zip(result.column_names, row))
                
                strategies.append(StrategyResponse(
                    id=strategy_data['id'],
                    name=strategy_data['name'],
                    symbol=strategy_data['symbol'],
                    strategy_type=strategy_data['strategy_type'],
                    min_price=strategy_data['min_price'],
                    max_price=strategy_data['max_price'],
                    grid_levels=strategy_data['grid_levels'],
                    quantity_per_level=strategy_data['quantity_per_level'],
                    spread_percentage=strategy_data['spread_percentage'],
                    active=bool(strategy_data['active']),
                    created_at=strategy_data['created_at'],
                    updated_at=strategy_data['updated_at'],
                    total_pnl=strategy_data['total_pnl'],
                    config=json.loads(strategy_data['config']) if strategy_data['config'] else None
                ))
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting strategies: {str(e)}")
            raise
    
    async def update_strategy(self, strategy_id: str, update_data: Dict[str, Any]) -> bool:
        """Update strategy configuration"""
        try:
            # Check if strategy exists
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return False
            
            # Prepare update data
            update_fields = []
            params = {'strategy_id': strategy_id}
            
            for field, value in update_data.items():
                if field in ['name', 'min_price', 'max_price', 'grid_levels', 
                           'total_quantity', 'spread_percentage', 'notes']:
                    update_fields.append(f"{field} = {{{field}:String}}")
                    params[field] = value
            
            if not update_fields:
                return True  # No fields to update
            
            # Add updated_at
            update_fields.append("updated_at = {updated_at:DateTime}")
            params['updated_at'] = datetime.utcnow()
            
            # Execute update
            client = await self.get_db_client()
            query = f"ALTER TABLE trading_strategies UPDATE {', '.join(update_fields)} WHERE id = {{strategy_id:String}}"
            client.command(query, parameters=params)
            
            logger.info(f"Updated strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating strategy {strategy_id}: {str(e)}")
            raise
    
    async def activate_strategy(self, strategy_id: str) -> bool:
        """Activate a trading strategy"""
        try:
            # Check if strategy exists and is not already active
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return False
            
            if strategy.active:
                return True  # Already active
            
            # Check concurrent strategy limit
            active_strategies = await self.get_strategies(active_only=True)
            if len(active_strategies) >= settings.MAX_CONCURRENT_STRATEGIES:
                raise ValueError(f"Maximum concurrent strategies limit ({settings.MAX_CONCURRENT_STRATEGIES}) reached")
            
            # Activate strategy in database
            client = await self.get_db_client()
            client.command(
                "ALTER TABLE trading_strategies UPDATE active = 1, updated_at = {updated_at:DateTime} WHERE id = {strategy_id:String}",
                parameters={
                    'strategy_id': strategy_id,
                    'updated_at': datetime.utcnow()
                }
            )
            
            # Start monitoring
            await self.start_strategy_monitoring(strategy_id)
            
            logger.info(f"Activated strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating strategy {strategy_id}: {str(e)}")
            raise
    
    async def deactivate_strategy(self, strategy_id: str) -> bool:
        """Deactivate a trading strategy"""
        try:
            # Check if strategy exists
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return False
            
            # Deactivate strategy in database
            client = await self.get_db_client()
            client.command(
                "ALTER TABLE trading_strategies UPDATE active = 0, updated_at = {updated_at:DateTime} WHERE id = {strategy_id:String}",
                parameters={
                    'strategy_id': strategy_id,
                    'updated_at': datetime.utcnow()
                }
            )
            
            # Cancel all pending orders for this strategy
            await self.cancel_strategy_orders(strategy_id)
            
            # Stop monitoring
            await self.stop_strategy_monitoring(strategy_id)
            
            logger.info(f"Deactivated strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating strategy {strategy_id}: {str(e)}")
            raise
    
    async def delete_strategy(self, strategy_id: str) -> bool:
        """Delete a trading strategy"""
        try:
            # First deactivate the strategy
            await self.deactivate_strategy(strategy_id)
            
            # Delete from database (note: this will cascade to related data)
            client = await self.get_db_client()
            
            # Delete related data first
            client.command(
                "DELETE FROM trading_orders WHERE strategy_id = {strategy_id:String}",
                parameters={'strategy_id': strategy_id}
            )
            
            client.command(
                "DELETE FROM trading_positions WHERE strategy_id = {strategy_id:String}",
                parameters={'strategy_id': strategy_id}
            )
            
            client.command(
                "DELETE FROM performance_metrics WHERE strategy_id = {strategy_id:String}",
                parameters={'strategy_id': strategy_id}
            )
            
            # Delete strategy
            client.command(
                "DELETE FROM trading_strategies WHERE id = {strategy_id:String}",
                parameters={'strategy_id': strategy_id}
            )
            
            logger.info(f"Deleted strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting strategy {strategy_id}: {str(e)}")
            raise
    
    async def get_orders(
        self,
        strategy_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[OrderResponse]:
        """Get trading orders"""
        try:
            client = await self.get_db_client()
            
            # Build query
            query = "SELECT * FROM trading_orders WHERE 1=1"
            params = {}
            
            if strategy_id:
                query += " AND strategy_id = {strategy_id:String}"
                params['strategy_id'] = strategy_id
            
            if status:
                query += " AND status = {status:String}"
                params['status'] = status
            
            query += " ORDER BY created_at DESC LIMIT {limit:UInt32}"
            params['limit'] = limit
            
            result = client.query(query, parameters=params)
            
            orders = []
            for row in result.result_rows:
                order_data = dict(zip(result.column_names, row))
                
                orders.append(OrderResponse(
                    id=order_data['id'],
                    strategy_id=order_data['strategy_id'],
                    symbol=order_data['symbol'],
                    side=order_data['side'],
                    order_type=order_data['order_type'],
                    quantity=order_data['quantity'],
                    price=order_data['price'],
                    filled_quantity=order_data['filled_quantity'],
                    status=order_data['status'],
                    exchange_order_id=order_data['exchange_order_id'],
                    created_at=order_data['created_at'],
                    filled_at=order_data['filled_at'],
                    commission=order_data['commission']
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            raise
    
    async def get_positions(self, strategy_id: Optional[str] = None) -> List[PositionResponse]:
        """Get current positions"""
        try:
            client = await self.get_db_client()
            
            # Build query
            query = "SELECT * FROM trading_positions WHERE size != 0"
            params = {}
            
            if strategy_id:
                query += " AND strategy_id = {strategy_id:String}"
                params['strategy_id'] = strategy_id
            
            query += " ORDER BY updated_at DESC"
            
            result = client.query(query, parameters=params)
            
            positions = []
            for row in result.result_rows:
                position_data = dict(zip(result.column_names, row))
                
                positions.append(PositionResponse(
                    id=position_data['id'],
                    strategy_id=position_data['strategy_id'],
                    symbol=position_data['symbol'],
                    side=position_data['side'],
                    size=position_data['size'],
                    entry_price=position_data['entry_price'],
                    current_price=position_data['current_price'],
                    unrealized_pnl=position_data['unrealized_pnl'],
                    realized_pnl=position_data['realized_pnl'],
                    opened_at=position_data['opened_at'],
                    updated_at=position_data['updated_at']
                ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise
    
    async def get_performance_metrics(
        self, 
        strategy_id: str, 
        days: int = 7
    ) -> List[PerformanceResponse]:
        """Get performance metrics for a strategy"""
        try:
            client = await self.get_db_client()
            
            result = client.query(
                """
                SELECT * FROM performance_metrics 
                WHERE strategy_id = {strategy_id:String} 
                  AND timestamp >= now() - INTERVAL {days:UInt32} DAY
                ORDER BY timestamp DESC
                """,
                parameters={'strategy_id': strategy_id, 'days': days}
            )
            
            metrics = []
            for row in result.result_rows:
                metric_data = dict(zip(result.column_names, row))
                
                metrics.append(PerformanceResponse(
                    strategy_id=metric_data['strategy_id'],
                    timestamp=metric_data['timestamp'],
                    total_pnl=metric_data['total_pnl'],
                    unrealized_pnl=metric_data['unrealized_pnl'],
                    realized_pnl=metric_data['realized_pnl'],
                    drawdown=metric_data['drawdown'],
                    win_rate=metric_data['win_rate'],
                    sharpe_ratio=metric_data['sharpe_ratio'],
                    total_trades=metric_data['total_trades'],
                    winning_trades=metric_data['winning_trades']
                ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            raise
    
    async def get_portfolio_metrics(self) -> PortfolioMetrics:
        """Get portfolio-level metrics"""
        try:
            client = await self.get_db_client()
            
            # Get all strategies
            strategies = await self.get_strategies()
            
            # Get all positions
            positions = await self.get_positions()
            
            # Calculate metrics
            total_pnl = sum(s.total_pnl for s in strategies)
            unrealized_pnl = sum(p.unrealized_pnl for p in positions)
            realized_pnl = total_pnl - unrealized_pnl
            
            # Calculate total value (simplified)
            total_value = sum(abs(p.size) * p.current_price for p in positions)
            
            # Calculate win rate (simplified)
            filled_orders = await self.get_orders(status='filled')
            if filled_orders:
                profitable_orders = [o for o in filled_orders if o.side == 'sell']  # Simplified
                win_rate = len(profitable_orders) / len(filled_orders)
            else:
                win_rate = 0.0
            
            return PortfolioMetrics(
                total_value=round(total_value, 2),
                total_pnl=round(total_pnl, 2),
                unrealized_pnl=round(unrealized_pnl, 2),
                realized_pnl=round(realized_pnl, 2),
                active_strategies=len([s for s in strategies if s.active]),
                total_strategies=len(strategies),
                win_rate=round(win_rate * 100, 2),
                max_drawdown=5.0,  # Placeholder
                sharpe_ratio=1.2,   # Placeholder
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting portfolio metrics: {str(e)}")
            raise
    
    async def emergency_stop_all(self) -> EmergencyStopResponse:
        """Emergency stop all trading activities"""
        try:
            # Get all active strategies
            active_strategies = await self.get_strategies(active_only=True)
            
            strategies_stopped = 0
            orders_cancelled = 0
            
            # Deactivate all strategies
            for strategy in active_strategies:
                try:
                    await self.deactivate_strategy(strategy.id)
                    strategies_stopped += 1
                    
                    # Count cancelled orders (simplified)
                    strategy_orders = await self.get_orders(strategy_id=strategy.id, status='pending')
                    orders_cancelled += len(strategy_orders)
                    
                except Exception as e:
                    logger.error(f"Error stopping strategy {strategy.id}: {str(e)}")
            
            logger.warning(f"Emergency stop: {strategies_stopped} strategies stopped, {orders_cancelled} orders cancelled")
            
            return EmergencyStopResponse(
                message=f"Emergency stop executed: {strategies_stopped} strategies stopped",
                strategies_stopped=strategies_stopped,
                orders_cancelled=orders_cancelled,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {str(e)}")
            raise
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            strategies = await self.get_strategies()
            active_strategies = [s for s in strategies if s.active]
            positions = await self.get_positions()
            pending_orders = await self.get_orders(status='pending')
            
            return {
                'trading_enabled': settings.TRADING_ENABLED,
                'system_health': 'healthy',
                'timestamp': datetime.utcnow(),
                'strategies': {
                    'total': len(strategies),
                    'active': len(active_strategies),
                    'max_allowed': settings.MAX_CONCURRENT_STRATEGIES
                },
                'positions': {
                    'total': len(positions),
                    'total_value': sum(abs(p.size) * p.current_price for p in positions)
                },
                'orders': {
                    'pending': len(pending_orders)
                },
                'performance': {
                    'total_pnl': sum(s.total_pnl for s in strategies),
                    'active_pnl': sum(s.total_pnl for s in active_strategies)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            raise
    
    async def start_strategy_monitoring(self, strategy_id: str):
        """Start monitoring a strategy"""
        if strategy_id not in self.monitoring_tasks:
            task = asyncio.create_task(self.monitor_strategy(strategy_id))
            self.monitoring_tasks[strategy_id] = task
            logger.info(f"Started monitoring strategy {strategy_id}")
    
    async def stop_strategy_monitoring(self, strategy_id: str):
        """Stop monitoring a strategy"""
        if strategy_id in self.monitoring_tasks:
            self.monitoring_tasks[strategy_id].cancel()
            del self.monitoring_tasks[strategy_id]
            logger.info(f"Stopped monitoring strategy {strategy_id}")
    
    async def monitor_strategy(self, strategy_id: str):
        """Monitor a strategy (placeholder implementation)"""
        try:
            while True:
                # This would contain the actual monitoring logic
                # For now, just sleep
                await asyncio.sleep(10)
                
                # Check if strategy is still active
                strategy = await self.get_strategy(strategy_id)
                if not strategy or not strategy.active:
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"Strategy monitoring cancelled for {strategy_id}")
        except Exception as e:
            logger.error(f"Error monitoring strategy {strategy_id}: {str(e)}")
    
    async def cancel_strategy_orders(self, strategy_id: str):
        """Cancel all pending orders for a strategy"""
        try:
            # This would integrate with the exchange API
            # For now, just mark orders as cancelled in database
            client = await self.get_db_client()
            
            client.command(
                """
                ALTER TABLE trading_orders 
                UPDATE status = 'cancelled' 
                WHERE strategy_id = {strategy_id:String} AND status = 'pending'
                """,
                parameters={'strategy_id': strategy_id}
            )
            
            logger.info(f"Cancelled pending orders for strategy {strategy_id}")
            
        except Exception as e:
            logger.error(f"Error cancelling orders for strategy {strategy_id}: {str(e)}")
            raise
