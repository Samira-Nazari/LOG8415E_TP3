import random
import subprocess
import time
from fastapi import FastAPI, HTTPException
import mysql.connector
from typing import List

app = FastAPI()

# Replace these with your actual IPs and credentials
MANAGER_IP = "manager_ip_here"
WORKER_IPS = ["worker1_ip_here", "worker2_ip_here"]
DB_USER = "root"
DB_PASSWORD = "123456"
DB_NAME = "sakila"

def execute_query(ip_address: str, query: str):
    try:
        conn = mysql.connector.connect(
            host=ip_address,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.commit()
        return results
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

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

@app.get("/query/{strategy}")
async def route_query(query: str, strategy: str):
    if "select" in query.lower():
        # READ operation
        if strategy == "direct":
            # Direct hit to the manager
            return execute_query(MANAGER_IP, query)
        elif strategy == "random":
            # Randomly choose one of the workers
            worker_ip = random.choice(WORKER_IPS)
            return execute_query(worker_ip, query)
        elif strategy == "customized":
            # Choose worker with the lowest ping time
            fastest_worker = min(WORKER_IPS, key=measure_ping)
            return execute_query(fastest_worker, query)
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy")
    else:
        # WRITE operation
        if strategy == ["direct", "random", "customized"]:
            # Directly forward to manager for writes
            execute_query(MANAGER_IP, query)
            for worker_ip in WORKER_IPS:
                execute_query(worker_ip, query)  # Replicate to workers
            return {"status": "Write replicated to all instances"}
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy")

