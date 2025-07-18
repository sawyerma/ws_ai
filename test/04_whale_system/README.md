# Whale System Tests

Comprehensive test suite for the Whale Monitoring System.

## Test Structure

### 1. Infrastructure Tests
- ClickHouse connection and table validation
- Schema verification
- Performance baseline tests

### 2. API Tests
- Blockchain API connections (Etherscan, BSCScan, Polygon)
- Price API connections (CoinGecko)
- Rate limiting and error handling

### 3. Database Tests
- Data insertion and retrieval
- Duplicate detection
- Query performance

### 4. Service Tests
- Price Service functionality
- Collector Manager operations
- Individual collector tests

### 5. Integration Tests
- End-to-end whale detection
- Cross-border analysis
- Geographic mapping

### 6. Frontend Data Tests
- Data availability for frontend
- API response formatting
- Query optimization

## Running Tests

```bash
# Run all whale system tests
python -m pytest test/04_whale_system/

# Run specific test categories
python -m pytest test/04_whale_system/test_infrastructure_whales.py
python -m pytest test/04_whale_system/test_api_connections_whales.py
python -m pytest test/04_whale_system/test_database_whales.py
python -m pytest test/04_whale_system/test_services_whales.py
python -m pytest test/04_whale_system/test_integration_whales.py
python -m pytest test/04_whale_system/test_frontend_data_whales.py
python -m pytest test/04_whale_system/test_recovery_whales.py
python -m pytest test/04_whale_system/test_negative_whales.py
```

## Test Requirements

- Docker containers running (ClickHouse, Backend)
- Valid API keys in .env file
- Network connectivity for external APIs
- Test data for validation

## Expected Results

All tests should pass to ensure:
- System reliability
- Data integrity
- Performance standards
- Frontend compatibility
