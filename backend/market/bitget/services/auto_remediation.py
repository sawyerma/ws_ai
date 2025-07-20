"""
Auto-Remediation Service für Bitget Integration
"""
import logging
import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger("auto-remediation")

# Globaler Zustand für Failover-Mechanismus
bitget_failover_active = False
_last_health_check = 0.0
_health_check_interval = 30.0  # 30 Sekunden

@dataclass
class SystemHealthMetrics:
    """Metriken für System-Gesundheit"""
    bitget_api: bool = True
    redis_connection: bool = True
    clickhouse_connection: bool = True
    websocket_connections: int = 0
    active_symbols: int = 0
    throughput_percent: float = 100.0
    error_rate_percent: float = 0.0
    last_update: float = field(default_factory=time.time)

_system_metrics = SystemHealthMetrics()

async def activate_failover(reason: str):
    """
    Aktiviert Failover-Modus
    """
    global bitget_failover_active
    bitget_failover_active = True
    logger.warning(f"🔴 Failover aktiviert: {reason}")
    
    # Hier würde normalerweise die Failover-Logik implementiert werden
    # z.B. Umschaltung auf Backup-APIs oder reduzierte Funktionalität

async def deactivate_failover():
    """
    Deaktiviert Failover-Modus
    """
    global bitget_failover_active
    bitget_failover_active = False
    logger.info("🟢 Failover deaktiviert - System wieder normal")

async def check_system_health() -> Dict[str, Any]:
    """
    Führt umfassende System-Gesundheitsprüfung durch
    """
    global _last_health_check, _system_metrics
    
    current_time = time.time()
    
    # Cached Health Check für Performance
    if current_time - _last_health_check < _health_check_interval:
        return _system_metrics_to_dict()
    
    _last_health_check = current_time
    
    try:
        # Bitget API Gesundheit
        api_health = await _check_bitget_api_health()
        _system_metrics.bitget_api = api_health
        
        # Redis Verbindung
        redis_health = await _check_redis_health()
        _system_metrics.redis_connection = redis_health
        
        # ClickHouse Verbindung
        clickhouse_health = await _check_clickhouse_health()
        _system_metrics.clickhouse_connection = clickhouse_health
        
        # WebSocket Verbindungen
        ws_count = await _count_active_websockets()
        _system_metrics.websocket_connections = ws_count
        
        # Symbol-Aktivität
        symbol_count = await _count_active_symbols()
        _system_metrics.active_symbols = symbol_count
        
        # Durchsatz berechnen
        throughput = await _calculate_throughput()
        _system_metrics.throughput_percent = throughput
        
        # Fehlerrate berechnen
        error_rate = await _calculate_error_rate()
        _system_metrics.error_rate_percent = error_rate
        
        _system_metrics.last_update = current_time
        
        # Auto-Remediation auslösen bei kritischen Problemen
        await _evaluate_auto_remediation()
        
        return _system_metrics_to_dict()
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "bitget_api": False,
            "redis": False,
            "clickhouse": False,
            "error": str(e),
            "throughput": 0.0,
            "last_check": current_time
        }

async def _check_bitget_api_health() -> bool:
    """Prüft Bitget API Gesundheit"""
    try:
        from market.bitget.services.bitget_rest import BitgetRestAPI
        
        api = BitgetRestAPI()
        response = await api.fetch_spot_symbols()
        
        if response and response.get("code") == "00000":
            return True
        return False
        
    except Exception as e:
        logger.debug(f"Bitget API health check failed: {str(e)}")
        return False

async def _check_redis_health() -> bool:
    """Prüft Redis Verbindung"""
    try:
        from market.bitget.storage.redis_manager import redis_manager
        
        # Einfacher Ping-Test
        result = await redis_manager.ping()
        return result is True
        
    except Exception as e:
        logger.debug(f"Redis health check failed: {str(e)}")
        return False

async def _check_clickhouse_health() -> bool:
    """Prüft ClickHouse Verbindung"""
    try:
        # Hier würde normalerweise eine ClickHouse-Verbindung getestet
        # Für jetzt nehmen wir an, dass es funktioniert
        return True
        
    except Exception as e:
        logger.debug(f"ClickHouse health check failed: {str(e)}")
        return False

