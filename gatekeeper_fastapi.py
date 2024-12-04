from fastapi import FastAPI, HTTPException, Request
import httpx
import os

app = FastAPI()

trusted_host_ip = os.getenv("TRUSTED_HOST_IP")
if not trusted_host_ip:
    raise ValueError("Environment variable TRUSTED_HOST_IP must be set.")

@app.get("/")
async def root():
    return {"message": "Gatekeeper is running!"}

@app.get("/status")
async def status():
    return {"status": "ok"}


@app.post("/validate_request/{strategy}")
async def validate_request(strategy: str, request: Request):
    try:
        # Simulate input validation (implement your own rules)
        data = await request.json()
        query = data.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query not provided")
        if "DROP" in query.upper():
            raise HTTPException(status_code=403, detail="Potentially malicious query detected")

        # Forward validated requests to the trusted host
        async with httpx.AsyncClient() as client:
            url = f"http://{trusted_host_ip}:8000/process_request/{strategy}"
            response = await client.post( url, json=data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
