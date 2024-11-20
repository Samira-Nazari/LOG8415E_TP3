#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Variables
KEY_PATH="TP3_pem_3.pem"             
REMOTE_USER="ubuntu"                
MAX_RETRIES=5                       
RETRY_DELAY=30                      
APP_FILE="worker_fastapi.py"  # Name of the FastAPI worker app file

# Check if all IP parts are provided
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
  echo "Usage: ./setup_fastapi_worker.sh <part1> <part2> <part3> <part4>"
  exit 1
fi

INSTANCE_IP="${1}.${2}.${3}.${4}"

function attempt_ssh() {
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_USER@$1 "echo 'Connected'"
}

# Retry loop to wait for SSH availability
for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Attempting to connect to ${INSTANCE_IP} (attempt $i of $MAX_RETRIES)..."
    if attempt_ssh "${INSTANCE_IP}"; then
        echo "Connection successful."
        break
    else
        echo "SSH not ready. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo "Max retries reached. SSH connection failed."
        exit 1
    fi
done

# Upload the FastAPI worker app file
echo "Uploading the FastAPI worker app file..."
scp -i "$KEY_PATH" $APP_FILE $REMOTE_USER@${INSTANCE_IP}:~/

# Connect to the instance and install FastAPI
echo "Connecting to the instance and installing FastAPI..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no $REMOTE_USER@${INSTANCE_IP} << EOF
    # Update system and install dependencies
    sudo apt update
    sudo apt install python3-pip python3-venv -y

    # Set up a virtual environment
    python3 -m venv fastapi_env
    source fastapi_env/bin/activate

    # Install required Python packages
    pip install fastapi uvicorn mysql-connector-python

    # Move the FastAPI app file to a working directory
    mkdir -p ~/fastapi_worker
    mv ~/worker_fastapi.py ~/fastapi_worker/

    # Create a systemd service file for FastAPI
    echo "[Unit]
    Description=FastAPI Worker Service
    After=network.target

    [Service]
    User=${REMOTE_USER}
    WorkingDirectory=/home/${REMOTE_USER}/fastapi_worker
    ExecStart=/home/${REMOTE_USER}/fastapi_env/bin/uvicorn worker_fastapi:app --host 0.0.0.0 --port 8000
    Restart=always

    [Install]
    WantedBy=multi-user.target" | sudo tee /etc/systemd/system/fastapi_worker.service

    # Reload systemd and start the FastAPI service
    sudo systemctl daemon-reload
    sudo systemctl enable fastapi_worker
    sudo systemctl start fastapi_worker

    echo "FastAPI worker service has been successfully deployed and started."
EOF

echo "FastAPI worker setup completed on ${INSTANCE_IP}."
