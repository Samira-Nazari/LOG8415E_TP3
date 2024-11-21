from fastapi import FastAPI, HTTPException
import httpx
import random
import os
import subprocess
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

app = FastAPI()
manager_ip = os.getenv("MANAGER_IP")
worker_ips = os.getenv("WORKER_IPS", "").split(",")

if not manager_ip or not worker_ips:
    raise ValueError("Environment variables MANAGER_IP and WORKER_IPS must be set correctly.")

def measure_ping(ip_address: str):
    try:
        response = subprocess.run(
            ["ping", "-c", "1", ip_address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if response.returncode == 0:
            ping_time = float(response.stdout.split("time=")[-1].split(" ms")[0])
            return ping_time
    except Exception as e:
        print(f"Error measuring ping for {ip_address}: {e}")
    return float("inf")

@app.get("/")
async def root():
    return {"message": "Proxy is running!"}

@app.get("/status")
async def status():
    return {"status": "ok"}

@app.post("/query/{strategy}")
async def route_query(strategy: str, query_request: QueryRequest):
    query = query_request.query
    if "select" in query.lower():
        # READ operation
        if strategy == "direct":
            url = f"http://{manager_ip}:8000/execute"
        elif strategy == "random":
            worker_ip = random.choice(worker_ips)
            url = f"http://{worker_ip}:8000/execute"
        elif strategy == "customized":
            fastest_worker_ip = min(worker_ips, key=measure_ping)
            url = f"http://{fastest_worker_ip}:8000/execute"
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy")
    else:
        # WRITE operation
        if strategy in ["direct", "random", "customized"]:
            url = f"http://{manager_ip}:8000/execute"
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json={"query": query})
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Request to {url} failed: {exc}")
