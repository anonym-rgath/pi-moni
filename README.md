# Pi Monitor - Raspberry Pi & Docker Monitoring Dashboard

Eine leichtgewichtige Echtzeit-Monitoring-Lösung für Raspberry Pi und Docker Container mit Grafana-ähnlichem Dark-Design.

![Pi Monitor Dashboard](https://img.shields.io/badge/Version-1.0-green) ![Docker](https://img.shields.io/badge/Docker-Ready-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Features](#features)
3. [Architektur](#architektur)
4. [Voraussetzungen](#voraussetzungen)
5. [Installation](#installation)
6. [Konfiguration](#konfiguration)
7. [Traefik Integration](#traefik-integration)
8. [API Referenz](#api-referenz)
9. [Sicherheit](#sicherheit)
10. [Troubleshooting](#troubleshooting)
11. [Entwicklung](#entwicklung)

---

## Überblick

Pi Monitor ist eine selbst-gehostete Monitoring-Webseite, die Echtzeit-Metriken deines Raspberry Pi und aller laufenden Docker Container anzeigt. Die Anwendung läuft selbst in Docker und ist für den Betrieb hinter Traefik als Reverse Proxy optimiert.

### Warum Pi Monitor?

- **Leichtgewichtig**: Keine externen Datenbanken, keine komplexen Setups
- **Echtzeit**: Live-Updates alle 2-10 Sekunden (konfigurierbar)
- **Docker-native**: Läuft als Container, überwacht Container
- **Traefik-ready**: Sofort einsatzbereit mit Traefik Labels
- **Offline-fähig**: Keine Cloud-Abhängigkeiten

---

## Features

### Host-Metriken (Raspberry Pi)

| Metrik | Beschreibung | Quelle |
|--------|--------------|--------|
| **CPU-Auslastung** | Prozentuale CPU-Last | `/proc/stat` |
| **CPU-Frequenz** | Aktuelle Taktfrequenz in MHz | `/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq` |
| **RAM-Nutzung** | Genutzter/Verfügbarer Speicher | `/proc/meminfo` |
| **Load Average** | 1m, 5m, 15m Durchschnitt | `/proc/loadavg` |
| **Temperatur** | CPU-Kerntemperatur in °C | `/sys/class/thermal/thermal_zone0/temp` |
| **Uptime** | Betriebszeit in Stunden | `/proc/uptime` |
| **Hostname** | System-Hostname | `/etc/hostname` |

### Container-Metriken (Docker)

| Metrik | Beschreibung | Quelle |
|--------|--------------|--------|
| **Status** | running / stopped | Docker API |
| **CPU %** | CPU-Auslastung pro Container | Docker Stats API |
| **RAM** | Speicherverbrauch in MB | Docker Stats API |
| **Netzwerk RX** | Empfangene Bytes | Docker Stats API |
| **Netzwerk TX** | Gesendete Bytes | Docker Stats API |

### UI Features

- Grafana-ähnliches Dark-Theme (#050505 Hintergrund)
- Responsive Design (Mobile, Tablet, Desktop)
- Live-Verlaufsgraphen für CPU und RAM
- Farbcodierte Status-Anzeigen (Grün/Gelb/Rot)
- Konfigurierbares Refresh-Intervall (2s, 3s, 5s, 10s)
- Pulsierender Live-Indikator

---

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      Raspberry Pi                           │
│                                                             │
│  ┌─────────────┐    ┌─────────────────────────────────┐    │
│  │   Traefik   │───▶│        Pi Monitor Container      │    │
│  │  (Port 80)  │    │  ┌─────────┐    ┌───────────┐   │    │
│  └─────────────┘    │  │  Nginx  │───▶│  FastAPI  │   │    │
│         ▲           │  │ (静态)  │    │ (Backend) │   │    │
│         │           │  └─────────┘    └─────┬─────┘   │    │
│  ┌──────┴──────┐    │       │               │         │    │
│  │ Cloudflare  │    │       │               ▼         │    │
│  │   Tunnel    │    │       │    ┌──────────────────┐ │    │
│  └─────────────┘    │       │    │ Volume Mounts:   │ │    │
│                     │       │    │ • /proc (ro)     │ │    │
│                     │       │    │ • /sys (ro)      │ │    │
│                     │       │    │ • docker.sock(ro)│ │    │
│                     │       │    └──────────────────┘ │    │
│                     └───────┴─────────────────────────┘    │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Container 1 │  │ Container 2 │  │ Container N │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Komponenten

| Komponente | Technologie | Funktion |
|------------|-------------|----------|
| Frontend | React 19, Tailwind CSS, Recharts | Benutzeroberfläche |
| Backend | FastAPI, Python 3.11 | API für Metriken |
| Webserver | Nginx | Statische Dateien & Reverse Proxy |
| Prozess-Manager | Supervisor | Startet Nginx + Backend |

---

## Voraussetzungen

### Hardware
- Raspberry Pi 3/4/5 (empfohlen: Pi 4 mit 2GB+ RAM)
- ARM64 oder ARMv7 Architektur

### Software
- **Docker** >= 20.10
- **Docker Compose** Plugin (v2)
- Optional: **Traefik** als Reverse Proxy

### Docker Installation (falls nicht vorhanden)

```bash
# Docker installieren
curl -fsSL https://get.docker.com | sh

# Benutzer zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Neu einloggen oder:
newgrp docker

# Docker Compose ist Teil von Docker (als Plugin)
docker compose version
```

---

## Installation

### 1. Repository klonen

```bash
cd ~
git clone <repository-url> pi-monitor
cd pi-monitor
```

### 2. Traefik-Netzwerk erstellen (falls nicht vorhanden)

```bash
docker network create traefik-network
```

### 3. Domain anpassen

Bearbeite `docker-compose.yml` und ändere die Domain:

```yaml
labels:
  - "traefik.http.routers.monitor.rule=Host(`deine-domain.de`)"
```

### 4. Starten

```bash
./start.sh
```

Oder manuell:

```bash
docker compose up -d --build
```

### 5. Cloudflare Tunnel (optional)

Falls du Cloudflare Tunnel verwendest, füge einen Public Hostname hinzu:

| Public Hostname | Service |
|-----------------|---------|
| `deine-domain.de` | `http://localhost:80` |

---

## Konfiguration

### docker-compose.yml

```yaml
services:
  pi-monitor:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: pi-monitor
    restart: unless-stopped
    networks:
      - traefik-network
    volumes:
      # Host-Metriken (read-only)
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      # Docker-Metriken (read-only)
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - HOST_PROC=/host/proc
      - HOST_SYS=/host/sys
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.monitor.rule=Host(`monitor.example.com`)"
      - "traefik.http.routers.monitor.entrypoints=web"
      - "traefik.http.services.monitor.loadbalancer.server.port=80"
      - "traefik.docker.network=traefik-network"

networks:
  traefik-network:
    external: true
```

### Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `HOST_PROC` | `/host/proc` | Pfad zum gemounteten /proc |
| `HOST_SYS` | `/host/sys` | Pfad zum gemounteten /sys |

### Frontend Konfiguration

Das Refresh-Intervall kann im UI oben rechts geändert werden:
- 2 Sekunden (höchste Last)
- 3 Sekunden (Standard)
- 5 Sekunden
- 10 Sekunden (niedrigste Last)

---

## Traefik Integration

### Voraussetzung: Traefik läuft bereits

```bash
# Traefik-Verzeichnis
cd ~/traefik

# traefik/docker-compose.yml
services:
  traefik:
    image: traefik:v3.3
    container_name: traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/etc/traefik/traefik.yml:ro
    networks:
      - traefik-network

networks:
  traefik-network:
    external: true
```

```yaml
# traefik/traefik.yml
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: traefik-network
```

### Architektur mit Traefik

```
Internet → Cloudflare → Tunnel → Traefik (Port 80) → pi-monitor
                                                   → andere-apps
```

---

## API Referenz

### Base URL

```
http://localhost/api  (intern)
https://deine-domain.de/api  (extern via Traefik)
```

### Endpoints

#### GET /api/

Health Check

**Response:**
```json
{
  "message": "Pi Monitor API",
  "status": "live"
}
```

---

#### GET /api/metrics/host

Raspberry Pi Host-Metriken

**Response:**
```json
{
  "timestamp": "2026-03-31T15:25:00.286085+00:00",
  "cpu": {
    "usage_percent": 2.1,
    "cores": 4,
    "frequency_mhz": 1800
  },
  "memory": {
    "total_mb": 3796,
    "used_mb": 1019,
    "available_mb": 2777,
    "usage_percent": 26.8
  },
  "load_average": {
    "1min": 0.65,
    "5min": 0.42,
    "15min": 0.33
  },
  "temperature": {
    "celsius": 52.6
  },
  "uptime_hours": 23.4,
  "hostname": "raspberrypi"
}
```

---

#### GET /api/metrics/containers

Docker Container-Metriken

**Response:**
```json
[
  {
    "id": "e321fda95c8c",
    "name": "pi-monitor",
    "status": "running",
    "cpu": {
      "usage_percent": 0.4
    },
    "memory": {
      "usage_mb": 85,
      "limit_mb": 3796,
      "usage_percent": 2.2
    },
    "network": {
      "rx_bytes": 1234567,
      "tx_bytes": 654321,
      "rx_rate_kbps": 0.0,
      "tx_rate_kbps": 0.0
    },
    "uptime_seconds": 3600
  }
]
```

---

#### GET /api/metrics/all

Alle Metriken kombiniert

**Response:**
```json
{
  "host": { ... },
  "containers": [ ... ]
}
```

---

## Sicherheit

### Risikobewertung

| Risiko | Bewertung | Erklärung |
|--------|-----------|-----------|
| Remote Code Execution | ❌ Nicht möglich | Nur lesende GET-Endpoints |
| Netzwerk-Zugriff | ❌ Nicht möglich | Keine Netzwerk-Funktionen |
| Datenmanipulation | ❌ Nicht möglich | Keine POST/PUT/DELETE |
| Informations-Offenlegung | ⚠️ Ja | System-Metriken sichtbar |

### Was wird offengelegt?

- CPU/RAM/Temperatur-Werte
- Container-Namen (z.B. "nginx", "postgres")
- Hostname des Pi
- Uptime

### Absicherungsoptionen

#### Option 1: Basic Auth via Traefik

```bash
# Passwort generieren
htpasswd -nb admin dein-passwort
# Ausgabe: admin:$apr1$xyz...
```

```yaml
# docker-compose.yml - Labels ergänzen
labels:
  - "traefik.http.middlewares.monitor-auth.basicauth.users=admin:$$apr1$$xyz..."
  - "traefik.http.routers.monitor.middlewares=monitor-auth"
```

**Wichtig:** `$` muss als `$$` escaped werden in docker-compose.yml!

#### Option 2: IP-Whitelist

```yaml
labels:
  - "traefik.http.middlewares.monitor-ip.ipwhitelist.sourcerange=192.168.178.0/24,10.0.0.0/8"
  - "traefik.http.routers.monitor.middlewares=monitor-ip"
```

#### Option 3: VPN-Only

Cloudflare Tunnel deaktivieren und nur via VPN (z.B. WireGuard) zugreifen.

---

## Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker compose logs pi-monitor

# Supervisor-Logs im Container
docker compose exec pi-monitor cat /var/log/supervisor/backend.err.log
```

### 502 Bad Gateway

Backend läuft nicht oder hängt.

```bash
# Container neu starten
docker compose restart pi-monitor

# Komplett neu bauen
docker compose down
docker compose up -d --build
```

### API antwortet nicht

```bash
# Intern testen
docker compose exec pi-monitor curl -s localhost:8001/api/metrics/host

# Nginx prüfen
docker compose exec pi-monitor curl -s localhost/api/
```

### Metriken zeigen 0 oder undefined

Volume-Mounts prüfen:

```bash
# Prüfen ob /proc gemountet ist
docker compose exec pi-monitor ls /host/proc/

# Prüfen ob Docker-Socket gemountet ist
docker compose exec pi-monitor ls -la /var/run/docker.sock
```

### Container-RAM zeigt 0 MB

cgroup v2 Kompatibilitätsproblem. Stelle sicher, dass die neueste Version des Backends verwendet wird.

### Traefik routet nicht

```bash
# Traefik-Dashboard prüfen
http://<PI-IP>:8080

# Prüfen ob Container im traefik-network ist
docker network inspect traefik-network
```

---

## Entwicklung

### Lokale Entwicklung

```bash
# Backend
cd backend
pip install -r requirements-docker.txt
uvicorn server:app --reload --port 8001

# Frontend
cd frontend
yarn install
yarn start
```

### Projektstruktur

```
pi-monitor/
├── backend/
│   ├── server.py              # FastAPI Backend
│   └── requirements-docker.txt # Python Dependencies
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js             # Haupt-React-Komponente
│   │   ├── App.css            # Styles
│   │   └── index.js           # Entry Point
│   ├── package.json
│   └── tailwind.config.js
├── Dockerfile                  # Multi-stage Build
├── docker-compose.yml          # Traefik-ready Konfiguration
├── start.sh                    # Start-Script
├── stop.sh                     # Stop-Script
└── README.md                   # Diese Dokumentation
```

### Build für andere Architekturen

```bash
# Für AMD64 (Standard-Server)
docker buildx build --platform linux/amd64 -t pi-monitor:amd64 .

# Für ARM64 (Raspberry Pi 4/5)
docker buildx build --platform linux/arm64 -t pi-monitor:arm64 .

# Für ARMv7 (Raspberry Pi 3)
docker buildx build --platform linux/arm/v7 -t pi-monitor:armv7 .
```

---

## Scripts

### start.sh

```bash
#!/bin/bash
# Startet Pi Monitor mit Traefik-Netzwerk

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}   Pi Monitor - Start${NC}"

# Docker Check
if ! command -v docker &> /dev/null; then
    echo "Docker nicht installiert!"
    exit 1
fi

# Netzwerk erstellen falls nötig
if ! docker network ls | grep -q traefik-network; then
    echo -e "${YELLOW}Erstelle traefik-network...${NC}"
    docker network create traefik-network
fi

# Starten
docker compose up -d --build
docker compose ps
```

### stop.sh

```bash
#!/bin/bash
# Stoppt Pi Monitor

docker compose down
echo "Pi Monitor gestoppt."
```

---

## Changelog

### v1.0 (2026-03-31)
- Initial Release
- Host-Metriken: CPU, RAM, Load, Temperatur, Uptime
- Container-Metriken: CPU, RAM, Netzwerk
- Grafana-ähnliches Dark-Theme
- Traefik-Integration
- Echtzeit-Updates (2-10s)

---

## Lizenz

MIT License - Frei verwendbar für private und kommerzielle Zwecke.

---

## Support

Bei Problemen:
1. [Troubleshooting](#troubleshooting) Sektion prüfen
2. Logs analysieren: `docker compose logs pi-monitor`
3. Issue erstellen mit:
   - Pi-Modell
   - Docker-Version (`docker --version`)
   - Fehlermeldung/Screenshot
