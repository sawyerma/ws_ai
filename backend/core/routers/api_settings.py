from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional, Union
import aiohttp
import asyncio
import logging
import os
from datetime import datetime
import hmac
import hashlib
import time

logger = logging.getLogger(__name__)

router = APIRouter()

class APIKeysRequest(BaseModel):
    keys: Dict[str, Union[str, Dict[str, str]]]

class ValidateAPIKeyRequest(BaseModel):
    provider: str
    apiKey: str
    secret: Optional[str] = None
    passphrase: Optional[str] = None

class APIKeysResponse(BaseModel):
    keys: Dict[str, str]
    lastChecked: Optional[Dict[str, str]] = None

class ValidateAPIKeyResponse(BaseModel):
    valid: bool
    message: Optional[str] = None

# In-memory storage (in production, use database or secure file storage)
_api_keys_storage: Dict[str, str] = {}
_last_checked_storage: Dict[str, str] = {}

@router.get("/api/settings/api-keys", response_model=APIKeysResponse)
async def get_api_keys():
    """Get saved API keys (masked for security)"""
    try:
        # Mask keys for security (show only first 8 and last 4 characters)
        masked_keys = {}
        for provider, key in _api_keys_storage.items():
            if key and len(key) > 12:
                masked_keys[provider] = f"{key[:8]}...{key[-4:]}"
            elif key:
                masked_keys[provider] = key
            else:
                masked_keys[provider] = ""
        
        return APIKeysResponse(
            keys=masked_keys,
            lastChecked=_last_checked_storage
        )
    except Exception as e:
        logger.error(f"Failed to get API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve API keys")

