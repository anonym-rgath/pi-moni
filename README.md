# Pi Monitor - Raspberry Pi & Docker Monitoring Dashboard

Eine leichtgewichtige Echtzeit-Monitoring-Lösung für Raspberry Pi und Docker Container mit Grafana-ähnlichem Dark-Design.

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
| **RAM-Nutzung** | Genutzter/Verfügbarer Speicher in MB | `/proc/meminfo` |
| **Swap-Nutzung** | Swap-Speicher verwendet/gesamt | `/proc/meminfo` |
| **Disk-Speicher** | SD-Karte verwendet/gesamt in GB | `os.statvfs` |
| **Load Average** | 1m, 5m, 15m Systemlast | `/proc/loadavg` |
| **Temperatur** | CPU-Kerntemperatur in °C | `/sys/class/thermal/thermal_zone0/temp` |
| **Uptime** | Betriebszeit in Tagen/Stunden | `/proc/uptime` |
| **Hostname** | System-Hostname | `/etc/hostname` |
| **Prozesse** | Anzahl laufender Prozesse | `/proc` |

### Container-Metriken (Docker)

| Metrik | Beschreibung | Quelle |
|--------|--------------|--------|
| **Status** | running / stopped | Docker API |
| **CPU %** | CPU-Auslastung pro Container | Docker Stats API |
| **RAM** | Speicherverbrauch in MB | Docker Stats API |
| **Netzwerk RX** | Empfangene Daten in MB | Docker Stats API |
| **Netzwerk TX** | Gesendete Daten in MB | Docker Stats API |
| **Uptime** | Container-Laufzeit | Docker API |
| **Restart Count** | Anzahl Neustarts | Docker Inspect API |

### UI Features

- Grafana-ähnliches Dark-Theme (#050505 Hintergrund)
- Responsive Design (Mobile, Tablet, Desktop)
- Live-Verlaufsgraphen für CPU und RAM (letzte 20 Datenpunkte)
- Swap-Anzeige (nur wenn Swap konfiguriert)
- Farbcodierte Status-Anzeigen:
  - 🟢 Grün: < 60%
  - 🟡 Gelb: 60-80%
  - 🔴 Rot: > 80%
- Konfigurierbares Refresh-Intervall (2s, 3s, 5s, 10s)
- Pulsierender Live-Indikator
- Prozess-Anzahl im Footer

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
│                     │       │    │ • /etc/hostname  │ │    │
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
      - /etc/hostname:/host/etc/hostname:ro
      # Docker-Metriken (read-only)
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - HOST_PROC=/host/proc
      - HOST_SYS=/host/sys
      - HOST_ETC=/host/etc
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

### Volume Mounts

| Mount | Zweck |
|-------|-------|
| `/proc:/host/proc:ro` | CPU, RAM, Load, Uptime, Prozesse |
| `/sys:/host/sys:ro` | Temperatur, CPU-Frequenz |
| `/etc/hostname:/host/etc/hostname:ro` | Hostname des Pi |
| `/var/run/docker.sock:ro` | Docker Container Metriken |

### Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `HOST_PROC` | `/host/proc` | Pfad zum gemounteten /proc |
| `HOST_SYS` | `/host/sys` | Pfad zum gemounteten /sys |
| `HOST_ETC` | `/host/etc` | Pfad zum gemounteten /etc |

### Frontend Konfiguration

Das Refresh-Intervall kann im UI oben rechts geändert werden:

| Intervall | Empfehlung |
|-----------|------------|
| 2 Sekunden | Debugging, hohe CPU-Last |
| 3 Sekunden | Standard, guter Kompromiss |
| 5 Sekunden | Normale Nutzung |
| 10 Sekunden | Niedrige Last, Langzeit-Monitoring |

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
    "usage_percent": 26.8,
    "swap_total_mb": 100,
    "swap_used_mb": 0,
    "swap_percent": 0.0
  },
  "disk": {
    "total_gb": 32,
    "used_gb": 8,
    "free_gb": 24,
    "usage_percent": 25.0
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
  "process_count": 142,
  "hostname": "pi4gath"
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
    "uptime_seconds": 3600,
    "restart_count": 0
  }
]
```

---

#### GET /api/metrics/all

Alle Metriken kombiniert (empfohlen für Dashboard)

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

- CPU/RAM/Disk/Temperatur-Werte
- Container-Namen und Status
- Hostname des Pi
- Uptime und Prozess-Anzahl

### Volume-Mount Sicherheit

Alle Mounts sind **read-only** (`:ro`):
- `/proc` - Nur Lesen von Systemmetriken
- `/sys` - Nur Lesen von Hardware-Info
- `/etc/hostname` - Nur Hostname
- `docker.sock` - Nur Container-Info abfragen

---

## Lizenz

MIT License - Frei verwendbar für private und kommerzielle Zwecke.
