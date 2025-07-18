#!/bin/bash

# Trading System - Vollautomatisierter Start
# Startet alle Services in der richtigen Reihenfolge für die Entwicklung

set -e  # Bei Fehlern stoppen

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    TRADING SYSTEM                            ║"
echo "║                  Vollautomatisierter Start                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Globale Variablen
CLICKHOUSE_CONTAINER="clickhouse-bolt"
BACKEND_PORT=8000
FRONTEND_PORT=8080
DESKTOP_PORT=8090

# PID Files für Process-Tracking
PIDS_DIR="./pids"
mkdir -p "$PIDS_DIR"

# Cleanup-Funktion für Fehler
cleanup_on_error() {
    echo -e "\n${RED}FEHLER beim Starten! Cleanup wird ausgeführt...${NC}"
    ./stop-all.sh 2>/dev/null || true
    exit 1
}

# Error Handler registrieren
trap cleanup_on_error ERR

# Funktion: Service-Status prüfen
check_service() {
    local name=$1
    local port=$2
    local max_attempts=${3:-30}
    
    echo -e "${YELLOW}Warte auf $name (Port $port)...${NC}"
    
    for i in $(seq 1 $max_attempts); do
        if curl -s "http://localhost:$port" >/dev/null 2>&1 || \
           curl -s "http://localhost:$port/health" >/dev/null 2>&1 || \
           curl -s "http://localhost:$port/ping" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $name ist bereit!${NC}"
            return 0
        fi
        
        if [ $i -eq $max_attempts ]; then
            echo -e "${RED}❌ $name antwortet nicht nach $max_attempts Versuchen${NC}"
            return 1
        fi
        
        printf "."
        sleep 1
    done
}

# Funktion: Docker Container prüfen
check_docker_container() {
    local container_name=$1
    local max_attempts=${2:-60}
    
    echo -e "${YELLOW}Warte auf Docker Container $container_name...${NC}"
    
    for i in $(seq 1 $max_attempts); do
        if docker ps --filter "name=$container_name" --filter "status=running" | grep -q "$container_name"; then
            # Zusätzlicher Health-Check
            if docker exec "$container_name" true 2>/dev/null; then
                echo -e "${GREEN}✅ Container $container_name ist bereit!${NC}"
                return 0
            fi
        fi
        
        if [ $i -eq $max_attempts ]; then
            echo -e "${RED}❌ Container $container_name nicht bereit nach $max_attempts Versuchen${NC}"
            return 1
        fi
        
        printf "."
        sleep 1
    done
}

# Funktion: Requirements installieren
install_requirements_func() {
    local dir=$1
    local venv_path="$dir/.venv"
    
    cd "$dir"
    
    # Virtual Environment erstellen falls nicht vorhanden
    if [ ! -d "$venv_path" ]; then
        echo -e "${YELLOW}Erstelle Virtual Environment...${NC}"
        python3 -m venv .venv
    fi
    
    # Virtual Environment aktivieren
    source .venv/bin/activate
    
    # Je nach Auswahl handeln
    case "$install_requirements" in
        "y")
            echo -e "${BLUE}📦 Installiere alle Requirements in $dir...${NC}"
            if [ -f "requirements.txt" ]; then
                echo -e "${YELLOW}📋 Installiere Python-Abhängigkeiten...${NC}"
                pip install --upgrade pip
                pip install -r requirements.txt || {
                    echo -e "${YELLOW}⚠️ Einige Packages konnten nicht installiert werden, aber fahre fort...${NC}"
                }
            fi
            ;;
        "s")
            echo -e "${BLUE}🔍 Überprüfe Requirements in $dir...${NC}"
            if [ -f "requirements.txt" ]; then
                pip install --upgrade pip
                pip install fastapi uvicorn python-dotenv aiohttp clickhouse-connect httpx websockets redis
            fi
            ;;
        "n"|*)
            echo -e "${YELLOW}⏭️ Überspringe Requirements Installation in $dir${NC}"
            if [ -f "requirements.txt" ]; then
                pip install --upgrade pip
                pip install fastapi uvicorn python-dotenv aiohttp clickhouse-connect httpx websockets redis
            fi
            ;;
    esac
    
    # Verifiziere kritische Module
    python -c "import fastapi, uvicorn, websockets, aiohttp, clickhouse_connect" && {
        echo -e "${GREEN}✅ Kritische Module sind verfügbar${NC}"
    } || {
        echo -e "${RED}❌ Kritische Module fehlen!${NC}"
        exit 1
    }
    
    cd - > /dev/null
}

echo -e "${PURPLE}🏁 START SEQUENCE INITIIERT${NC}\n"

# ==================== REQUIREMENTS ABFRAGE ====================
echo -e "${YELLOW}❓ Requirements installieren? (kann lange dauern)${NC}"
echo -e "${BLUE}[y] Ja, installieren${NC}"
echo -e "${BLUE}[n] Nein, überspringen${NC}"
echo -e "${BLUE}[s] Nur überprüfen${NC}"
read -p "Auswahl [n]: " install_requirements
install_requirements=${install_requirements:-n}

echo ""

# ==================== SCHRITT 1: DOCKER SERVICES ====================
echo -e "${BLUE}Schritt 1: Docker Services starten${NC}"

# Prüfe ob Docker läuft
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker ist nicht verfügbar. Bitte Docker starten.${NC}"
    exit 1
fi

# Alte Container stoppen (falls laufend)
echo -e "${YELLOW}Cleanup alter Container...${NC}"
docker-compose down 2>/dev/null || true

# ClickHouse & Redis starten
echo -e "${YELLOW}🚀 Starte ClickHouse & Redis...${NC}"
docker-compose up -d clickhouse-bolt redis-bolt

