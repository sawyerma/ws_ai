#!/bin/bash

# Trading System - Vollautomatisierter Neustart
# Stoppt alle Services und startet sie dann neu

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🔄 TRADING SYSTEM 🔄                     ║"
echo "║                   Vollautomatisierter Neustart               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}🔄 RESTART SEQUENCE INITIIERT${NC}\n"

# Schritt 1: Alles stoppen
echo -e "${RED}🛑 Schritt 1: Alle Services stoppen...${NC}"
./stop-all.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Fehler beim Stoppen der Services${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Alle Services gestoppt\n${NC}"

# Kurze Pause für sauberes Shutdown
echo -e "${YELLOW}⏱️  Warte 5 Sekunden für sauberes Shutdown...${NC}"
sleep 5

# Schritt 2: Alles starten
echo -e "${GREEN}🚀 Schritt 2: Alle Services starten...${NC}"
./start-all.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Fehler beim Starten der Services${NC}"
    exit 1
fi

echo -e "\n${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  🎉 RESTART ERFOLGREICH! 🎉                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}✅ System erfolgreich neugestartet!${NC}"
echo -e "\n${BLUE}📋 Nützliche Befehle:${NC}"
echo -e "  ${CYAN}./status.sh${NC}       - Aktueller System-Status"
echo -e "  ${CYAN}./stop-all.sh${NC}     - System stoppen"

echo ""
