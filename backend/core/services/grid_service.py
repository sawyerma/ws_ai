import asyncio
import uuid
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.trading import GridLevelCalculation, GridCalculationResponse
from ..config import settings

logger = logging.getLogger(__name__)

class GridService:
    """Service for grid trading calculations and management"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache for calculations
        logger.info("Grid Service initialized")
    
    async def calculate_grid_levels(
        self,
        min_price: float,
        max_price: float,
        levels: int,
        total_quantity: float,
        spread_factor: float = 0.001
    ) -> GridCalculationResponse:
        """Calculate grid levels for a trading strategy"""
        
        try:
            # Validate inputs
            if min_price >= max_price:
                raise ValueError("min_price must be less than max_price")
            
            if levels < settings.MIN_GRID_LEVELS or levels > settings.MAX_GRID_LEVELS:
                raise ValueError(f"Grid levels must be between {settings.MIN_GRID_LEVELS} and {settings.MAX_GRID_LEVELS}")
            
            if total_quantity <= 0:
                raise ValueError("total_quantity must be positive")
            
            # Calculate price range and step
            price_range = max_price - min_price
            price_step = price_range / (levels - 1) if levels > 1 else 0
            quantity_per_level = total_quantity / levels
            
            grid_levels = []
            total_investment = 0
            
            # Generate grid levels
            for i in range(levels):
                # Calculate price for this level
                level_price = min_price + (i * price_step)
                
                # Apply spread factor
                adjusted_price = level_price * (1 + spread_factor)
                
                # Determine side (buy orders below middle, sell orders above)
                middle_index = levels // 2
                side = "buy" if i < middle_index else "sell"
                
                # Calculate order value
                order_value = adjusted_price * quantity_per_level
                total_investment += order_value
                
                grid_level = GridLevelCalculation(
                    price=round(adjusted_price, 8),
                    quantity=round(quantity_per_level, 8),
                    side=side,
                    order_value=round(order_value, 2)
                )
                
                grid_levels.append(grid_level)
            
            # Create response
            response = GridCalculationResponse(
                levels=grid_levels,
                total_investment=round(total_investment, 2),
                price_range=round(price_range, 2),
                price_step=round(price_step, 8),
                levels_count=levels
            )
            
            # Cache the calculation for potential reuse
            cache_key = f"{min_price}_{max_price}_{levels}_{total_quantity}_{spread_factor}"
            self.cache[cache_key] = response
            
            logger.info(f"Calculated grid levels: {levels} levels, range ${min_price}-${max_price}")
            return response
            
        except Exception as e:
            logger.error(f"Error calculating grid levels: {str(e)}")
            raise
    
    async def calculate_grid_pnl(
        self,
        grid_levels: List[Dict],
        current_price: float,
        filled_orders: List[Dict]
    ) -> Dict[str, float]:
        """Calculate P&L for a grid strategy"""
        
        try:
            total_pnl = 0.0
            unrealized_pnl = 0.0
            realized_pnl = 0.0
            
            # Calculate realized P&L from filled orders
            buy_orders = [o for o in filled_orders if o.get('side') == 'buy']
            sell_orders = [o for o in filled_orders if o.get('side') == 'sell']
            
            # Simple FIFO matching for realized P&L
            for sell_order in sell_orders:
                sell_qty = sell_order.get('filled_quantity', 0)
                sell_price = sell_order.get('price', 0)
                
                remaining_qty = sell_qty
                for buy_order in buy_orders:
                    if remaining_qty <= 0:
                        break
                    
                    buy_qty = buy_order.get('filled_quantity', 0)
                    buy_price = buy_order.get('price', 0)
                    
                    if buy_qty > 0:
                        matched_qty = min(remaining_qty, buy_qty)
                        realized_pnl += matched_qty * (sell_price - buy_price)
                        
                        buy_order['filled_quantity'] -= matched_qty
                        remaining_qty -= matched_qty
            
            # Calculate unrealized P&L from remaining positions
            net_position = 0.0
            avg_entry_price = 0.0
            total_cost = 0.0
            
            for order in filled_orders:
                if order.get('side') == 'buy':
                    qty = order.get('filled_quantity', 0)
                    price = order.get('price', 0)
                    net_position += qty
                    total_cost += qty * price
                elif order.get('side') == 'sell':
                    qty = order.get('filled_quantity', 0)
                    net_position -= qty
            
            if net_position > 0 and total_cost > 0:
                avg_entry_price = total_cost / net_position
                unrealized_pnl = net_position * (current_price - avg_entry_price)
            
            total_pnl = realized_pnl + unrealized_pnl
            
            return {
                'total_pnl': round(total_pnl, 2),
                'realized_pnl': round(realized_pnl, 2),
                'unrealized_pnl': round(unrealized_pnl, 2),
                'net_position': round(net_position, 8),
                'avg_entry_price': round(avg_entry_price, 2) if avg_entry_price > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating grid P&L: {str(e)}")
            raise
    
    async def optimize_grid_spacing(
        self,
        symbol: str,
        min_price: float,
        max_price: float,
        volatility: float,
        levels: int
    ) -> Dict[str, Any]:
        """Optimize grid spacing based on volatility"""
        
        try:
            # Basic volatility-based optimization
            base_spacing = (max_price - min_price) / (levels - 1)
            
            # Adjust spacing based on volatility
            if volatility > 0.05:  # High volatility
                # Wider spacing for high volatility
                volatility_multiplier = 1.2
            elif volatility < 0.02:  # Low volatility
                # Tighter spacing for low volatility
                volatility_multiplier = 0.8
            else:
                volatility_multiplier = 1.0
            
            optimized_spacing = base_spacing * volatility_multiplier
            
            # Recalculate levels with optimized spacing
            optimized_levels = []
            current_price = min_price
            
            for i in range(levels):
                optimized_levels.append({
                    'level': i + 1,
                    'price': round(current_price, 8),
                    'spacing': round(optimized_spacing, 8)
                })
                current_price += optimized_spacing
            
            return {
                'original_spacing': round(base_spacing, 8),
                'optimized_spacing': round(optimized_spacing, 8),
                'volatility_multiplier': volatility_multiplier,
                'levels': optimized_levels,
                'total_range': round(current_price - min_price, 2)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing grid spacing: {str(e)}")
            raise
    
    async def validate_grid_parameters(
        self,
        symbol: str,
        min_price: float,
        max_price: float,
        levels: int,
        total_quantity: float,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Validate grid parameters against market conditions"""
        
        try:
            validation_result = {
                'valid': True,
                'warnings': [],
                'errors': [],
                'recommendations': []
            }
            
            # Basic parameter validation
            if min_price >= max_price:
                validation_result['errors'].append("Minimum price must be less than maximum price")
                validation_result['valid'] = False
            
            if levels < settings.MIN_GRID_LEVELS:
                validation_result['errors'].append(f"Grid levels must be at least {settings.MIN_GRID_LEVELS}")
                validation_result['valid'] = False
            
            if levels > settings.MAX_GRID_LEVELS:
                validation_result['errors'].append(f"Grid levels cannot exceed {settings.MAX_GRID_LEVELS}")
                validation_result['valid'] = False
            
            if total_quantity <= 0:
                validation_result['errors'].append("Total quantity must be positive")
                validation_result['valid'] = False
            
            # Market-based validation
            if current_price:
                if current_price < min_price or current_price > max_price:
                    validation_result['warnings'].append(
                        f"Current price ${current_price} is outside grid range ${min_price}-${max_price}"
                    )
                
                # Check if grid range is reasonable relative to current price
                price_range_pct = ((max_price - min_price) / current_price) * 100
                if price_range_pct > 50:
                    validation_result['warnings'].append(
                        f"Grid range ({price_range_pct:.1f}%) is very wide relative to current price"
                    )
                elif price_range_pct < 5:
                    validation_result['warnings'].append(
                        f"Grid range ({price_range_pct:.1f}%) is very narrow relative to current price"
                    )
            
            # Level density check
            if levels > 20:
                validation_result['warnings'].append(
                    "High number of grid levels may result in frequent rebalancing"
                )
            
            # Quantity per level check
            quantity_per_level = total_quantity / levels
            if quantity_per_level < 0.001:  # Minimum trade size check
                validation_result['warnings'].append(
                    f"Quantity per level ({quantity_per_level:.6f}) may be below minimum trade size"
                )
            
            # Investment size validation
            avg_price = (min_price + max_price) / 2
            total_investment = total_quantity * avg_price
            if total_investment > settings.MAX_POSITION_SIZE * 1000:  # Assuming position size is in units
                validation_result['warnings'].append(
                    f"Total investment (${total_investment:.2f}) is very large"
                )
            
            # Recommendations
            if validation_result['valid']:
                if levels < 10:
                    validation_result['recommendations'].append(
                        "Consider using more grid levels for better market coverage"
                    )
                
                if current_price and abs(current_price - (min_price + max_price) / 2) / current_price > 0.1:
                    validation_result['recommendations'].append(
                        "Consider centering the grid range closer to current market price"
                    )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating grid parameters: {str(e)}")
            raise
    
    def clear_cache(self):
        """Clear calculation cache"""
        self.cache.clear()
        logger.info("Grid calculation cache cleared")
