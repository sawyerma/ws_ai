# 🚀 Data Pipeline Performance Tests

Vollständige Performance-Testsuite für die **Bitget → Backend → Redis → Frontend** Pipeline.

## 🎯 **Ziel: <20ms End-to-End Latenz**

```
Bitget API → Backend → Redis → Frontend → UI Display
    45ms    +  <1ms  +  <1ms  +    5ms   = **<52ms Total**
```

## 📁 **Test-Struktur**

```
test/05_bitget_system/
├── test_full_pipeline_performance.py    # Haupttest (Redis + Backend)
├── frontend_performance_tester.py       # Browser Performance Test
├── README_PERFORMANCE.md               # Diese Datei
└── simple_bitget_test.py               # Einfacher API Test
```

## 🏃‍♂️ **Tests Ausführen**

### **Option 1: Test-Runner (Empfohlen)**
```bash
cd /Users/sawyer_ma/Desktop/Firma/2_DarkMa/0_WS_AI
python3 test/run_tests.py

# Wähle Option "p" für Performance Tests
```

### **Option 2: Einzelne Tests**
```bash
# Pipeline Performance Test (Redis + Backend)
python3 test/05_bitget_system/test_full_pipeline_performance.py

# Frontend Performance Test (Browser + DOM)
pip install selenium  # Falls nicht installiert
python3 test/05_bitget_system/frontend_performance_tester.py
```

### **Option 3: Pytest**
```bash
pytest test/05_bitget_system/test_full_pipeline_performance.py -v
```

## ⚡ **Was wird gemessen?**

### **1. Redis Cache Performance**
- **Ping Latenz:** <0.5ms 
- **Write Speed:** 50,000+ ops/sec
- **Read Speed:** 100,000+ ops/sec
- **Memory Usage:** <100MB optimal

### **2. Backend API Performance**  
- **/ticker Endpoint:** Latenz + Cache Hit Rate
- **/symbols Endpoint:** Bulk Data Performance
- **Concurrent Load:** 50+ simultane Requests

### **3. End-to-End Pipeline**
- **Cold Cache:** Bitget API → Redis → Frontend
- **Warm Cache:** Redis Hit → Frontend (Sub-ms)
- **Total Latenz:** Target <20ms

### **4. Frontend Performance**
- **Page Load Speed:** <2 Sekunden
- **DOM Updates:** <10ms pro Update
- **Table Rendering:** 100+ Zeilen/Sekunde
- **Memory Usage:** Browser Heap Size
- **API Call Speed:** Frontend → Backend

## 📊 **Erwartete Resultate**

### **🚀 EXCELLENT Performance:**
```
⚡ REDIS PERFORMANCE:
  Ping Latency:     0.15ms 
  Write Speed:      52,000 ops/sec (0.45ms avg)
  Read Speed:       98,000 ops/sec (0.18ms avg)
  Memory Usage:     15.2MB

🎯 CACHE PERFORMANCE:
  Cache Hit:        95,000 ops/sec (0.021ms avg)
  Cache Miss:       89,000 ops/sec (0.023ms avg)

🔌 BACKEND API PERFORMANCE:
  /ticker endpoint: 48ms avg
  /symbols endpoint: 125ms avg

🔀 CONCURRENT LOAD (50 requests):
  Success Rate:     100.0% (50/50)
  95th Percentile:  67ms

🎯 END-TO-END PIPELINE:
  Average:          18ms ✅ ACHIEVED
  Best Case:        12ms
  Total Pipeline:   ~18ms

Overall Rating: 🚀 EXCELLENT (Sub-20ms)
```

### **🖥️ Frontend Performance:**
```
📄 PAGE LOAD PERFORMANCE:
  Average Load Time: 890ms
  Fastest Load:      654ms

⚡ DOM UPDATE PERFORMANCE:
  Average Update:    0.85ms
  Updates/sec:       1176 ops/sec

📊 TABLE RENDERING:
   10 rows:          8ms (1250 rows/sec)
   50 rows:         18ms (2778 rows/sec) 
  100 rows:         31ms (3226 rows/sec)

🧠 BROWSER MEMORY:
  Used Memory:       12.5MB
  Total Memory:      25.8MB

Overall Rating: 🚀 EXCELLENT (95/100)
```

## 🛠️ **Voraussetzungen**

### **Docker Services (Automatisch gestartet)**
- ClickHouse: `localhost:8124`
- Redis: `localhost:6380`
- Backend: `localhost:8100`
- Frontend: `localhost:8180`

### **Python Dependencies**
```bash
# Basis (bereits in requirements.txt)
pytest==8.2.2
aiohttp
redis
statistics

# Für Frontend Tests (optional)
selenium==4.15.0
```

### **Browser (für Frontend Tests)**
- **Chrome/Chromium** installiert
- **ChromeDriver** verfügbar
```bash
# macOS
brew install chromedriver

# Linux
apt-get install chromium-chromedriver

# Windows
Downloade ChromeDriver von Google
```

## 🚨 **Troubleshooting**

### **Redis Connection Failed**
```bash
# Prüfe Redis Status
docker ps | grep redis
docker logs redis-bolt

# Neustart
docker-compose restart redis-bolt
```

### **Backend API Errors**
```bash
# Prüfe Backend Status  
curl http://localhost:8100/health
docker logs backend-bolt
```

### **Frontend Tests Fehlschlagen**
```bash
# ChromeDriver installieren
brew install chromedriver  # macOS

# Selenium installieren
pip install selenium

# Headless Chrome testen
google-chrome --version
```

### **Performance Ziele nicht erreicht**

**Wenn E2E > 20ms:**
1. **Redis optimieren:** Memory-Konfiguration prüfen
2. **Backend caching:** Implementierung überprüfen  
3. **Netzwerk:** Loopback vs. Docker-Netzwerk
4. **System Load:** CPU/Memory verfügbar?

**Wenn Frontend > 2s Load:**
1. **Bundle Size:** Frontend-Assets optimieren
2. **API Calls:** Parallel loading implementieren
3. **Browser Cache:** Service Worker nutzen

## 🎯 **Performance Benchmarks**

| Komponente | Target | Good | Excellent |
|------------|--------|------|-----------|
| Redis Read | <1ms | <0.5ms | <0.2ms |
| Redis Write | <2ms | <1ms | <0.5ms |
| Backend API | <100ms | <50ms | <30ms |
| Frontend Load | <3s | <2s | <1s |
| DOM Update | <10ms | <5ms | <1ms |
| End-to-End | <50ms | <30ms | <20ms |

## 📈 **Monitoring**

Performance-Tests loggen automatisch:
- **Latenz-Histogramme** (P50, P95, P99)
- **Throughput-Metriken** (ops/sec)
- **Error Rates** (Cache Miss, API Errors)
- **Resource Usage** (Memory, CPU)

Logs werden in Console ausgegeben und können in Monitoring-Systeme integriert werden.

---

**💡 Tipp:** Führe Tests mehrmals aus für konsistente Ergebnisse. Erste Ausführung kann durch Code-Loading langsamer sein.
