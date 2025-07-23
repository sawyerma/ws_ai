# backend/core/routers/exchange_factory.py
import logging
from importlib import import_module

logger = logging.getLogger("exchange-factory")

class ExchangeFactory:
    @staticmethod
    def get_service(exchange, service_type, *args, **kwargs):
        """Dynamisch Exchange-spezifische Services laden"""
        try:
            module = import_module(f"market.{exchange}.services.{service_type}")
            class_name = f"{exchange.capitalize()}{service_type.capitalize()}"
            return getattr(module, class_name)(*args, **kwargs)
        except (ImportError, AttributeError) as e:
            logger.error(f"Service not available: {exchange}.{service_type} - {str(e)}")
            return None

    @staticmethod
    def get_storage(exchange, storage_type):
        """Holt Storage-Manager (Redis/ClickHouse)"""
        try:
            module = import_module(f"market.{exchange}.storage.{storage_type}_manager")
            class_name = f"{exchange.capitalize()}{storage_type.capitalize()}Manager"
            return getattr(module, class_name)()
        except (ImportError, AttributeError) as e:
            logger.error(f"Storage not available: {exchange}.{storage_type} - {str(e)}")
            return None

    @staticmethod
    def get_collector(exchange, symbol, market):
        """Holt Collector-Instanz für Symbol/Markt"""
        try:
            module = import_module(f"market.{exchange}.collector")
            symbol_key = f"{symbol}_{market}"
            return getattr(module, "collectors").get(symbol_key)
        except (ImportError, AttributeError) as e:
            logger.error(f"Collector not available: {exchange}/{symbol}/{market} - {str(e)}")
            return None

    @staticmethod
    def get_rest_api(exchange):
        """Holt REST API Client"""
        return ExchangeFactory.get_service(exchange, "rest_api")

    @staticmethod
    def get_historical_manager(exchange):
        """Holt Backfill Manager"""
        try:
            module = import_module(f"market.{exchange}.historical")
            return getattr(module, f"{exchange.capitalize()}Backfill")()
        except (ImportError, AttributeError) as e:
            logger.error(f"Historical manager not available: {exchange} - {str(e)}")
            return None
