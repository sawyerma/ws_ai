#!/bin/bash

# Trading System - Status Check
# Zeigt den aktuellen Status aller Services

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    📊 TRADING SYSTEM 📊                     ║"
echo "║                       System Status                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Globale Variablen
PIDS_DIR="./pids"

# Funktion: Service-Status prüfen
check_service_status() {
    local name=$1
    local port=$2
    local pid_file="$PIDS_DIR/$name.pid"
    
    # Status-Variablen
    local pid_status="❌"
    local port_status="❌" 
    local http_status="❌"
    local pid_info=""
    
    # PID-Check
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            pid_status="✅"
            pid_info="PID: $pid"
        else
            pid_info="PID: $pid (dead)"
        fi
    else
        pid_info="No PID file"
    fi
    
    # Port-Check
    if lsof -ti:$port >/dev/null 2>&1; then
        port_status="✅"
    fi
    
    # HTTP-Check
    if curl -s "http://localhost:$port" >/dev/null 2>&1 || \
       curl -s "http://localhost:$port/health" >/dev/null 2>&1 || \
       curl -s "http://localhost:$port/ping" >/dev/null 2>&1; then
        http_status="✅"
    fi
    
    # Status ausgeben
    printf "%-15s | %-8s | %-8s | %-8s | %s\n" \
        "$name" "$pid_status" "$port_status" "$http_status" "$pid_info"
}

# Funktion: Docker Container Status
check_docker_status() {
    local container=$1
    local port=$2
    
    local status="❌"
    local health="❌"
    local info=""
    
    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        status="✅"
        
        # Health-Check falls verfügbar
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
        if [ "$health_status" = "healthy" ]; then
            health="✅"
        elif [ "$health_status" = "none" ]; then
            health="N/A"
        fi
        
        info="Running"
    else
        if docker ps -a --filter "name=$container" | grep -q "$container"; then
            info="Stopped"
        else
            info="Not found"
        fi
    fi
    
    printf "%-15s | %-8s | %-8s | %-8s | %s\n" \
        "$container" "$status" "$health" "N/A" "$info"
}

# System-Übersicht
echo -e "${CYAN}🔍 SYSTEM OVERVIEW${NC}"
echo -e "$(date '+%Y-%m-%d %H:%M:%S')\n"

# Header für Service-Tabelle
echo -e "${YELLOW}📋 SERVICE STATUS:${NC}"
printf "%-15s | %-8s | %-8s | %-8s | %s\n" \
    "Service" "Process" "Port" "HTTP" "Info"
echo "----------------|----------|----------|----------|--------------------"

# Services prüfen
check_service_status "Backend" 8000
check_service_status "Frontend" 8080
check_service_status "Desktop" 8090

echo ""

# Header für Docker-Tabelle
echo -e "${YELLOW}🐳 DOCKER STATUS:${NC}"
printf "%-15s | %-8s | %-8s | %-8s | %s\n" \
    "Container" "Running" "Health" "N/A" "Info"
echo "----------------|----------|----------|----------|--------------------"

# Docker Container prüfen
check_docker_status "clickhouse-bolt" 8124
check_docker_status "redis-bolt" 6380

echo ""

# Port-Übersicht
echo -e "${YELLOW}🔌 PORT OVERVIEW:${NC}"
ports=(8000 8080 8090 8124 6380)
for port in "${ports[@]}"; do
    pid=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ -n "$pid" ]; then
        process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo -e "  Port $port: ${GREEN}✅ IN USE${NC} (PID: $pid, Process: $process_name)"
    else
        echo -e "  Port $port: ${RED}❌ FREE${NC}"
    fi
done

echo ""

# Log-Dateien Status
echo -e "${YELLOW}📝 LOG FILES:${NC}"
if [ -d "logs" ]; then
    for log in backend.log frontend.log desktop.log; do
        if [ -f "logs/$log" ]; then
            size=$(du -h "logs/$log" | cut -f1)
            lines=$(wc -l < "logs/$log")
            echo -e "  $log: ${GREEN}✅ EXISTS${NC} ($size, $lines lines)"
        else
            echo -e "  $log: ${RED}❌ MISSING${NC}"
        fi
    done
else
    echo -e "  ${RED}❌ Logs directory not found${NC}"
fi

echo ""

# System Resources
echo -e "${YELLOW}💻 SYSTEM RESOURCES:${NC}"

# Memory Usage
memory_info=$(free -h 2>/dev/null || vm_stat 2>/dev/null | head -5 || echo "Memory info not available")
if command -v free >/dev/null 2>&1; then
    echo -e "  Memory: $(free -h | awk 'NR==2{printf "Used: %s/%s (%.1f%%)", $3, $2, $3*100/$2}')"
elif command -v vm_stat >/dev/null 2>&1; then
    echo -e "  Memory: macOS system"
fi

# CPU Load
if command -v uptime >/dev/null 2>&1; then
    load_avg=$(uptime | awk -F'load average:' '{print $2}')
    echo -e "  Load Average:$load_avg"
fi

# Disk Space
if [ -d "." ]; then
    disk_usage=$(df -h . | awk 'NR==2 {print $3"/"$2" ("$5" used)"}')
    echo -e "  Disk Usage: $disk_usage"
fi

echo ""

# Zusammenfassung
echo -e "${CYAN}📊 SUMMARY:${NC}"

# Zähle laufende Services
running_services=0
total_services=3

# Backend
if curl -s "http://localhost:8000" >/dev/null 2>&1 || curl -s "http://localhost:8000/health" >/dev/null 2>&1; then
    ((running_services++))
fi

# Frontend  
if curl -s "http://localhost:8080" >/dev/null 2>&1; then
    ((running_services++))
fi

# ClickHouse
if docker ps --filter "name=clickhouse-bolt" --filter "status=running" | grep -q "clickhouse-bolt"; then
    ((running_services++))
fi

# Status-Bewertung
if [ $running_services -eq $total_services ]; then
    echo -e "  System Status: ${GREEN}✅ FULLY OPERATIONAL${NC} ($running_services/$total_services services)"
elif [ $running_services -gt 0 ]; then
    echo -e "  System Status: ${YELLOW}⚠️ PARTIALLY RUNNING${NC} ($running_services/$total_services services)"
else
    echo -e "  System Status: ${RED}❌ ALL SERVICES DOWN${NC} ($running_services/$total_services services)"
fi

# URLs falls System läuft
if [ $running_services -gt 0 ]; then
    echo ""
    echo -e "${GREEN}🌐 Available URLs:${NC}"
    if curl -s "http://localhost:8080" >/dev/null 2>&1; then
        echo -e "  Frontend:  ${CYAN}http://localhost:8080${NC}"
    fi
    if curl -s "http://localhost:8000" >/dev/null 2>&1; then
        echo -e "  Backend:   ${CYAN}http://localhost:8000${NC}"
    fi
    if docker ps --filter "name=clickhouse-bolt" --filter "status=running" | grep -q "clickhouse-bolt"; then
        echo -e "  ClickHouse: ${CYAN}http://localhost:8124${NC}"
    fi
fi

# Management-Befehle
echo ""
echo -e "${BLUE}📋 Management Commands:${NC}"
echo -e "  ${CYAN}./start-all.sh${NC}    - Start all services"
echo -e "  ${CYAN}./stop-all.sh${NC}     - Stop all services"
echo -e "  ${CYAN}./restart.sh${NC}      - Restart system"
echo -e "  ${CYAN}./status.sh${NC}       - Show this status"

echo ""
