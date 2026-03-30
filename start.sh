#!/bin/bash

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}   Pi Monitor - Start${NC}"
echo ""

# Docker Check
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker nicht installiert!${NC}"
    echo "  curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Starte Container
echo -e "${YELLOW}Starte Services...${NC}"
docker compose up -d --build

# Status
echo ""
docker compose ps

# IP Adresse
IP=$(hostname -I | awk '{print $1}')
echo ""
echo -e "${GREEN}Erreichbar unter: http://${IP}${NC}"
echo ""
