#!/bin/bash

# Check if sufficient arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <proxy_ip> <manager_ip> <worker_ips>"
    echo "Example: $0 54.167.204.147 54.227.86.12 100.26.46.118,54.227.17.17"
    exit 1
fi

PROXY_IP=$1
MANAGER_IP=$2
WORKER_IPS=$3
PEM_FILE="TP3_pem_3.pem"

# Step 1: Install python3-venv and Python dependencies in a virtual environment on the proxy server
echo "Installing python3-venv and creating a virtual environment on the proxy server..."
ssh -i "$PEM_FILE" -o "StrictHostKeyChecking=no" ubuntu@"$PROXY_IP" <<EOF
    # Update the package list and install python3-venv if not already installed
    sudo apt-get update
    sudo apt-get install -y python3-venv

    # Create a virtual environment
    python3 -m venv /home/ubuntu/fastapi_env

    # Activate the virtual environment
    source /home/ubuntu/fastapi_env/bin/activate

    # Install dependencies inside the virtual environment
    pip install fastapi uvicorn httpx
EOF

# Step 2: Transfer the FastAPI script to the proxy server
echo "Transferring proxy_server_fastapi_route.py to the proxy server..."
scp -i "$PEM_FILE" -o "StrictHostKeyChecking=no" proxy_server_fastapi_route.py ubuntu@"$PROXY_IP":/home/ubuntu/proxy_server_fastapi_route.py

# Step 3: Set environment variables directly for the current session
echo "Setting environment variables on the proxy server..."
ssh -i "$PEM_FILE" -o "StrictHostKeyChecking=no" ubuntu@"$PROXY_IP" <<EOF
    export MANAGER_IP=$MANAGER_IP
    export WORKER_IPS=$WORKER_IPS
EOF

# Step 4: Start the FastAPI proxy server with the correct host binding
echo "Starting the FastAPI proxy server..."
ssh -i "$PEM_FILE" -o "StrictHostKeyChecking=no" ubuntu@"$PROXY_IP" <<EOF
    # Activate the virtual environment
    source /home/ubuntu/fastapi_env/bin/activate

    # Run FastAPI with uvicorn
    nohup uvicorn /home/ubuntu/proxy_server_fastapi_route.py:app --host 0.0.0.0 --port 8000 > /home/ubuntu/proxy_server.log 2>&1 &
EOF

echo "FastAPI proxy server deployed successfully on $PROXY_IP."
