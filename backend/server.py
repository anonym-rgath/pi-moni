from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
import logging
import os
import json
import socket
from typing import List, Dict, Any
from datetime import datetime, timezone

app = FastAPI(title="Pi Monitor API")
api_router = APIRouter(prefix="/api")

DOCKER_SOCKET = "/var/run/docker.sock"
HOST_PROC = os.environ.get('HOST_PROC', '/proc')
HOST_SYS = os.environ.get('HOST_SYS', '/sys')

# CPU usage tracking
_prev_cpu = None

def read_file(path: str) -> str:
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logging.warning(f"Cannot read {path}: {e}")
        return ""

def get_cpu_usage() -> float:
    global _prev_cpu
    try:
        with open(f'{HOST_PROC}/stat', 'r') as f:
            line = f.readline()
        parts = line.split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:8])
        
        if _prev_cpu is None:
            _prev_cpu = (idle, total)
            return 0.0
        
        prev_idle, prev_total = _prev_cpu
        _prev_cpu = (idle, total)
        
        idle_delta = idle - prev_idle
        total_delta = total - prev_total
        
        if total_delta == 0:
            return 0.0
        
        return round((1 - idle_delta / total_delta) * 100, 1)
    except Exception as e:
        logging.warning(f"CPU error: {e}")
        return 0.0

def get_memory_info() -> Dict[str, Any]:
    try:
        mem = {}
        with open(f'{HOST_PROC}/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(':')
                mem[key] = int(parts[1])
        
        total = mem.get('MemTotal', 0) // 1024
        available = mem.get('MemAvailable', 0) // 1024
        used = total - available
        percent = round((used / total) * 100, 1) if total > 0 else 0
        
        return {"total_mb": total, "used_mb": used, "available_mb": available, "usage_percent": percent}
    except Exception as e:
        logging.warning(f"Memory error: {e}")
        return {"total_mb": 0, "used_mb": 0, "available_mb": 0, "usage_percent": 0}

def get_cpu_info() -> Dict[str, Any]:
    cores = os.cpu_count() or 4
    freq = 1500
    try:
        freq_str = read_file(f'{HOST_SYS}/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq')
        if freq_str:
            freq = int(freq_str) // 1000
    except:
        pass
    return {"cores": cores, "frequency_mhz": freq}

def get_temperature() -> float:
    try:
        temp_str = read_file(f'{HOST_SYS}/class/thermal/thermal_zone0/temp')
        if temp_str:
            return round(int(temp_str) / 1000, 1)
    except:
        pass
    return 0.0

def get_load_average() -> Dict[str, float]:
    try:
        with open(f'{HOST_PROC}/loadavg', 'r') as f:
            load = f.read().strip().split()
        return {"1min": float(load[0]), "5min": float(load[1]), "15min": float(load[2])}
    except Exception as e:
        logging.warning(f"Load error: {e}")
        return {"1min": 0.0, "5min": 0.0, "15min": 0.0}

def get_uptime() -> float:
    try:
        with open(f'{HOST_PROC}/uptime', 'r') as f:
            uptime_str = f.read().strip().split()[0]
        return round(float(uptime_str) / 3600, 1)
    except:
        return 0.0

def get_hostname() -> str:
    try:
        return socket.gethostname()
    except:
        return "raspberrypi"

def docker_request(endpoint: str, timeout: float = 2.0) -> Any:
    """Query Docker API with timeout"""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(DOCKER_SOCKET)
        
        request = f"GET {endpoint} HTTP/1.0\r\nHost: localhost\r\n\r\n"
        sock.send(request.encode())
        
        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break
        sock.close()
        
        # Parse response body
        if b"\r\n\r\n" in response:
            body = response.split(b"\r\n\r\n", 1)[1]
            return json.loads(body.decode('utf-8', errors='ignore'))
    except Exception as e:
        logging.warning(f"Docker API error: {e}")
    return None

def get_containers() -> List[Dict[str, Any]]:
    containers = []
    try:
        data = docker_request("/containers/json?all=true")
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
                stats = docker_request(f"/containers/{container_id}/stats?stream=false", timeout=3.0)
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
                        for net in stats.get('networks', {}).values():
                            container['network']['rx_bytes'] += net.get('rx_bytes', 0)
                            container['network']['tx_bytes'] += net.get('tx_bytes', 0)
                    except:
                        pass
            
            containers.append(container)
    except Exception as e:
        logging.error(f"Container error: {e}")
    
    return containers

@api_router.get("/")
async def root():
    return {"message": "Pi Monitor API", "status": "live"}

@api_router.get("/metrics/host")
async def get_host_metrics():
    cpu_info = get_cpu_info()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu": {"usage_percent": get_cpu_usage(), "cores": cpu_info["cores"], "frequency_mhz": cpu_info["frequency_mhz"]},
        "memory": get_memory_info(),
        "load_average": get_load_average(),
        "temperature": {"celsius": get_temperature()},
        "uptime_hours": get_uptime(),
        "hostname": get_hostname()
    }

@api_router.get("/metrics/containers")
async def get_container_metrics():
    return get_containers()

@api_router.get("/metrics/all")
async def get_all_metrics():
    cpu_info = get_cpu_info()
    return {
        "host": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {"usage_percent": get_cpu_usage(), "cores": cpu_info["cores"], "frequency_mhz": cpu_info["frequency_mhz"]},
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
