# Backend API Tests
=================

**FastAPI + WebSocket + Bitget Integration Tests**

## 🎯 **Test-Ziele**

- REST API Endpoints validieren
- WebSocket Core Functionality testen
- Bitget API Integration verifizieren
- OHLC Data Flow Ende-zu-Ende testen
- Latenz & Performance messen
- Error Handling & Recovery prüfen

## 📋 **Test-Dateien**

### **health_endpoints.sh**
- Basic Health Check (/health, /ping)
- Service Availability Validation
- Response Time Measurements

### **trading_endpoints.sh**
- REST Trading API Tests
- JWT Authentication Tests
- CRUD Operations Validation
- Data Format Validation

### **websocket_core_tests.py**
- WebSocket Connection Management
- Message Broadcasting Tests
- Reconnection Logic Validation
- Multiple Client Handling

### **bitget_api_tests.sh**
- Bitget WebSocket Integration
- Market Data Streaming Tests
- Rate Limit Handling
- Error Recovery Tests

### **ohlc_data_tests.sh**
- OHLC/Candle Data Validation
- Data Format Consistency
- Historical Data Retrieval
- Real-time Data Updates

### **ohlc_bitget_flow_tests.sh**
- Ende-zu-Ende: Bitget → Backend → Database → Frontend
- Complete Data Pipeline Tests
- Data Integrity Validation
- Performance Monitoring

### **latency_tests.py**
- WebSocket Latency Measurements
- Sub-100ms Performance Tests
- Network Optimization Validation
- Performance Regression Tests

### **error_handling_tests.py**
- Error Scenarios & Recovery
- Exception Handling Tests
- Graceful Degradation Tests
- Failover Mechanism Tests

### **concurrent_connections_test.py**
- Multiple WebSocket Clients
- Load Testing (50+ connections)
- Resource Usage Monitoring
- Scalability Validation

## 🚀 **Ausführung**

```bash
# Alle Backend API Tests
cd test/02_backend_api
./run_all_backend_tests.sh

# Kritische WebSocket Tests
python websocket_core_tests.py
python latency_tests.py
python concurrent_connections_test.py

# Bitget Integration
./bitget_api_tests.sh
./ohlc_bitget_flow_tests.sh
```

## ✅ **Erfolgskriterien**

- **Latenz:** WebSocket <100ms Response Time
- **Stabilität:** 99.9% Uptime bei 50+ Clients
- **Datenintegrität:** Zero Data Loss bei Reconnects
- **Performance:** 1000+ Messages/Second
- **Bitget Integration:** Live Data Stream funktional

## 📊 **Kritische Metriken**

| Test-Kategorie | Threshold | Messbereich |
|----------------|-----------|-------------|
| WebSocket Latenz | <100ms | 50-200ms |
| REST API Response | <500ms | 100-1000ms |
| Concurrent Clients | 50+ | 1-100 |
| Message Throughput | 1000/s | 100-5000/s |
| Error Recovery | <5s | 1-30s |

## 🔥 **WebSocket Test-Szenarien**

### **Connection Management**
- Verbindungsaufbau unter Last
- Graceful Disconnect Handling
- Automatic Reconnection Logic
- Connection Pool Management

### **Data Integrity**
- Message Order Preservation
- No Message Loss Validation
- Duplicate Message Detection
- Corrupt Data Handling

### **Performance**
- High-Frequency Updates
- Burst Message Handling
- Memory Leak Detection
- CPU Usage Optimization

### **Error Scenarios**
- Network Interruption Recovery
- Invalid Message Handling
- Rate Limit Response
- Server Overload Behavior
