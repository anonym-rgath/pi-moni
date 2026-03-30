#!/bin/bash

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Pi Monitor - Logs${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${YELLOW}Zeige Logs (Ctrl+C zum Beenden)...${NC}"
echo ""

docker compose logs -f
