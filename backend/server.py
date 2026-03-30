from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

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

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class HostMetrics(BaseModel):
    timestamp: str
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    load_average: Dict[str, Any]
    temperature: Dict[str, Any]
    uptime_hours: float
    hostname: str

class ContainerMetrics(BaseModel):
    id: str
    name: str
    status: str
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    network: Dict[str, Any]
    uptime_seconds: float

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Pi Monitor API"}

@api_router.get("/metrics/host", response_model=HostMetrics)
async def get_host_metrics():
    """Get current Raspberry Pi host metrics"""
    return generate_host_metrics()

@api_router.get("/metrics/containers", response_model=List[ContainerMetrics])
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

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