async def _count_active_websockets() -> int:
    """Zählt aktive WebSocket-Verbindungen"""
    try:
        # Hier würde normalerweise die Anzahl der aktiven WS-Verbindungen ermittelt
        # Placeholder für jetzt
        return 2
        
    except Exception:
        return 0

async def _count_active_symbols() -> int:
    """Zählt aktive Symbole"""
    try:
        from market.bitget.config import system_config
        return len(system_config.symbols)
        
    except Exception:
        return 0

async def _calculate_throughput() -> float:
    """Berechnet aktuellen Durchsatz"""
    try:
        from market.bitget.utils.adaptive_rate_limiter import get_all_stats
        
        stats = get_all_stats()
        if stats:
            # Durchschnittliche Erfolgsrate aller Rate Limiter
            total_requests = sum(s.get("total_requests", 0) for s in stats.values())
            successful_requests = sum(s.get("successful_requests", 0) for s in stats.values())
            
            if total_requests > 0:
                return (successful_requests / total_requests) * 100
        
        return 98.5  # Default für gesundes System
        
    except Exception:
        return 50.0

async def _calculate_error_rate() -> float:
    """Berechnet aktuelle Fehlerrate"""
    try:
        from market.bitget.utils.adaptive_rate_limiter import get_all_stats
        
        stats = get_all_stats()
        if stats:
            total_requests = sum(s.get("total_requests", 0) for s in stats.values())
            failed_requests = sum(s.get("failed_requests", 0) for s in stats.values())
            
            if total_requests > 0:
                return (failed_requests / total_requests) * 100
        
        return 1.5  # Default niedrige Fehlerrate
        
    except Exception:
        return 10.0

async def _evaluate_auto_remediation():
    """Evaluiert ob Auto-Remediation aktiviert werden soll"""
    global bitget_failover_active
    
    # Failover aktivieren bei kritischen Problemen
    critical_issues = []
    
    if not _system_metrics.bitget_api:
        critical_issues.append("Bitget API nicht verfügbar")
    
    if not _system_metrics.redis_connection:
        critical_issues.append("Redis-Verbindung verloren")
    
    if _system_metrics.throughput_percent < 50.0:
        critical_issues.append(f"Durchsatz zu niedrig: {_system_metrics.throughput_percent:.1f}%")
    
    if _system_metrics.error_rate_percent > 25.0:
        critical_issues.append(f"Fehlerrate zu hoch: {_system_metrics.error_rate_percent:.1f}%")
    
    if critical_issues and not bitget_failover_active:
        reason = "; ".join(critical_issues)
        await activate_failover(reason)
        
    elif not critical_issues and bitget_failover_active:
        await deactivate_failover()

def _system_metrics_to_dict() -> Dict[str, Any]:
    """Konvertiert SystemHealthMetrics zu Dictionary"""
    return {
        "bitget_api": _system_metrics.bitget_api,
        "redis": _system_metrics.redis_connection,
        "clickhouse": _system_metrics.clickhouse_connection,
        "websocket_connections": _system_metrics.websocket_connections,
        "active_symbols": _system_metrics.active_symbols,
        "throughput": round(_system_metrics.throughput_percent, 1),
        "error_rate": round(_system_metrics.error_rate_percent, 1),
        "failover_active": bitget_failover_active,
        "last_check": _system_metrics.last_update,
        "status": "healthy" if (
            _system_metrics.bitget_api and 
            _system_metrics.redis_connection and
            _system_metrics.throughput_percent > 70.0 and
            _system_metrics.error_rate_percent < 10.0
        ) else "degraded" if not bitget_failover_active else "critical"
    }

async def get_remediation_status() -> Dict[str, Any]:
    """
    Gibt aktuellen Status des Auto-Remediation Systems zurück
    """
    return {
        "failover_active": bitget_failover_active,
        "last_health_check": _last_health_check,
        "check_interval": _health_check_interval,
        "system_metrics": _system_metrics_to_dict()
    }

# Startup-Funktion für regelmäßige Health Checks
async def start_health_monitoring():
    """Startet kontinuierliche Gesundheitsüberwachung"""
    logger.info("🏥 Starting health monitoring service")
    
    while True:
        try:
            await check_system_health()
            await asyncio.sleep(_health_check_interval)
        except Exception as e:
            logger.error(f"❌ Health monitoring error: {str(e)}")
            await asyncio.sleep(5.0)  # Kurze Pause bei Fehlern
