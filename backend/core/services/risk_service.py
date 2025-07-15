import asyncio
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from models.trading import RiskAlert, AlertSeverity
from ..config import settings
from db.clickhouse import get_client as get_clickhouse_client

logger = logging.getLogger(__name__)

class RiskService:
    """Risk management and monitoring service"""
    
    def __init__(self):
        self.active_alerts = {}
        self.risk_thresholds = {
            'max_position_size': settings.MAX_POSITION_SIZE,
            'max_drawdown': settings.MAX_DRAWDOWN,
            'max_daily_loss': 1000.0,  # $1000 daily loss limit
            'max_portfolio_concentration': 0.25,  # 25% max in single asset
            'max_leverage': 3.0,
            'volatility_threshold': 0.15  # 15% daily volatility
        }
        self.db_client = None
        logger.info("Risk Service initialized")
    
    async def get_db_client(self):
        """Get ClickHouse database client"""
        if not self.db_client:
            self.db_client = get_clickhouse_client()
        return self.db_client
    
    async def check_strategy_activation(self, strategy_id: str) -> Dict[str, Any]:
        """Check if a strategy can be safely activated"""
        try:
            from .trading_service import TradingService
            trading_service = TradingService()
            
            # Get strategy details
            strategy = await trading_service.get_strategy(strategy_id)
            if not strategy:
                return {"allowed": False, "reason": "Strategy not found"}
            
            # Check concurrent strategy limit
            active_strategies = await trading_service.get_strategies(active_only=True)
            if len(active_strategies) >= settings.MAX_CONCURRENT_STRATEGIES:
                return {
                    "allowed": False, 
                    "reason": f"Maximum concurrent strategies limit ({settings.MAX_CONCURRENT_STRATEGIES}) reached"
                }
            
            # Check position size
            if strategy.quantity_per_level * strategy.grid_levels > self.risk_thresholds['max_position_size']:
                return {
                    "allowed": False,
                    "reason": f"Strategy position size exceeds limit of {self.risk_thresholds['max_position_size']}"
                }
            
            # Check portfolio concentration
            portfolio_check = await self._check_portfolio_concentration(strategy.symbol, strategy.quantity_per_level * strategy.grid_levels)
            if not portfolio_check["allowed"]:
                return portfolio_check
            
            # Check if price range is reasonable
            price_range_pct = ((strategy.max_price - strategy.min_price) / strategy.min_price) * 100
            if price_range_pct > 100:  # More than 100% range
                return {
                    "allowed": False,
                    "reason": f"Price range ({price_range_pct:.1f}%) is too wide and may be risky"
                }
            
            return {"allowed": True, "reason": "All risk checks passed"}
            
        except Exception as e:
            logger.error(f"Error checking strategy activation: {str(e)}")
            return {"allowed": False, "reason": f"Risk check failed: {str(e)}"}
    
    async def monitor_strategy_risk(self, strategy_id: str) -> List[RiskAlert]:
        """Monitor risk for an active strategy"""
        try:
            from .trading_service import TradingService
            trading_service = TradingService()
            
            alerts = []
            
            # Get strategy and its performance
            strategy = await trading_service.get_strategy(strategy_id)
            if not strategy:
                return alerts
            
            positions = await trading_service.get_positions(strategy_id=strategy_id)
            orders = await trading_service.get_orders(strategy_id=strategy_id, status='pending')
            
            # Check drawdown
            if strategy.total_pnl < 0:
                drawdown_pct = abs(strategy.total_pnl) / (strategy.quantity_per_level * strategy.grid_levels * strategy.min_price)
                if drawdown_pct > self.risk_thresholds['max_drawdown']:
                    alert = await self._create_alert(
                        strategy_id=strategy_id,
                        alert_type='drawdown',
                        severity=AlertSeverity.HIGH if drawdown_pct < self.risk_thresholds['max_drawdown'] * 2 else AlertSeverity.CRITICAL,
                        message=f"Strategy drawdown ({drawdown_pct:.2%}) exceeds threshold ({self.risk_thresholds['max_drawdown']:.2%})",
                        current_value=drawdown_pct,
                        threshold_value=self.risk_thresholds['max_drawdown']
                    )
                    alerts.append(alert)
            
            # Check position concentration
            total_position_value = sum(abs(p.size) * p.current_price for p in positions)
            if total_position_value > self.risk_thresholds['max_position_size'] * 1000:  # Assuming position size is in units
                alert = await self._create_alert(
                    strategy_id=strategy_id,
                    alert_type='position_size',
                    severity=AlertSeverity.HIGH,
                    message=f"Total position value (${total_position_value:.2f}) is very large",
                    current_value=total_position_value,
                    threshold_value=self.risk_thresholds['max_position_size'] * 1000
                )
                alerts.append(alert)
            
            # Check pending orders count
            if len(orders) > 50:  # Too many pending orders
                alert = await self._create_alert(
                    strategy_id=strategy_id,
                    alert_type='order_count',
                    severity=AlertSeverity.MEDIUM,
                    message=f"High number of pending orders ({len(orders)})",
                    current_value=len(orders),
                    threshold_value=50
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error monitoring strategy risk: {str(e)}")
            return []
    
    async def check_portfolio_risk(self) -> Dict[str, Any]:
        """Check overall portfolio risk"""
        try:
            from .trading_service import TradingService
            trading_service = TradingService()
            
            # Get portfolio data
            strategies = await trading_service.get_strategies()
            positions = await trading_service.get_positions()
            
            risk_metrics = {
                'total_exposure': 0.0,
                'total_pnl': 0.0,
                'max_single_position': 0.0,
                'concentration_risk': 0.0,
                'active_strategies': len([s for s in strategies if s.active]),
                'total_strategies': len(strategies),
                'risk_score': 0.0,
                'alerts': []
            }
            
            # Calculate total exposure and P&L
            total_pnl = sum(s.total_pnl for s in strategies)
            total_exposure = sum(abs(p.size) * p.current_price for p in positions)
            
            risk_metrics['total_pnl'] = total_pnl
            risk_metrics['total_exposure'] = total_exposure
            
            # Check concentration by symbol
            symbol_exposure = {}
            for position in positions:
                symbol = position.symbol
                exposure = abs(position.size) * position.current_price
                symbol_exposure[symbol] = symbol_exposure.get(symbol, 0) + exposure
            
            if symbol_exposure and total_exposure > 0:
                max_concentration = max(symbol_exposure.values()) / total_exposure
                risk_metrics['concentration_risk'] = max_concentration
                
                if max_concentration > self.risk_thresholds['max_portfolio_concentration']:
                    risk_metrics['alerts'].append({
                        'type': 'concentration',
                        'severity': 'high',
                        'message': f"Portfolio concentration risk: {max_concentration:.2%} in single asset"
                    })
            
            # Calculate risk score (0-100)
            risk_score = 0
            
            # P&L component
            if total_pnl < 0 and total_exposure > 0:
                pnl_risk = min(abs(total_pnl) / total_exposure, 0.2) * 50  # Max 50 points for P&L risk
                risk_score += pnl_risk
            
            # Concentration component
            if 'concentration_risk' in risk_metrics:
                concentration_risk = min(risk_metrics['concentration_risk'], 0.5) * 40  # Max 40 points
                risk_score += concentration_risk
            
            # Active strategies component
            if risk_metrics['active_strategies'] > settings.MAX_CONCURRENT_STRATEGIES * 0.8:
                strategy_risk = 10  # 10 points for high strategy count
                risk_score += strategy_risk
            
            risk_metrics['risk_score'] = min(risk_score, 100)
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"Error checking portfolio risk: {str(e)}")
            return {'error': str(e)}
    
    async def get_alerts(
        self,
        strategy_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[RiskAlert]:
        """Get risk alerts from database"""
        try:
            client = await self.get_db_client()
            
            # Build query
            query = "SELECT * FROM risk_alerts WHERE 1=1"
            params = {}
            
            if strategy_id:
                query += " AND strategy_id = {strategy_id:String}"
                params['strategy_id'] = strategy_id
            
            if severity:
                query += " AND severity = {severity:String}"
                params['severity'] = severity
            
            if acknowledged is not None:
                query += " AND acknowledged = {acknowledged:UInt8}"
                params['acknowledged'] = 1 if acknowledged else 0
            
            query += " ORDER BY created_at DESC LIMIT {limit:UInt32}"
            params['limit'] = limit
            
            result = client.query(query, parameters=params)
            
            alerts = []
            for row in result.result_rows:
                alert_data = dict(zip(result.column_names, row))
                
                alerts.append(RiskAlert(
                    id=alert_data['id'],
                    strategy_id=alert_data['strategy_id'],
                    alert_type=alert_data['alert_type'],
                    severity=AlertSeverity(alert_data['severity']),
                    message=alert_data['message'],
                    current_value=alert_data['current_value'],
                    threshold_value=alert_data['threshold_value'],
                    acknowledged=bool(alert_data['acknowledged']),
                    created_at=alert_data['created_at'],
                    acknowledged_at=alert_data['acknowledged_at']
                ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            return []
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a risk alert"""
        try:
            client = await self.get_db_client()
            
            # Update alert in database
            client.command(
                """
                ALTER TABLE risk_alerts 
                UPDATE acknowledged = 1, acknowledged_at = {acknowledged_at:DateTime}
                WHERE id = {alert_id:String}
                """,
                parameters={
                    'alert_id': alert_id,
                    'acknowledged_at': datetime.utcnow()
                }
            )
            
            logger.info(f"Acknowledged risk alert {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
            return False
    
    async def _create_alert(
        self,
        strategy_id: str,
        alert_type: str,
        severity: AlertSeverity,
        message: str,
        current_value: float,
        threshold_value: float
    ) -> RiskAlert:
        """Create a new risk alert"""
        try:
            alert_id = str(uuid.uuid4())
            
            alert_data = {
                'id': alert_id,
                'strategy_id': strategy_id,
                'alert_type': alert_type,
                'severity': severity.value,
                'message': message,
                'current_value': current_value,
                'threshold_value': threshold_value,
                'acknowledged': 0,
                'created_at': datetime.utcnow(),
                'acknowledged_at': None
            }
            
            # Insert into database
            client = await self.get_db_client()
            client.insert('risk_alerts', [alert_data])
            
            # Create alert object
            alert = RiskAlert(
                id=alert_id,
                strategy_id=strategy_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                current_value=current_value,
                threshold_value=threshold_value,
                acknowledged=False,
                created_at=datetime.utcnow(),
                acknowledged_at=None
            )
            
            logger.warning(f"Created risk alert: {message}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise
    
    async def _check_portfolio_concentration(self, symbol: str, additional_size: float) -> Dict[str, Any]:
        """Check if adding position would create concentration risk"""
        try:
            from .trading_service import TradingService
            trading_service = TradingService()
            
            # Get current positions
            positions = await trading_service.get_positions()
            
            # Calculate current exposure by symbol
            symbol_exposure = {}
            total_exposure = 0
            
            for position in positions:
                exposure = abs(position.size) * position.current_price
                symbol_exposure[position.symbol] = symbol_exposure.get(position.symbol, 0) + exposure
                total_exposure += exposure
            
            # Add proposed position
            # Estimate price (using a reasonable approximation)
            estimated_price = 50000.0  # This would come from market data in practice
            additional_exposure = additional_size * estimated_price
            
            symbol_exposure[symbol] = symbol_exposure.get(symbol, 0) + additional_exposure
            total_exposure += additional_exposure
            
            # Check concentration
            if total_exposure > 0:
                max_concentration = max(symbol_exposure.values()) / total_exposure
                if max_concentration > self.risk_thresholds['max_portfolio_concentration']:
                    return {
                        "allowed": False,
                        "reason": f"Position would create concentration risk: {max_concentration:.2%} in {symbol}"
                    }
            
            return {"allowed": True, "reason": "Concentration check passed"}
            
        except Exception as e:
            logger.error(f"Error checking portfolio concentration: {str(e)}")
            return {"allowed": True, "reason": "Concentration check skipped due to error"}
    
    def update_risk_thresholds(self, new_thresholds: Dict[str, float]):
        """Update risk thresholds"""
        try:
            for key, value in new_thresholds.items():
                if key in self.risk_thresholds:
                    self.risk_thresholds[key] = value
                    logger.info(f"Updated risk threshold {key} to {value}")
            
        except Exception as e:
            logger.error(f"Error updating risk thresholds: {str(e)}")
    
    def get_risk_thresholds(self) -> Dict[str, float]:
        """Get current risk thresholds"""
        return self.risk_thresholds.copy()
