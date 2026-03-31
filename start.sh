#!/bin/bash

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}   Pi Monitor - Start (Traefik)${NC}"
echo ""

# Docker Check
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker nicht installiert!${NC}"
    exit 1
fi

# Prüfe ob traefik-network existiert
if ! docker network ls | grep -q traefik-network; then
    echo -e "${YELLOW}Erstelle traefik-network...${NC}"
    docker network create traefik-network
fi

# Starte Container
echo -e "${YELLOW}Baue und starte Pi Monitor...${NC}"
docker compose up -d --build

# Status
echo ""
docker compose ps
echo ""
echo -e "${GREEN}Pi Monitor läuft via Traefik${NC}"
echo ""
