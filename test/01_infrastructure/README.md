# Infrastructure Tests
====================

**Basis-Infrastructure Tests für DarkMa Trading System**

## 🎯 **Test-Ziele**

- Docker Services Verfügbarkeit prüfen
- ClickHouse Verbindung & Performance validieren  
- Datenbank-Migrationen testen
- Komplettes Environment Setup verifizieren

## 📋 **Test-Dateien**

### **docker_compose_test.py**
- Docker Services Health Check
- Container Startup Validation
- Network Connectivity Tests
- Resource Usage Monitoring

### **clickhouse_connection_test.py**
- ClickHouse Connection Tests
- Query Performance Benchmarks
- Data Insertion/Retrieval Tests
- Connection Pool Management

### **database_migration_test.py**
- Migration Scripts Validation
- Schema Evolution Tests
- Data Integrity Checks
- Rollback Functionality

### **environment_setup_test.sh**
- Complete Environment Bootstrap
- Dependencies Installation Check
- Configuration Validation
- Service Orchestration Test

## 🚀 **Ausführung**

```bash
# Alle Infrastructure Tests ausführen
cd test/01_infrastructure
./run_all_tests.sh

# Einzelne Tests
python docker_compose_test.py
python clickhouse_connection_test.py
python database_migration_test.py
./environment_setup_test.sh
```

## ✅ **Erfolgskriterien**

- Docker Services starten in <30 Sekunden
- ClickHouse Connection <100ms Response Time
- Migrations laufen fehlerfrei durch
- Environment Setup vollständig automatisiert

## 📊 **Test-Metriken**

| Test | Erwartete Dauer | Kritischer Threshold |
|------|----------------|---------------------|
| Docker Startup | <30s | 60s |
| ClickHouse Connect | <1s | 5s |
| Migration Run | <10s | 30s |
| Full Setup | <120s | 300s |
