#!/bin/bash

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Pi Monitor - Start Script${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Prüfe ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Fehler: Docker ist nicht installiert!${NC}"
    echo ""
    echo "Bitte installiere Docker mit:"
    echo "  curl -fsSL https://get.docker.com | sh"
    echo "  sudo usermod -aG docker \$USER"
    echo ""
    exit 1
fi

# Prüfe ob Docker Compose Plugin vorhanden ist
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Fehler: Docker Compose Plugin ist nicht installiert!${NC}"
    echo ""
    echo "Bitte installiere es mit:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install docker-compose-plugin"
    echo ""
    exit 1
fi

# Baue und starte die Container
echo ""
echo -e "${YELLOW}Baue Docker Images (kann beim ersten Mal 5-10 Minuten dauern)...${NC}"
echo ""

docker compose build --no-cache

echo ""
echo -e "${YELLOW}Starte alle Services...${NC}"
docker compose up -d

# Warte auf Start
echo ""
echo -e "${YELLOW}Warte auf Service-Start...${NC}"
sleep 10

# Prüfe Status
echo ""
echo "Service Status:"
echo "==============="
docker compose ps

# Hole IP-Adresse
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Setup abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Die App ist erreichbar unter:"
echo -e "  ${GREEN}http://${IP_ADDRESS}${NC}"
echo -e "  ${GREEN}http://localhost${NC}"
echo ""
echo "Nuetzliche Befehle:"
echo "  ./stop.sh           - Stoppe alle Services"
echo "  ./logs.sh           - Zeige Logs"
echo "  docker compose ps   - Status anzeigen"
echo ""
