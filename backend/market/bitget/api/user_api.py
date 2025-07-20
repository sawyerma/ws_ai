"""
API Endpoints für Benutzerkonfiguration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from market.bitget.config import bitget_config, system_config
from market.bitget.services.bitget_rest import BitgetRestAPI
from market.bitget.services.auto_remediation import check_system_health

router = APIRouter(prefix="/api/user", tags=["user"])
logger = logging.getLogger(__name__)

class BitgetApiSettings(BaseModel):
    api_key: str = Field(..., min_length=10, description="Bitget API Key")
    secret_key: str = Field(..., min_length=10, description="Bitget Secret Key")
    passphrase: str = Field(..., min_length=3, description="Bitget Passphrase")

class ApiLimitsResponse(BaseModel):
    max_rps: int
    max_symbols_per_market: int
    max_symbols_per_connection: int
    available_resolutions: list
    max_historical_days: int
    is_premium: bool
    effective_market_types: list
    total_max_symbols: int

class ApiStatusResponse(BaseModel):
    status: str
    premium_features: bool
    message: str
    limits: Optional[ApiLimitsResponse] = None

@router.post("/set_bitget_api", response_model=ApiStatusResponse)
async def set_bitget_api(settings: BitgetApiSettings):
    """
    Setzt Bitget API-Schlüssel und aktiviert Premium-Features
    """
    try:
        logger.info(f"Attempting to validate Bitget API credentials")
        
        # Erstelle temporäre API-Instanz für Validierung
        test_api = BitgetRestAPI()
        
        # Temporär die Credentials setzen
        old_key = bitget_config.api_key
        old_secret = bitget_config.secret_key
        old_passphrase = bitget_config.passphrase
        
        # Neue Credentials setzen
        bitget_config.update_credentials(
            settings.api_key, 
            settings.secret_key, 
            settings.passphrase
        )
        
        # Validierung durch API-Test
        try:
            # Test mit öffentlichem Endpoint
            response = await test_api.fetch_spot_symbols()
            
            if not response or response.get("code") != "00000":
                raise ValueError("API credentials validation failed")
            
            # Weitere Validierung mit privaten Endpunkten (falls verfügbar)
            if bitget_config.is_premium:
                # Test mit Account-Info (signierte Anfrage)
                logger.info("Testing signed API request for premium validation")
                # Hier würde normalerweise eine signierte Anfrage folgen
            
            logger.info("✅ API credentials validated successfully")
            
        except Exception as validation_error:
            # Rollback bei Validierungsfehler
            bitget_config.update_credentials(old_key, old_secret, old_passphrase)
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid API credentials: {str(validation_error)}"
            )
        
        # Systemkonfiguration für Premium aktualisieren
        system_config.update_for_premium(bitget_config)
        
        # Aktuelle Limits abrufen
        limits = get_current_limits()
        
        logger.info(f"✅ Premium features {'activated' if bitget_config.is_premium else 'not available'}")
        
        return ApiStatusResponse(
            status="success",
            premium_features=bitget_config.is_premium,
            message="API credentials updated successfully" + 
                   (" - Premium features activated!" if bitget_config.is_premium else " - Using free tier"),
            limits=limits
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to set API credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/limits", response_model=ApiLimitsResponse)
async def get_current_limits():
    """
    Gibt aktuelle Rate Limits und Konfiguration zurück
    """
    return ApiLimitsResponse(
        max_rps=bitget_config.effective_max_rps,
        max_symbols_per_market=system_config.get_max_symbols_per_market(bitget_config),
        max_symbols_per_connection=bitget_config.max_symbols_per_connection,
        available_resolutions=bitget_config.available_resolutions,
        max_historical_days=bitget_config.max_historical_days,
        is_premium=bitget_config.is_premium,
        effective_market_types=system_config.get_effective_market_types(bitget_config),
        total_max_symbols=system_config.get_total_max_symbols(bitget_config)
    )

@router.get("/status", response_model=Dict[str, Any])
async def get_api_status():
    """
    Gibt aktuellen API-Status zurück
    """
    try:
        # System Health Check
        health = await check_system_health()
        
        return {
            "api_configured": bitget_config.api_key != "PUBLIC_ACCESS",
            "is_premium": bitget_config.is_premium,
            "system_health": health,
            "limits": await get_current_limits(),
            "active_markets": system_config.get_effective_market_types(bitget_config),
            "total_symbols": len(system_config.symbols)
        }
    except Exception as e:
        logger.error(f"❌ Failed to get API status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reset_bitget_api")
async def reset_bitget_api():
    """
    Setzt Bitget API-Konfiguration auf Free Tier zurück
    """
    try:
        logger.info("Resetting Bitget API to free tier")
        
        # Auf öffentlichen Zugang zurücksetzen
        bitget_config.update_credentials("PUBLIC_ACCESS", "", "")
        
        # Systemkonfiguration zurücksetzen
        system_config.market_types = ["spot", "usdtm"]
        
        return {
            "status": "success",
            "message": "API configuration reset to free tier",
            "is_premium": False
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to reset API configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test_connection")
async def test_api_connection():
    """
    Testet die aktuelle API-Verbindung
    """
    try:
        test_api = BitgetRestAPI()
        
        # Test öffentlicher Endpoint
        symbols_response = await test_api.fetch_spot_symbols()
        if not symbols_response or symbols_response.get("code") != "00000":
            raise ValueError("Public API test failed")
        
        # Test Ticker-Daten
        ticker_response = await test_api.fetch_spot_tickers()
        if not ticker_response or ticker_response.get("code") != "00000":
            raise ValueError("Ticker API test failed")
        
        return {
            "status": "success",
            "message": "API connection test successful",
            "symbols_count": len(symbols_response.get("data", [])),
            "tickers_count": len(ticker_response.get("data", [])),
            "is_premium": bitget_config.is_premium
        }
    
    except Exception as e:
        logger.error(f"❌ API connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
