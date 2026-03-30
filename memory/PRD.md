# Pi Monitor - Product Requirements Document

## Original Problem Statement
Eine Monitoring-Webseite mit Grafana als Frontend-Stil, für Docker-Container-Metriken und Raspberry-Pi-Host-Metriken.

## User Choices
- Custom Monitoring Dashboard (nicht echter Grafana/Prometheus Stack)
- Mock-Daten für Demo-Zwecke
- Grafana-ähnliches dunkles Dashboard-Design
- Echtzeit-Updates (Auto-Refresh)
- Docker-ready für Raspberry Pi Deployment

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI (Python)
- **Database**: MongoDB (für Status-Logs)
- **Deployment**: Docker + Docker Compose

## Core Requirements (Static)
| Feature | Status |
|---------|--------|
| Host CPU-Auslastung | ✅ Implemented |
| Host RAM-Nutzung | ✅ Implemented |
| Host Load Average | ✅ Implemented |
| Host Temperatur | ✅ Implemented |
| Container CPU | ✅ Implemented |
| Container RAM | ✅ Implemented |
| Container Netzwerk | ✅ Implemented |
| Auto-Refresh | ✅ Implemented |
| Dark Theme | ✅ Implemented |
| Docker Deployment | ✅ Implemented |

## What's Been Implemented
**Date: 2026-03-30**
- Backend API mit Mock-Metriken Generator
- Grafana-ähnliches Dark Dashboard UI
- Echtzeit-Charts für CPU und RAM Verlauf
- Container-Übersicht mit Status-Anzeige
- Konfigurierbares Refresh-Intervall (2s, 3s, 5s, 10s)
- Dockerfile und docker-compose.yml für Deployment

## Prioritized Backlog
### P0 (Done)
- ✅ Mock data generation
- ✅ Dashboard UI
- ✅ Real-time updates

### P1 (Nice to Have)
- Integration mit echtem cAdvisor
- Integration mit echtem Node Exporter
- Prometheus-Datenquelle

### P2 (Future)
- Alerting/Benachrichtigungen
- Historische Daten-Ansicht
- Multi-Host Support

## Next Tasks
1. Echte Metriken via cAdvisor/Node Exporter integrieren
2. Alerting hinzufügen bei hoher Auslastung
3. Persistente Metriken-Historie
