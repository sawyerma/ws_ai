"""
Bitget API-Validierung
Validiert Bitget API-Credentials mit HMAC-Signatur
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hmac
import hashlib
import time
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class BitgetCredentials(BaseModel):
    apiKey: str
    secret: str
    passphrase: str

@router.post("/validate-bitget")
async def validate_bitget_key(credentials: BitgetCredentials):
    """Validierung der Bitget API-Anmeldeinformationen"""
    try:
        logger.info("Starting Bitget API validation")
        
        # 1. Zeitstempel erstellen
        timestamp = str(int(time.time() * 1000))
        
        # 2. Nachricht für Signatur erstellen
        method = "GET"
        endpoint = "/api/spot/v1/account/info"
        message = timestamp + method + endpoint
        
        # 3. HMAC-SHA256 Signatur berechnen
        signature = hmac.new(
            credentials.secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 4. Anfrage an Bitget senden
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.bitget.com" + endpoint,
                headers={
                    "X-Bitget-Api-Key": credentials.apiKey,
                    "X-Bitget-Api-Signature": signature,
                    "X-Bitget-Api-Timestamp": timestamp,
                    "X-Bitget-Api-Passphrase": credentials.passphrase,
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            # 5. Antwort auswerten
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "00000":
                    logger.info("✅ Bitget API validation successful")
                    return {
                        "valid": True, 
                        "is_premium": True,
                        "account_type": "verified",
                        "limits": {
                            "max_rps": 120,
                            "max_symbols": 100,
                            "resolutions": [1, 5, 15, 30, 60, 240, 360, 720, 1440]
                        }
                    }
                else:
                    logger.warning(f"Bitget API error: {data}")
                    return {"valid": False, "error": f"API error: {data.get('msg', 'Unknown error')}"}
            elif response.status_code == 401:
                logger.warning("Bitget API authentication failed")
                return {"valid": False, "error": "Invalid credentials"}
            else:
                logger.error(f"Bitget API unexpected status: {response.status_code}")
                return {"valid": False, "error": f"API error: {response.status_code}"}
                
    except httpx.TimeoutException:
        logger.error("Bitget API timeout")
        return {"valid": False, "error": "API timeout"}
    except Exception as e:
        logger.error(f"Bitget validation failed: {str(e)}")
        raise HTTPException(500, f"Validation failed: {str(e)}")
