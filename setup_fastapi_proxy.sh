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
KEY_PATH="TP3_pem_3.pem"
REMOTE_USER="ubuntu"
MAX_RETRIES=5
RETRY_DELAY=30
APP_FILE="proxy_server_fastapi_route.py"

function attempt_ssh() {
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_USER@$1 "echo 'Connected'"
}

# Retry loop to wait for SSH availability
for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Attempting to connect to proxy server ${PROXY_IP} (attempt $i of $MAX_RETRIES)..."
    if attempt_ssh "${PROXY_IP}"; then
        echo "Connection successful to proxy server."
        break
    else
        echo "SSH not ready in proxy server. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo "Max retries reached. SSH connection failed in proxy server."
        exit 1
    fi
done

# Step 0: Upload the FastAPI proxy app file
echo "Uploading the FastAPI proxy app file..."
scp -i "$KEY_PATH" "$APP_FILE" $REMOTE_USER@"${PROXY_IP}":~/

# Step 1: Install Python dependencies and set up the FastAPI proxy server
echo "Installing Python dependencies and setting up the FastAPI proxy server..."
ssh -i "$KEY_PATH" -o "StrictHostKeyChecking=no" $REMOTE_USER@"$PROXY_IP" <<EOF
    # Update system and install dependencies
    sudo apt update
    sudo apt install python3-pip python3-venv -y

    # Set up a virtual environment
    python3 -m venv ~/fastapi_env
    source ~/fastapi_env/bin/activate

    # Install dependencies inside the virtual environment
    pip install fastapi uvicorn httpx

    # Prepare the application directory
    mkdir -p ~/fastapi_proxy
    mv ~/proxy_server_fastapi_route.py ~/fastapi_proxy/

    # Create a systemd service file for FastAPI
    echo "[Unit]
    Description=FastAPI Proxy Service
    After=network.target

    [Service]
    User=${REMOTE_USER}
    WorkingDirectory=/home/${REMOTE_USER}/fastapi_proxy
    ExecStart=/home/${REMOTE_USER}/fastapi_env/bin/uvicorn proxy_server_fastapi_route:app --host 0.0.0.0 --port 8000
    Environment=MANAGER_IP=${MANAGER_IP}
    Environment=WORKER_IPS=${WORKER_IPS}
    Restart=always
    StandardOutput=file:/home/${REMOTE_USER}/fastapi_proxy/fastapi.log
    StandardError=file:/home/${REMOTE_USER}/fastapi_proxy/fastapi_error.log

    [Install]
    WantedBy=multi-user.target" | sudo tee /etc/systemd/system/fastapi_proxy.service > /dev/null

    # Reload systemd and start the FastAPI service
    sudo systemctl daemon-reload
    sudo systemctl enable fastapi_proxy
    sudo systemctl restart fastapi_proxy

    echo "FastAPI proxy service has been successfully deployed and started."
EOF

# Final message
echo "FastAPI proxy server deployed successfully on $PROXY_IP."
