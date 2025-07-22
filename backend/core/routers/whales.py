"""
Whale Monitoring API Routes
Provides endpoints for whale transaction data and system status
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from db.clickhouse_whales import fetch_whale_events, get_whale_client
from whales.collector_manager_whales import collector_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whales", tags=["whales"])


@router.get("/recent")
async def get_recent_whale_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    symbol: Optional[str] = Query(default=None),
    chain: Optional[str] = Query(default=None),
    min_amount_usd: Optional[float] = Query(default=None),
    hours: Optional[int] = Query(default=24, ge=1, le=168)  # Max 1 week
):
    """
    Get recent whale events with optional filtering
    
    Args:
        limit: Maximum number of events to return (1-200)
        offset: Number of events to skip for pagination
        symbol: Filter by coin symbol (e.g., 'BTC', 'ETH')
        chain: Filter by blockchain (e.g., 'ethereum', 'binance')
        min_amount_usd: Minimum USD amount filter
        hours: Time window in hours (default: 24, max: 168)
    
    Returns:
        JSON object with whale events and metadata
    """
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Fetch whale events
        events = fetch_whale_events(
            symbol=symbol,
            limit=limit
        )
        
        # Apply additional filters
        if chain:
            events = [e for e in events if e.get('chain', '').lower() == chain.lower()]
        
        if min_amount_usd:
            events = [e for e in events if e.get('amount_usd', 0) >= min_amount_usd]
        
        # Apply time filter
        filtered_events = []
        for event in events:
            try:
                event_time = datetime.fromisoformat(event['ts'].replace('Z', '+00:00'))
                if start_time <= event_time <= end_time:
                    filtered_events.append(event)
            except (ValueError, KeyError):
                continue
        
        # Apply limit after filtering
        filtered_events = filtered_events[:limit]
        
        # Calculate summary statistics
        total_volume = sum(e.get('amount_usd', 0) for e in filtered_events)
        cross_border_count = sum(1 for e in filtered_events if e.get('is_cross_border', 0))
        
        # Chain distribution
        chain_stats = {}
        for event in filtered_events:
            chain = event.get('chain', 'unknown')
            if chain not in chain_stats:
                chain_stats[chain] = {'count': 0, 'volume': 0}
            chain_stats[chain]['count'] += 1
            chain_stats[chain]['volume'] += event.get('amount_usd', 0)
        
        return {
            "events": filtered_events,
            "metadata": {
                "total_count": len(filtered_events),
                "total_volume_usd": total_volume,
                "cross_border_count": cross_border_count,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours": hours
                },
                "chain_distribution": chain_stats,
                "filters": {
                    "symbol": symbol,
                    "chain": chain,
                    "min_amount_usd": min_amount_usd,
                    "limit": limit,
                    "offset": offset
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching whale events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch whale events: {str(e)}")


@router.get("/status")
async def get_whale_system_status():
    """
    Get whale monitoring system status
    
    Returns:
        JSON object with system status information
    """
    try:
        client = get_whale_client()
        
        # Get basic event statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_events,
                SUM(amount_usd) as total_volume,
                MAX(ts) as latest_event,
                MIN(ts) as earliest_event,
                COUNT(DISTINCT chain) as active_chains
            FROM whale_events
            WHERE ts >= now() - INTERVAL 24 HOUR
        """
        
        stats_result = client.query(stats_query)
        stats = dict(zip(stats_result.column_names, stats_result.result_rows[0])) if stats_result.result_rows else {}
        
        # Get collector status
        collector_status = {}
        for collector_name, collector in collector_manager.collectors.items():
            collector_status[collector_name] = {
                "running": collector.running if hasattr(collector, 'running') else False,
                "last_block": getattr(collector, 'last_block', 0)
            }
        
        # Calculate backfill progress
        latest_event = stats.get('latest_event')
        backfill_date = "15.01.2025"  # Default fallback
        backfill_status = "Running"
        
        if latest_event:
            latest_dt = datetime.fromisoformat(str(latest_event).replace('Z', '+00:00'))
            now = datetime.now()
            hours_behind = (now - latest_dt).total_seconds() / 3600
            
            if hours_behind < 1:
                backfill_status = "Completed"
                backfill_date = now.strftime("%d.%m.%Y")
            elif hours_behind < 24:
                backfill_status = "Running"
                backfill_date = latest_dt.strftime("%d.%m.%Y")
            else:
                backfill_status = "Error"
        
        # Test status (simple health check)
        test_status = "passed"
        try:
            # Simple connectivity test
            test_query = "SELECT 1"
            client.query(test_query)
        except Exception:
            test_status = "failed"
        
        return {
            "system_status": "online",
            "backfill_status": backfill_status,
            "backfill_date": backfill_date,
            "test_status": test_status,
            "last_test_run": datetime.now().isoformat(),
            "statistics": {
                "total_events_24h": stats.get('total_events', 0),
                "total_volume_24h": stats.get('total_volume', 0),
                "latest_event": str(latest_event) if latest_event else None,
                "earliest_event": str(stats.get('earliest_event')) if stats.get('earliest_event') else None,
                "active_chains": stats.get('active_chains', 0)
            },
            "collectors": collector_status,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting whale system status: {e}")
        return {
            "system_status": "error",
            "backfill_status": "Error",
            "backfill_date": "15.01.2025",
            "test_status": "failed",
            "last_test_run": datetime.now().isoformat(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/statistics")
async def get_whale_statistics(
    days: int = Query(default=7, ge=1, le=30)
):
    """
    Get whale statistics for dashboard
    
    Args:
        days: Number of days to analyze (1-30)
    
    Returns:
        JSON object with comprehensive statistics
    """
    try:
        client = get_whale_client()
        
        # Time-based volume analysis
        volume_query = f"""
            SELECT 
                toDate(ts) as date,
                COUNT(*) as events,
                SUM(amount_usd) as volume,
                AVG(amount_usd) as avg_volume
            FROM whale_events
            WHERE ts >= now() - INTERVAL {days} DAY
            GROUP BY date
            ORDER BY date DESC
        """
        
        volume_result = client.query(volume_query)
        daily_stats = [
            dict(zip(volume_result.column_names, row))
            for row in volume_result.result_rows
        ]
        
        # Chain distribution
        chain_query = f"""
            SELECT 
                chain,
                COUNT(*) as events,
                SUM(amount_usd) as volume
            FROM whale_events
            WHERE ts >= now() - INTERVAL {days} DAY
            GROUP BY chain
            ORDER BY volume DESC
        """
        
        chain_result = client.query(chain_query)
        chain_stats = [
            dict(zip(chain_result.column_names, row))
            for row in chain_result.result_rows
        ]
        
        # Top symbols
        symbol_query = f"""
            SELECT 
                symbol,
                COUNT(*) as events,
                SUM(amount_usd) as volume
            FROM whale_events
            WHERE ts >= now() - INTERVAL {days} DAY
            GROUP BY symbol
            ORDER BY volume DESC
            LIMIT 10
        """
        
        symbol_result = client.query(symbol_query)
        symbol_stats = [
            dict(zip(symbol_result.column_names, row))
            for row in symbol_result.result_rows
        ]
        
        # Cross-border analysis
        cross_border_query = f"""
            SELECT 
                is_cross_border,
                COUNT(*) as events,
                SUM(amount_usd) as volume
            FROM whale_events
            WHERE ts >= now() - INTERVAL {days} DAY
            GROUP BY is_cross_border
        """
        
        cross_border_result = client.query(cross_border_query)
        cross_border_stats = [
            dict(zip(cross_border_result.column_names, row))
            for row in cross_border_result.result_rows
        ]
        
        return {
            "daily_statistics": daily_stats,
            "chain_distribution": chain_stats,
            "top_symbols": symbol_stats,
            "cross_border_analysis": cross_border_stats,
            "time_range": {
                "days": days,
                "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
                "end_date": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching whale statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")


@router.get("/health")
async def whale_health_check():
    """
    Simple health check endpoint
    
    Returns:
        JSON object with health status
    """
    try:
        client = get_whale_client()
        
        # Test database connectivity
        test_query = "SELECT COUNT(*) FROM whale_events LIMIT 1"
        result = client.query(test_query)
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Whale health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
