from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
import random
import logging
from typing import List, Dict, Any
import uuid
from datetime import datetime, timezone

# Create the main app
app = FastAPI(title="Pi Monitor API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Mock data generators
CONTAINER_NAMES = ["nginx", "postgres", "redis", "grafana", "prometheus", "cadvisor"]

def generate_host_metrics() -> Dict[str, Any]:
    """Generate mock Raspberry Pi host metrics"""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu": {
            "usage_percent": round(random.uniform(15, 85), 1),
            "cores": 4,
            "frequency_mhz": 1500
        },
        "memory": {
            "total_mb": 4096,
            "used_mb": round(random.uniform(1500, 3500), 0),
            "usage_percent": round(random.uniform(35, 85), 1)
        },
        "load_average": {
            "1min": round(random.uniform(0.5, 3.0), 2),
            "5min": round(random.uniform(0.4, 2.5), 2),
            "15min": round(random.uniform(0.3, 2.0), 2)
        },
        "temperature": {
            "celsius": round(random.uniform(45, 72), 1)
        },
        "uptime_hours": round(random.uniform(24, 720), 1),
        "hostname": "raspberrypi"
    }

def generate_container_metrics() -> List[Dict[str, Any]]:
    """Generate mock Docker container metrics"""
    containers = []
    for name in CONTAINER_NAMES:
        status = random.choices(["running", "stopped"], weights=[0.9, 0.1])[0]
        containers.append({
            "id": str(uuid.uuid4())[:12],
            "name": name,
            "status": status,
            "cpu": {
                "usage_percent": round(random.uniform(1, 45), 1) if status == "running" else 0
            },
            "memory": {
                "usage_mb": round(random.uniform(50, 512), 0) if status == "running" else 0,
                "limit_mb": 1024,
                "usage_percent": round(random.uniform(5, 50), 1) if status == "running" else 0
            },
            "network": {
                "rx_bytes": round(random.uniform(100000, 50000000), 0) if status == "running" else 0,
                "tx_bytes": round(random.uniform(50000, 25000000), 0) if status == "running" else 0,
                "rx_rate_kbps": round(random.uniform(10, 5000), 1) if status == "running" else 0,
                "tx_rate_kbps": round(random.uniform(5, 2500), 1) if status == "running" else 0
            },
            "uptime_seconds": round(random.uniform(3600, 604800), 0) if status == "running" else 0
        })
    return containers

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Pi Monitor API"}

@api_router.get("/metrics/host")
async def get_host_metrics():
    """Get current Raspberry Pi host metrics"""
    return generate_host_metrics()

@api_router.get("/metrics/containers")
async def get_container_metrics():
    """Get current Docker container metrics"""
    return generate_container_metrics()

@api_router.get("/metrics/all")
async def get_all_metrics():
    """Get all metrics in one call"""
    return {
        "host": generate_host_metrics(),
        "containers": generate_container_metrics()
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
