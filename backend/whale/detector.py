# /backend/whale/detector.py

import os
import logging
import traceback
import time
import uuid
from typing import Dict, Any, Optional
from web3 import Web3
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # Fallback for newer web3 versions
    try:
        from web3.middleware.geth_poa import geth_poa_middleware
    except ImportError:
        # Fallback if middleware doesn't exist
        geth_poa_middleware = None
from whale.settings import fetch_active_coin_map
import clickhouse_connect

# Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = ""
CLICKHOUSE_DB = "bitget"

ETHEREUM_NODE_URL = os.getenv("ETHEREUM_NODE_URL", "wss://mainnet.infura.io/ws/v3/YOUR_INFURA_PROJECT_ID")
CHAIN = "ethereum"

ERC20_TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()

# --- Heartbeat für Healthcheck ---
_detector_last_heartbeat = 0

def heartbeat():
    global _detector_last_heartbeat
    _detector_last_heartbeat = int(time.time())

def is_detector_alive(timeout=60):
    return (int(time.time()) - _detector_last_heartbeat) < timeout

def get_client():
    try:
        return clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DB,
        )
    except Exception as e:
        logger.error(f"Failed to create ClickHouse client: {e}")
        traceback.print_exc()
        raise

def insert_whale_event(event: Dict[str, Any]):
    try:
        client = get_client()
        sql = """
        INSERT INTO whale_events (
            event_id, ts, chain, tx_hash, from_addr, to_addr,
            token, symbol, amount, is_native, exchange
        )
        VALUES (
            %(event_id)s, %(ts)s, %(chain)s, %(tx_hash)s, %(from_addr)s, %(to_addr)s,
            %(token)s, %(symbol)s, %(amount)s, %(is_native)s, %(exchange)s
        )
        """
        client.command(sql, event)
        logger.info(f"[WHLE_EVENT] {event['symbol']} {event['amount']} ({event['exchange']}) {event['tx_hash'][:10]}...")
    except Exception as e:
        logger.error(f"Failed to insert whale_event: {e}")
        traceback.print_exc()
        raise

def decode_address(address):
    if isinstance(address, bytes):
        return Web3.to_checksum_address(address[-20:])
    elif isinstance(address, str) and address.startswith("0x") and len(address) == 42:
        return Web3.to_checksum_address(address)
    return address

def run_whale_detection(min_eth: float = 100.0):
    logger.info("Starting Whale-Detection Service...")
    w3 = Web3(Web3.WebsocketProvider(ETHEREUM_NODE_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    coin_map = fetch_active_coin_map()

    while True:
        try:
            heartbeat()  # Heartbeat für Healthcheck setzen
            latest = w3.eth.block_number
            logger.info(f"Scanning block {latest}...")
            block = w3.eth.get_block(latest, full_transactions=True)
            ts = block['timestamp']
            for tx in block['transactions']:
                # Native ETH transfers
                if tx['value'] >= int(min_eth * 1e18):
                    from_addr = decode_address(tx['from'])
                    to_addr = decode_address(tx['to'])
                    symbol = "ETH"
                    key = (symbol, CHAIN)
                    mapping = coin_map.get(key)
                    exchange = mapping['exchange'] if mapping else "none"
                    active = mapping['active'] if mapping else 0
                    if active:
                        event = dict(
                            event_id=str(uuid.uuid4()),
                            ts=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts)),
                            chain=CHAIN,
                            tx_hash=tx['hash'].hex(),
                            from_addr=from_addr,
                            to_addr=to_addr,
                            token="ETH",
                            symbol=symbol,
                            amount=tx['value'] / 1e18,
                            is_native=1,
                            exchange=exchange
                        )
                        insert_whale_event(event)
                # ERC-20 Transfers
                if tx['to'] is not None:
                    receipt = w3.eth.get_transaction_receipt(tx['hash'])
                    for log in receipt['logs']:
                        if log['topics'] and log['topics'][0].hex() == ERC20_TRANSFER_TOPIC:
                            contract = log['address']
                            from_addr = decode_address('0x'+log['topics'][1].hex()[-40:])
                            to_addr = decode_address('0x'+log['topics'][2].hex()[-40:])
                            amount = int(log['data'], 16)
                            key = (contract, CHAIN)
                            # Try to match ERC-20 token by contract address (in coins mapping)
                            for ckey, mapping in coin_map.items():
                                if mapping['contract_addr'].lower() == contract.lower():
                                    symbol = mapping['symbol']
                                    exchange = mapping['exchange']
                                    active = mapping['active']
                                    decimals = 18  # Default fallback, can be extended
                                    # min_amount-Check optional je Token
                                    if active:
                                        event = dict(
                                            event_id=str(uuid.uuid4()),
                                            ts=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts)),
                                            chain=CHAIN,
                                            tx_hash=tx['hash'].hex(),
                                            from_addr=from_addr,
                                            to_addr=to_addr,
                                            token=contract,
                                            symbol=symbol,
                                            amount=amount / (10 ** decimals),
                                            is_native=0,
                                            exchange=exchange
                                        )
                                        insert_whale_event(event)
            # Sleep bis nächster Block (~12s bei Ethereum)
            time.sleep(10)
            coin_map = fetch_active_coin_map()  # Optional: mapping zyklisch aktualisieren
        except Exception as e:
            logger.error(f"Error in whale detection loop: {e}")
            traceback.print_exc()
            time.sleep(5)
