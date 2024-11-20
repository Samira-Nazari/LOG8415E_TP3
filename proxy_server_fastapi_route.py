from fastapi import FastAPI, Request
import httpx
import random
import os
import subprocess


app = FastAPI()
manager_ip = os.getenv("MANAGER_IP")
worker_ips = os.getenv("WORKER_IPS").split(",")

def measure_ping(ip_address: str):
    response = subprocess.run(
        ["ping", "-c", "1", ip_address],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if response.returncode == 0:
        ping_time = float(response.stdout.decode().split("time=")[-1].split(" ms")[0])
        return ping_time
    else:
        return float("inf")

@app.get("/")
async def root():
    return {"message": "Proxy is running!"}


@app.get("/status")
async def status():
    return {"status": "ok"}

@app.post("/query/{strategy}")
#async def route_query(query: str, strategy: str):
async def route_query(query_request: QueryRequest, strategy: str):
    query = query_request.query  # Extract query from request body
    if "select" in query.lower():
        # READ operation
        if strategy == "direct":
            # Direct hit to the manager
            url = f"http://{manager_ip}:8000/execute"
        elif strategy == "random":
            # Randomly choose one of the workers
            worker_ip = random.choice(worker_ips)
            url = f"http://{worker_ip}:8000/execute"
        elif strategy == "customized":
            # Choose worker with the lowest ping time
            fastest_worker_ip = min(worker_ips, key=measure_ping)
            url = f"http://{fastest_worker_ip}:8000/execute"
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy")
    else:
        # WRITE operation
        if strategy == ["direct", "random", "customized"]:
            # Directly forward to manager for writes
            url = f"http://{manager_ip}:8000/execute"
            '''
            for worker_ip in WORKER_IPS:
                execute_query(worker_ip, query)  # Replicate to workers
            return {"status": "Write replicated to all instances"}
            ''' 
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy")
    async with httpx.AsyncClient() as client:
        #response = await client.post(url, json=data)
        response = await client.post(url, json={"query": query})
        return response.json()
