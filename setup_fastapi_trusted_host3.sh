#!/bin/bash

# Check if sufficient arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <trusted_host_ip> <proxy_ip>"
    echo "Example: $0 54.227.86.12 54.227.86.12"
    exit 1
fi

TRUSTED_HOST_IP=$1
PROXY_IP=$2
KEY_PATH="TP3_pem_3.pem"
REMOTE_USER="ubuntu"
MAX_RETRIES=5
RETRY_DELAY=30
APP_FILE="trustedhost_fastapi.py"
PORT=8000  # FastAPI application port

# Function to attempt SSH connection
function attempt_ssh() {
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$REMOTE_USER@$1" "echo 'Connected'"
}

# Retry loop for SSH connection
for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Attempting to connect to Trusted Host instance ${TRUSTED_HOST_IP} (attempt $i of $MAX_RETRIES)..."
    if attempt_ssh "$TRUSTED_HOST_IP"; then
        echo "Connection successful to Trusted Host."
        break
    else
        echo "SSH not ready on Trusted Host. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo "Max retries reached. SSH connection failed on Trusted Host."
        exit 1
    fi
done

# Step 0: Upload the Trusted Host app file
echo "Uploading Trusted Host app..."
scp -i "$KEY_PATH" "$APP_FILE" "$REMOTE_USER@$TRUSTED_HOST_IP:~/" || { echo "Failed to upload the app file."; exit 1; }

# Step 1: Install Python dependencies and set up Trusted Host application
echo "Installing Python dependencies on Trusted Host..."
ssh -i "$KEY_PATH" -o "StrictHostKeyChecking=no" "$REMOTE_USER@$TRUSTED_HOST_IP" <<EOF
    set -e

    # Update system and install dependencies
    sudo apt update && sudo apt install python3-pip python3-venv ufw -y

    # Set up a virtual environment
    python3 -m venv ~/fastapi_env
    if [ ! -d "~/fastapi_env" ]; then
        echo "Virtual environment setup failed."
        exit 1
    fi

    source ~/fastapi_env/bin/activate
    pip install fastapi uvicorn httpx

    # Prepare application directory
    mkdir -p ~/trustedhost_fastapi
    mv ~/trustedhost_fastapi.py ~/trustedhost_fastapi/

    # Create log directory
    mkdir -p ~/trustedhost_fastapi/logs
    chmod 700 ~/trustedhost_fastapi/logs

    # Create a systemd service file for FastAPI
    echo "[Unit]
    Description=FastAPI Trusted Host Service
    After=network.target

    [Service]
    User=${REMOTE_USER}
    WorkingDirectory=/home/${REMOTE_USER}/trustedhost_fastapi
    ExecStart=/home/${REMOTE_USER}/fastapi_env/bin/uvicorn trustedhost_fastapi:app --host 0.0.0.0 --port ${PORT}
    Environment=PROXY_IP=${PROXY_IP}
    Restart=on-failure
    RestartSec=10
    StandardOutput=append:/home/${REMOTE_USER}/trustedhost_fastapi/logs/trusted_host.log
    StandardError=append:/home/${REMOTE_USER}/trustedhost_fastapi/logs/trusted_host_error.log

    [Install]
    WantedBy=multi-user.target" | sudo tee /etc/systemd/system/fastapi_trusted_host.service > /dev/null

    # Reload systemd and start FastAPI service
    sudo systemctl daemon-reload
    sudo systemctl enable fastapi_trusted_host
    sudo systemctl restart fastapi_trusted_host

    echo "FastAPI Trusted Host service deployed and started."
EOF

if [ $? -ne 0 ]; then
    echo "Failed to set up the FastAPI app or systemd service."
    exit 1
fi

# Step 2: Harden the Trusted Host (Firewall and Services)
echo "Hardening the firewall and services on the Trusted Host..."
ssh -i "$KEY_PATH" -o "StrictHostKeyChecking=no" "$REMOTE_USER@$TRUSTED_HOST_IP" <<EOF
    set -e

    # Stop and disable unnecessary services
    sudo systemctl stop apache2 || true
    sudo systemctl disable apache2 || true
    sudo systemctl stop nginx || true
    sudo systemctl disable nginx || true

    # Configure firewall rules
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22  # SSH access
    sudo ufw allow ${PORT}  # Trusted host communication port
    sudo ufw --force enable

    # Ensure all security measures are applied
    sudo apt-get update
    sudo apt-get upgrade -y
EOF

if [ $? -ne 0 ]; then
    echo "Failed to harden the Trusted Host."
    exit 1
fi

# Final message
echo "Trusted Host deployed and secured successfully on ${TRUSTED_HOST_IP}."