# Warten bis Container bereit sind
check_docker_container "$CLICKHOUSE_CONTAINER" 60

# ClickHouse Health-Check
echo -e "${YELLOW}🔍 ClickHouse Health-Check...${NC}"
for i in {1..30}; do
    if curl -s "http://localhost:8124/ping" | grep -q "Ok"; then
        echo -e "${GREEN}✅ ClickHouse ist gesund!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ ClickHouse Health-Check fehlgeschlagen${NC}"
        exit 1
    fi
    sleep 2
done

echo -e "${GREEN}✅ Docker Services bereit!\n${NC}"

# ==================== SCHRITT 2: BACKEND ====================
echo -e "${BLUE}🔧 Schritt 2: Backend starten${NC}"

# Requirements installieren
install_requirements_func "backend"

# Backend im Hintergrund starten
echo -e "${YELLOW}🚀 Starte Backend Server (Port $BACKEND_PORT)...${NC}"

# Port-Check
if lsof -ti:$BACKEND_PORT >/dev/null 2>&1; then
    echo -e "${RED}❌ Port $BACKEND_PORT bereits belegt! Stoppe alte Prozesse...${NC}"
    lsof -ti:$BACKEND_PORT | xargs kill -9
    sleep 2
fi

# Logs-Verzeichnis sicherstellen
mkdir -p logs

cd backend
source .venv/bin/activate

# Backend starten mit sichtbaren Logs (für Debugging)
echo -e "${BLUE}📋 Starte uvicorn mit Live-Logs...${NC}"
python -m uvicorn core.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "../$PIDS_DIR/backend.pid"

# Zeige ALLE Logs live
sleep 3
echo -e "${YELLOW}Backend Log (ALLE Zeilen):${NC}"
echo "----------------------------------------"
cat ../logs/backend.log || echo "Noch keine Logs..."
echo "----------------------------------------"

# Backend Health-Check mit Live-Logs
echo -e "${YELLOW}Backend Health-Check mit Live-Logs...${NC}"
cd - > /dev/null

# Starte tail -f in background und zeige Health-Check
tail -f logs/backend.log &
TAIL_PID=$!

# Health-Check mit Live-Output
for i in $(seq 1 45); do
    if curl -s "http://localhost:$BACKEND_PORT" >/dev/null 2>&1 || \
       curl -s "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
        kill $TAIL_PID 2>/dev/null
        echo -e "\n${GREEN}✅ Backend ist bereit!${NC}"
        break
    fi
    
    if [ $i -eq 45 ]; then
        kill $TAIL_PID 2>/dev/null
        echo -e "\n${RED}❌ Backend antwortet nicht nach 45 Versuchen${NC}"
        exit 1
    fi
    
    sleep 1
done

echo -e "${GREEN}✅ Backend läuft!\n${NC}"

# ==================== SCHRITT 3: FRONTEND ====================
echo -e "${BLUE}Schritt 3: Frontend starten${NC}"

cd frontend

# Node Modules installieren falls nicht vorhanden
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installiere Node Dependencies...${NC}"
    npm install
fi

# Frontend im Hintergrund starten
echo -e "${YELLOW}🚀 Starte Frontend Dev Server (Port $FRONTEND_PORT)...${NC}"
mkdir -p ../logs
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "../$PIDS_DIR/frontend.pid"
cd - > /dev/null

# Frontend Health-Check
check_service "Frontend" $FRONTEND_PORT 45

echo -e "${GREEN}✅ Frontend läuft!\n${NC}"

# ==================== SCHRITT 4: DESKTOP GUI ====================
echo -e "${BLUE}🖥️  Schritt 4: Desktop GUI starten${NC}"

# Desktop GUI Requirements installieren
install_requirements_func "desktop_gui"

# Desktop GUI im Hintergrund starten
echo -e "${YELLOW}🚀 Starte Desktop GUI...${NC}"
cd desktop_gui
source .venv/bin/activate
nohup python main.py > ../logs/desktop.log 2>&1 &
DESKTOP_PID=$!
echo $DESKTOP_PID > "../$PIDS_DIR/desktop.pid"
cd - > /dev/null

echo -e "${GREEN}✅ Desktop GUI gestartet!\n${NC}"

# ==================== FINAL STATUS ====================
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 SYSTEM BEREIT! 🎉                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}🌐 Verfügbare Services:${NC}"
echo -e "  ${YELLOW}Frontend:${NC}      http://localhost:$FRONTEND_PORT"
echo -e "  ${YELLOW}Backend API:${NC}   http://localhost:$BACKEND_PORT"
echo -e "  ${YELLOW}ClickHouse:${NC}    http://localhost:8124"
echo -e "  ${YELLOW}Redis:${NC}         localhost:6380"
echo -e "  ${YELLOW}Desktop GUI:${NC}  Läuft im System Tray"

echo -e "\n${BLUE}Verfügbare Befehle:${NC}"
echo -e "  ${CYAN}./stop-all.sh${NC}     - Alle Services stoppen"
echo -e "  ${CYAN}./status.sh${NC}       - Status aller Services"
echo -e "  ${CYAN}./restart.sh${NC}      - System neu starten"

echo -e "\n${PURPLE}🚀 System erfolgreich gestartet! Viel Spaß beim Entwickeln!${NC}"

# Log-Dateien anzeigen
echo -e "\n${YELLOW}📝 Log-Dateien:${NC}"
echo -e "  Backend:  tail -f logs/backend.log"
echo -e "  Frontend: tail -f logs/frontend.log" 
echo -e "  Desktop:  tail -f logs/desktop.log"

echo ""
