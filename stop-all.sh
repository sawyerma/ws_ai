#!/bin/bash

# Trading System - Vollautomatisiertes Stoppen
# Stoppt alle Services sauber in umgekehrter Reihenfolge

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${RED}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🛑 TRADING SYSTEM 🛑                     ║"
echo "║                  Vollautomatisiertes Stoppen                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# PID Files Verzeichnis
PIDS_DIR="./pids"

# Funktion: Process sauber beenden
kill_process() {
    local name=$1
    local pid_file="$PIDS_DIR/$name.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}🔄 Stoppe $name (PID: $pid)...${NC}"
            
            # Erst SIGTERM versuchen
            kill "$pid" 2>/dev/null
            
            # Warten bis zu 10 Sekunden
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    echo -e "${GREEN}✅ $name erfolgreich gestoppt${NC}"
                    rm -f "$pid_file"
                    return 0
                fi
                sleep 1
            done
            
            # Falls nicht reagiert, SIGKILL verwenden
            echo -e "${YELLOW}⚡ Force-Kill $name...${NC}"
            kill -9 "$pid" 2>/dev/null || true
            rm -f "$pid_file"
            echo -e "${GREEN}✅ $name force-gestoppt${NC}"
        else
            echo -e "${BLUE}ℹ️  $name war bereits gestoppt${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${BLUE}ℹ️  Keine PID-Datei für $name gefunden${NC}"
    fi
}

# Funktion: Alle Prozesse mit Namen beenden
kill_by_name() {
    local name=$1
    local pattern=$2
    
    echo -e "${YELLOW}🔍 Suche nach $name Prozessen...${NC}"
    
    # Finde alle passenden Prozesse
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}🔄 Stoppe $name Prozesse: $pids${NC}"
        for pid in $pids; do
            kill "$pid" 2>/dev/null || true
        done
        
        # Warten
        sleep 3
        
        # Force-Kill falls nötig
        remaining_pids=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo -e "${YELLOW}⚡ Force-Kill $name: $remaining_pids${NC}"
            for pid in $remaining_pids; do
                kill -9 "$pid" 2>/dev/null || true
            done
        fi
        
        echo -e "${GREEN}✅ $name Prozesse gestoppt${NC}"
    else
        echo -e "${BLUE}ℹ️  Keine $name Prozesse gefunden${NC}"
    fi
}

echo -e "${PURPLE}🛑 STOP SEQUENCE INITIIERT${NC}\n"

# ==================== SCHRITT 1: DESKTOP GUI ====================
echo -e "${BLUE}🖥️  Schritt 1: Desktop GUI stoppen${NC}"
kill_process "desktop"
kill_by_name "Desktop GUI" "desktop_gui.*main.py"

# ==================== SCHRITT 2: FRONTEND ====================
echo -e "${BLUE}🎨 Schritt 2: Frontend stoppen${NC}"
kill_process "frontend"
kill_by_name "Frontend" "npm.*run.*dev"
kill_by_name "Vite Dev Server" "vite.*--host"

# ==================== SCHRITT 3: BACKEND ====================
echo -e "${BLUE}🔧 Schritt 3: Backend stoppen${NC}"
kill_process "backend"
kill_by_name "Backend" "uvicorn.*core.main:app"

# ==================== SCHRITT 4: DOCKER SERVICES ====================
echo -e "${BLUE}🐳 Schritt 4: Docker Services stoppen${NC}"

echo -e "${YELLOW}🛑 Stoppe Docker Container...${NC}"
docker-compose down 2>/dev/null || {
    echo -e "${YELLOW}⚠️  docker-compose down fehlgeschlagen, versuche direkte Container-Stopps${NC}"
    
    # Direkte Container-Stopps als Fallback
    containers=("clickhouse-bolt" "redis-bolt" "backend-bolt" "frontend-bolt")
    for container in "${containers[@]}"; do
        if docker ps -q --filter "name=$container" | grep -q .; then
            echo -e "${YELLOW}🔄 Stoppe Container $container...${NC}"
            docker stop "$container" 2>/dev/null || true
            docker rm "$container" 2>/dev/null || true
        fi
    done
}

# ==================== CLEANUP ====================
echo -e "${BLUE}🧹 Schritt 5: Cleanup${NC}"

# PID Files löschen
echo -e "${YELLOW}📁 Lösche PID-Dateien...${NC}"
rm -rf "$PIDS_DIR" 2>/dev/null || true

# Port-Cleanup (macOS/Linux)
echo -e "${YELLOW}🔌 Port-Cleanup...${NC}"
ports=(8000 8080 8090 8124 6380)
for port in "${ports[@]}"; do
    pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}🔄 Beende Prozess auf Port $port (PID: $pid)${NC}"
        kill -9 "$pid" 2>/dev/null || true
    fi
done

# Logs rotieren (optional)
if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
    echo -e "${YELLOW}📝 Rotiere Log-Dateien...${NC}"
    timestamp=$(date +"%Y%m%d_%H%M%S")
    mkdir -p "logs/archive"
    mv logs/*.log "logs/archive/" 2>/dev/null || true
fi

# ==================== FINAL STATUS ====================
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   ✅ SYSTEM GESTOPPT! ✅                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}🛑 Alle Services wurden erfolgreich gestoppt:${NC}"
echo -e "  ${YELLOW}✅ Desktop GUI${NC}     - Gestoppt"
echo -e "  ${YELLOW}✅ Frontend${NC}        - Gestoppt" 
echo -e "  ${YELLOW}✅ Backend${NC}         - Gestoppt"
echo -e "  ${YELLOW}✅ ClickHouse${NC}      - Gestoppt"
echo -e "  ${YELLOW}✅ Redis${NC}           - Gestoppt"

echo -e "\n${BLUE}📋 Verfügbare Befehle:${NC}"
echo -e "  ${CYAN}./start-all.sh${NC}     - System wieder starten"
echo -e "  ${CYAN}./status.sh${NC}        - Status prüfen"

echo -e "\n${PURPLE}🛑 System sauber heruntergefahren!${NC}"
echo ""
