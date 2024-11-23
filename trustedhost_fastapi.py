from fastapi import FastAPI, HTTPException, Request
import httpx
import os

app = FastAPI()

proxy_ip = os.getenv("PROXY_IP")
if not proxy_ip:
    raise ValueError("Environment variable PROXY_IP must be set.")

@app.get("/")
async def root():
    return {"message": "Trusted Host is running!"}

@app.get("/status")
async def status():
    return {"status": "ok"}

'''
@app.post("/process_request/")
async def process_request(request: Request):
    try:
        # Forward requests to the Proxy
        data = await request.json()
        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://{proxy_ip}:8000/query/random", json=data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

@app.post("/process_request/{strategy}")
async def process_request(strategy: str, request: Request):
    if strategy in ["direct", "random", "customized"]:
        try:
        # Forward requests to the Proxy
            data = await request.json()
            async with httpx.AsyncClient() as client:
                url = f"http://{proxy_ip}:8000/query/{strategy}"
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Invalid strategy")

