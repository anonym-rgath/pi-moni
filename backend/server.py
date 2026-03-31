from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
import logging
import os
import json
import urllib.request
import socket
from typing import List, Dict, Any
from datetime import datetime, timezone

app = FastAPI(title="Pi Monitor API")
api_router = APIRouter(prefix="/api")

# Docker Socket
DOCKER_SOCKET = "/var/run/docker.sock"

def read_file(path: str) -> str:
    """Read file content - try host path first, then container path"""
    host_proc = os.environ.get('HOST_PROC', '/proc')
    host_sys = os.environ.get('HOST_SYS', '/sys')
    
    # Map paths to host mounts
    if path.startswith('/proc'):
        path = path.replace('/proc', host_proc, 1)
    elif path.startswith('/sys'):
        path = path.replace('/sys', host_sys, 1)
    
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except:
        return ""

def get_cpu_usage() -> float:
    """Get CPU usage from /proc/stat"""
    host_proc = os.environ.get('HOST_PROC', '/proc')
    try:
        with open(f'{host_proc}/stat', 'r') as f:
            line = f.readline()
        parts = line.split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:8])
        
        # Store for delta calculation
        if not hasattr(get_cpu_usage, 'prev'):
            get_cpu_usage.prev = (idle, total)
            return 0.0
        
        prev_idle, prev_total = get_cpu_usage.prev
        get_cpu_usage.prev = (idle, total)
        
        idle_delta = idle - prev_idle
        total_delta = total - prev_total
        
        if total_delta == 0:
            return 0.0
        
        return round((1 - idle_delta / total_delta) * 100, 1)
    except:
        return 0.0

