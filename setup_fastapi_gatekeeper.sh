#!/bin/bash

# Check if sufficient arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <gatekeeper_ip> <trusted_host_ip>"
    echo "Example: $0 54.167.204.147 54.227.86.12"
    exit 1
fi

GATEKEEPER_IP=$1
TRUSTED_HOST_IP=$2
KEY_PATH="TP3_pem_3.pem"
REMOTE_USER="ubuntu"
MAX_RETRIES=5
RETRY_DELAY=30
APP_FILE="gatekeeper_fastapi.py"

# Function to attempt SSH connection
function attempt_ssh() {
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_USER@$1 "echo 'Connected'"
}

# Retry loop for SSH connection
for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Attempting to connect to Gatekeeper instance ${GATEKEEPER_IP} (attempt $i of $MAX_RETRIES)..."
    if attempt_ssh "${GATEKEEPER_IP}"; then
        echo "Connection successful to Gatekeeper."
        break
    else
        echo "SSH not ready on Gatekeeper. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo "Max retries reached. SSH connection failed on Gatekeeper."
        exit 1
    fi
done

# Step 0: Upload the Gatekeeper FastAPI app file
echo "Uploading FastAPI Gatekeeper app..."
scp -i "$KEY_PATH" "$APP_FILE" $REMOTE_USER@"${GATEKEEPER_IP}":~/ 

# Step 1: Install Python dependencies and set up FastAPI Gatekeeper
echo "Installing Python dependencies on Gatekeeper..."
ssh -i "$KEY_PATH" -o "StrictHostKeyChecking=no" $REMOTE_USER@"$GATEKEEPER_IP" <<EOF
    # Update system and install dependencies
    sudo apt update
    sudo apt install python3-pip python3-venv -y

    # Set up a virtual environment
    python3 -m venv ~/fastapi_env
    source ~/fastapi_env/bin/activate

    # Install FastAPI and dependencies
    pip install fastapi uvicorn httpx

    # Move the Gatekeeper app file
    mkdir -p ~/gatekeeper_app
    mv ~/gatekeeper_fastapi.py ~/gatekeeper_app/

    # Create a systemd service file for FastAPI
    echo "[Unit]
    Description=FastAPI Gatekeeper Service
    After=network.target

    [Service]
    User=${REMOTE_USER}
    WorkingDirectory=/home/${REMOTE_USER}/gatekeeper_app
    ExecStart=/home/${REMOTE_USER}/fastapi_env/bin/uvicorn gatekeeper_fastapi:app --host 0.0.0.0 --port 8000
    Environment=TRUSTED_HOST_IP=${TRUSTED_HOST_IP}
    Restart=always
    StandardOutput=file:/home/${REMOTE_USER}/gatekeeper_app/gatekeeper.log
    StandardError=file:/home/${REMOTE_USER}/gatekeeper_app/gatekeeper_error.log

    [Install]
    WantedBy=multi-user.target" | sudo tee /etc/systemd/system/fastapi_gatekeeper.service > /dev/null

    # Reload systemd and start FastAPI service
    sudo systemctl daemon-reload
    sudo systemctl enable fastapi_gatekeeper
    sudo systemctl restart fastapi_gatekeeper

    echo "FastAPI Gatekeeper service deployed and started."
EOF

# Final message
echo "Gatekeeper deployed successfully on ${GATEKEEPER_IP}."