@router.post("/api/settings/api-keys", response_model=dict)
async def save_api_keys(request: APIKeysRequest):
    """Save API keys securely"""
    try:
        # Validate input
        if not request.keys:
            raise HTTPException(status_code=400, detail="No API keys provided")
        
        # Store keys (in production, encrypt before storing)
        for provider, key in request.keys.items():
            if key.strip():  # Only store non-empty keys
                _api_keys_storage[provider] = key.strip()
                logger.info(f"Saved API key for {provider}")
            else:
                # Remove empty keys
                _api_keys_storage.pop(provider, None)
                _last_checked_storage.pop(provider, None)
        
        return {"message": "API keys saved successfully", "count": len(request.keys)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to save API keys")

@router.post("/api/settings/validate-api-key", response_model=ValidateAPIKeyResponse)
async def validate_api_key(request: ValidateAPIKeyRequest):
    """Validate an API key by making a test request"""
    try:
        if not request.apiKey.strip():
            return ValidateAPIKeyResponse(valid=False, message="API key is empty")
        
        # Validation logic for each provider
        is_valid = False
        message = "Unknown provider"
        
        if request.provider == "etherscan":
            is_valid, message = await _validate_etherscan_key(request.apiKey)
        elif request.provider == "bscscan":
            is_valid, message = await _validate_bscscan_key(request.apiKey)
        elif request.provider == "polygonscan":
            is_valid, message = await _validate_polygonscan_key(request.apiKey)
        elif request.provider == "coingecko":
            is_valid, message = await _validate_coingecko_key(request.apiKey)
        elif request.provider == "bitget":
            if not request.secret or not request.passphrase:
                return ValidateAPIKeyResponse(valid=False, message="Bitget requires API Key, Secret, and Passphrase")
            is_valid, message = await _validate_bitget_key(request.apiKey, request.secret, request.passphrase)
        else:
            return ValidateAPIKeyResponse(valid=False, message=f"Unknown provider: {request.provider}")
        
        # Update last checked timestamp
        if is_valid:
            _last_checked_storage[request.provider] = datetime.now().isoformat()
        
        return ValidateAPIKeyResponse(valid=is_valid, message=message)
        
    except Exception as e:
        logger.error(f"Failed to validate API key for {request.provider}: {e}")
        return ValidateAPIKeyResponse(valid=False, message="Validation failed due to network error")

async def _validate_etherscan_key(api_key: str) -> tuple[bool, str]:
    """Validate Etherscan API key"""
    try:
        url = "https://api.etherscan.io/api"
        params = {
            "module": "stats",
            "action": "ethsupply",
            "apikey": api_key
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1":
                        return True, "Valid Etherscan API key"
                    else:
                        return False, f"Etherscan API error: {data.get('message', 'Unknown error')}"
                else:
                    return False, f"HTTP {response.status}: {response.reason}"
    except asyncio.TimeoutError:
        return False, "Request timeout - check your internet connection"
    except Exception as e:
        return False, f"Network error: {str(e)}"

async def _validate_bscscan_key(api_key: str) -> tuple[bool, str]:
    """Validate BSCScan API key"""
    try:
        url = "https://api.bscscan.com/api"
        params = {
            "module": "stats",
            "action": "bnbsupply",
            "apikey": api_key
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1":
                        return True, "Valid BSCScan API key"
                    else:
                        return False, f"BSCScan API error: {data.get('message', 'Unknown error')}"
                else:
                    return False, f"HTTP {response.status}: {response.reason}"
    except asyncio.TimeoutError:
        return False, "Request timeout - check your internet connection"
    except Exception as e:
        return False, f"Network error: {str(e)}"

async def _validate_polygonscan_key(api_key: str) -> tuple[bool, str]:
    """Validate PolygonScan API key"""
    try:
        url = "https://api.polygonscan.com/api"
        params = {
            "module": "stats",
            "action": "maticprice",
            "apikey": api_key
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1":
                        return True, "Valid PolygonScan API key"
                    else:
                        return False, f"PolygonScan API error: {data.get('message', 'Unknown error')}"
                else:
                    return False, f"HTTP {response.status}: {response.reason}"
    except asyncio.TimeoutError:
        return False, "Request timeout - check your internet connection"
    except Exception as e:
        return False, f"Network error: {str(e)}"

async def _validate_coingecko_key(api_key: str) -> tuple[bool, str]:
    """Validate CoinGecko API key"""
    try:
        # CoinGecko Pro API endpoint
        url = "https://pro-api.coingecko.com/api/v3/ping"
        headers = {
            "x-cg-pro-api-key": api_key
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "gecko_says" in data:
                        return True, "Valid CoinGecko Pro API key"
                    else:
                        return False, "Invalid CoinGecko API response"
                elif response.status == 401:
                    return False, "Invalid CoinGecko API key"
                else:
                    return False, f"HTTP {response.status}: {response.reason}"
    except asyncio.TimeoutError:
        return False, "Request timeout - check your internet connection"
    except Exception as e:
        # Try free API as fallback
        try:
            url = "https://api.coingecko.com/api/v3/ping"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return True, "CoinGecko free API accessible (Pro key may be invalid)"
                    else:
                        return False, f"CoinGecko API not accessible: HTTP {response.status}"
        except:
            return False, f"Network error: {str(e)}"

async def _validate_bitget_key(api_key: str, secret: str, passphrase: str) -> tuple[bool, str]:
    """Validate Bitget API key with HMAC signature"""
    try:
        # 1. Zeitstempel erstellen
        timestamp = str(int(time.time() * 1000))
        
        # 2. Nachricht für Signatur erstellen
        method = "GET"
        endpoint = "/api/spot/v1/account/info"
        message = timestamp + method + endpoint
        
        # 3. HMAC-SHA256 Signatur berechnen
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 4. Anfrage an Bitget senden
        headers = {
            "X-Bitget-Api-Key": api_key,
            "X-Bitget-Api-Signature": signature,
            "X-Bitget-Api-Timestamp": timestamp,
            "X-Bitget-Api-Passphrase": passphrase,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"https://api.bitget.com{endpoint}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == "00000":
                        return True, "Valid Bitget API credentials - Premium features activated"
                    else:
                        return False, f"Bitget API error: {data.get('msg', 'Unknown error')}"
                elif response.status == 401:
                    return False, "Invalid Bitget API credentials"
                else:
                    return False, f"Bitget API error: HTTP {response.status}"
                    
    except asyncio.TimeoutError:
        return False, "Bitget API timeout - check your internet connection"
    except Exception as e:
        logger.error(f"Bitget validation error: {str(e)}")
        return False, f"Validation error: {str(e)}"

# Health check endpoint
@router.get("/api/settings/health")
async def health_check():
    """Health check for settings API"""
    return {
        "status": "healthy",
        "service": "api_settings",
        "timestamp": datetime.now().isoformat(),
        "stored_keys": len(_api_keys_storage)
    }