def get_memory_info() -> Dict[str, Any]:
    """Get memory info from /proc/meminfo"""
    host_proc = os.environ.get('HOST_PROC', '/proc')
    try:
        mem = {}
        with open(f'{host_proc}/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(':')
                mem[key] = int(parts[1])
        
        total = mem.get('MemTotal', 0) // 1024
        available = mem.get('MemAvailable', 0) // 1024
        used = total - available
        percent = round((used / total) * 100, 1) if total > 0 else 0
        
        return {
            "total_mb": total,
            "used_mb": used,
            "available_mb": available,
            "usage_percent": percent
        }
    except:
        return {"total_mb": 0, "used_mb": 0, "available_mb": 0, "usage_percent": 0}

def get_cpu_info() -> Dict[str, Any]:
    """Get CPU cores and frequency"""
    host_sys = os.environ.get('HOST_SYS', '/sys')
    cores = os.cpu_count() or 4
    freq = 1500
    try:
        freq_str = read_file(f'{host_sys}/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq')
        if freq_str:
            freq = int(freq_str) // 1000
    except:
        pass
    return {"cores": cores, "frequency_mhz": freq}

def get_temperature() -> float:
    """Get CPU temperature"""
    host_sys = os.environ.get('HOST_SYS', '/sys')
    try:
        temp_str = read_file(f'{host_sys}/class/thermal/thermal_zone0/temp')
        if temp_str:
            return round(int(temp_str) / 1000, 1)
    except:
        pass
    return 0.0

def get_load_average() -> Dict[str, float]:
    """Get load average from /proc/loadavg"""
    host_proc = os.environ.get('HOST_PROC', '/proc')
    try:
        with open(f'{host_proc}/loadavg', 'r') as f:
            load = f.read().strip().split()
        return {
            "1min": float(load[0]),
            "5min": float(load[1]),
            "15min": float(load[2])
        }
    except:
        return {"1min": 0.0, "5min": 0.0, "15min": 0.0}

def get_uptime() -> float:
    """Get uptime in hours"""
    host_proc = os.environ.get('HOST_PROC', '/proc')
    try:
        with open(f'{host_proc}/uptime', 'r') as f:
            uptime_str = f.read().strip().split()[0]
        return round(float(uptime_str) / 3600, 1)
    except:
        return 0.0

def docker_api(endpoint: str) -> Any:
    """Query Docker API via socket"""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(DOCKER_SOCKET)
        request = f"GET {endpoint} HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock.send(request.encode())
        
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        sock.close()
        
        # Parse HTTP response
        parts = response.split(b"\r\n\r\n", 1)
        if len(parts) > 1:
            body = parts[1]
            # Handle chunked encoding
            if b"\r\n" in body and body[:10].replace(b'\r\n', b'').isalnum():
                lines = body.split(b"\r\n")
                body = b"".join(lines[1::2])
            return json.loads(body.decode('utf-8', errors='ignore'))
    except Exception as e:
        logging.error(f"Docker API error: {e}")
    return None

def get_containers() -> List[Dict[str, Any]]:
    """Get Docker container metrics"""
    containers = []
    
    try:
        # Get container list
        data = docker_api("/containers/json?all=true")
        if not data:
            return containers
        
        for c in data:
            name = c.get('Names', ['/unknown'])[0].lstrip('/')
            state = c.get('State', 'unknown')
            container_id = c.get('Id', '')[:12]
            
            container = {
                "id": container_id,
                "name": name,
                "status": state,
                "cpu": {"usage_percent": 0.0},
                "memory": {"usage_mb": 0, "limit_mb": 0, "usage_percent": 0.0},
                "network": {"rx_bytes": 0, "tx_bytes": 0, "rx_rate_kbps": 0.0, "tx_rate_kbps": 0.0},
                "uptime_seconds": 0
            }
            
            if state == "running":
                # Get stats
                stats = docker_api(f"/containers/{container_id}/stats?stream=false")
                if stats:
                    # CPU
                    try:
                        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                        num_cpus = stats['cpu_stats'].get('online_cpus', 1)
                        if system_delta > 0:
                            container['cpu']['usage_percent'] = round((cpu_delta / system_delta) * num_cpus * 100, 1)
                    except:
                        pass
                    
                    # Memory
                    try:
                        mem_usage = stats['memory_stats'].get('usage', 0)
                        mem_limit = stats['memory_stats'].get('limit', 1)
                        container['memory']['usage_mb'] = mem_usage // (1024 * 1024)
                        container['memory']['limit_mb'] = mem_limit // (1024 * 1024)
                        container['memory']['usage_percent'] = round((mem_usage / mem_limit) * 100, 1) if mem_limit > 0 else 0
                    except:
                        pass
                    
                    # Network
                    try:
                        networks = stats.get('networks', {})
                        for net in networks.values():
                            container['network']['rx_bytes'] += net.get('rx_bytes', 0)
                            container['network']['tx_bytes'] += net.get('tx_bytes', 0)
                    except:
                        pass
            
            containers.append(container)
    except Exception as e:
        logging.error(f"Container error: {e}")
    
    return containers

def get_hostname() -> str:
    """Get system hostname"""
    try:
        return socket.gethostname()
    except:
        return "raspberrypi"

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Pi Monitor API", "status": "live"}

@api_router.get("/metrics/host")
async def get_host_metrics():
    """Get Raspberry Pi host metrics"""
    cpu_info = get_cpu_info()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu": {
            "usage_percent": get_cpu_usage(),
            "cores": cpu_info["cores"],
            "frequency_mhz": cpu_info["frequency_mhz"]
        },
        "memory": get_memory_info(),
        "load_average": get_load_average(),
        "temperature": {"celsius": get_temperature()},
        "uptime_hours": get_uptime(),
        "hostname": get_hostname()
    }

@api_router.get("/metrics/containers")
async def get_container_metrics():
    """Get Docker container metrics"""
    return get_containers()

@api_router.get("/metrics/all")
async def get_all_metrics():
    """Get all metrics"""
    cpu_info = get_cpu_info()
    return {
        "host": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {
                "usage_percent": get_cpu_usage(),
                "cores": cpu_info["cores"],
                "frequency_mhz": cpu_info["frequency_mhz"]
            },
            "memory": get_memory_info(),
            "load_average": get_load_average(),
            "temperature": {"celsius": get_temperature()},
            "uptime_hours": get_uptime(),
            "hostname": get_hostname()
        },
        "containers": get_containers()
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
