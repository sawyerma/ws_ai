# QUICK START - Tests ausführen

## 1. Services starten (macht jetzt ALLES automatisch!)

```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
python3 test/start_services.py
```

**Das macht automatisch:**
- ✅ Virtual Environment erstellen/aktivieren
- ✅ Requirements installieren (selenium, requests, pytest)
- ✅ ClickHouse starten (localhost:8124)
- ✅ Redis starten (localhost:6380) 
- ✅ Backend starten (localhost:8100)
- ✅ Frontend starten (localhost:8180)

**🌐 Frontend GUI öffnen:**
```bash
open http://localhost:8180
```

---

## 2. Tests ausführen

### Test 1 - Bitget API Tests (funktioniert immer)
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
python3 test/05_bitget_system/simple_bitget_test.py
```

### Test 2 - Frontend Browser Performance Tests (mit Virtual Environment)
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
test_venv/bin/python test/05_bitget_system/frontend_performance_tester.py
```

### Test 3 - Pipeline Performance Tests (mit Virtual Environment)
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
test_venv/bin/python test/05_bitget_system/test_full_pipeline_performance.py
```

### Test 4 - ClickHouse Database Tests
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
python3 test/01_infrastructure/clickhouse_connection_test.py
```

### Test 5 - Docker System Tests
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
python3 test/01_infrastructure/docker_compose_test.py
```

## 🚨 KRITISCHE INFRASTRUCTURE TESTS (bei Performance-Problemen)

### Test 6 - Redis Connection & Performance Test
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
test_venv/bin/python test/05_bitget_system/test_redis_connection.py
```

### Test 7 - Backend Health & Latency Test
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
test_venv/bin/python test/05_bitget_system/test_backend_health.py
```

### Test 8 - Cache Service Function Test
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
test_venv/bin/python test/05_bitget_system/test_cache_service.py
```

### Test 9 - Direct API Performance Test
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
test_venv/bin/python test/05_bitget_system/test_direct_api_performance.py
```

---

## 3. Services stoppen

```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
docker-compose down
```

---

## Quick Commands (alles in einem Terminal)

```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI && python3 test/start_services.py && python3 test/05_bitget_system/simple_bitget_test.py
```

## Expected Results

**Test 1 (Bitget) - 5/5 Tests sollten ✅ PASS sein:**
- Basic Connection ✅ PASS  
- Spot Symbols ✅ PASS
- Spot Ticker ✅ PASS
- Orderbook ✅ PASS  
- Futures Symbols ✅ PASS

**Overall: 5/5 tests passed (100.0%)**
