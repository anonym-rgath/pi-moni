# Pi Monitor - Raspberry Pi & Docker Monitoring Dashboard

Ein Grafana-ähnliches Monitoring-Dashboard für Raspberry Pi und Docker Container.

## Features

### Raspberry Pi Host-Metriken
- CPU-Auslastung (gesamt)
- RAM-Nutzung (gesamt)
- Load Average (1m, 5m, 15m)
- Temperatur
- Uptime

### Docker Container-Metriken
- CPU-Verbrauch je Container
- RAM-Verbrauch je Container
- Netzwerk-Traffic (RX/TX) je Container
- Container-Status (running/stopped)

### UI Features
- Grafana-ähnliches dunkles Design
- Echtzeit-Updates (konfigurierbar: 2s, 3s, 5s, 10s)
- Responsive Layout
- Live-Verlaufsgraphen für CPU und RAM

## Deployment auf Raspberry Pi

### Voraussetzungen
- Docker und Docker Compose installiert
- Git (optional)

### Installation

1. Repository klonen oder Dateien kopieren:
```bash
git clone <repository-url>
cd pi-monitor
```

2. Mit Docker Compose starten:
```bash
docker-compose up -d
```

3. Dashboard öffnen:
```
http://<raspberry-pi-ip>:80
```

### Nur Frontend + Backend (ohne MongoDB)

Falls Sie MongoDB separat betreiben:

```bash
# .env Datei erstellen
echo "MONGO_URL=mongodb://your-mongo-host:27017" > backend/.env
echo "DB_NAME=pi_monitor" >> backend/.env

# Docker Image bauen
docker build -t pi-monitor .

# Container starten
docker run -d -p 80:80 \
  -e MONGO_URL=mongodb://your-mongo-host:27017 \
  -e DB_NAME=pi_monitor \
  pi-monitor
```

## Entwicklung

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

### Frontend (React)
```bash
cd frontend
yarn install
yarn start
```

## Technologie-Stack

- **Frontend**: React, Tailwind CSS, Recharts, Lucide Icons
- **Backend**: FastAPI, Python 3.11
- **Datenbank**: MongoDB
- **Deployment**: Docker, Nginx, Supervisor

## Erweiterungen

Um echte Metriken statt Mock-Daten zu verwenden:

1. **cAdvisor** für Docker-Metriken integrieren
2. **Node Exporter** für Host-Metriken integrieren
3. API-Endpoints anpassen um von Prometheus zu lesen

## Lizenz

MIT License
