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
GATEKEEPER_IP=$3

function attempt_ssh() {
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_USER@$1 "echo 'Connected'"
}

# Retry loop to wait for SSH availability
for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Attempting to connect to TRUSTED_HOST server ${TRUSTED_HOST_IP} (attempt $i of $MAX_RETRIES)..."
    if attempt_ssh "${TRUSTED_HOST_IP}"; then
        echo "Connection successful to trustedhost server."
        break
    else
        echo "SSH not ready in trustedhost server. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo "Max retries reached. SSH connection failed in trustedhost server."
        exit 1
    fi
done

# Step 0: Upload the FastAPI trustedhost app file
echo "Uploading the FastAPI trustedhost app file..."
scp -i "$KEY_PATH" "$APP_FILE" $REMOTE_USER@"${TRUSTED_HOST_IP}":~/ 

# Step 1: Install Python dependencies and set up the FastAPI trustedhost server
echo "Installing Python dependencies and setting up the FastAPI trustedhost server..."
ssh -i "$KEY_PATH" -o "StrictHostKeyChecking=no" $REMOTE_USER@"$TRUSTED_HOST_IP" <<EOF
    # Update system and install dependencies
    sudo apt update
    sudo apt install python3-pip python3-venv -y

    # Set up a virtual environment
    python3 -m venv ~/fastapi_env
    source ~/fastapi_env/bin/activate

    # Install dependencies inside the virtual environment
    pip install fastapi uvicorn httpx

    # Prepare the application directory
    mkdir -p ~/fastapi_trustedhost
    mv ~/trustedhost_fastapi.py ~/fastapi_trustedhost/

    # Create a systemd service file for FastAPI
    echo "[Unit]
    Description=FastAPI trustedhost Service
    After=network.target

    [Service]
    User=${REMOTE_USER}
    WorkingDirectory=/home/${REMOTE_USER}/fastapi_trustedhost
    ExecStart=/home/${REMOTE_USER}/fastapi_env/bin/uvicorn trustedhost_fastapi:app --host 0.0.0.0 --port 8000
    Environment=PROXY_IP=${PROXY_IP}
    Restart=always
    StandardOutput=file:/home/${REMOTE_USER}/fastapi_trustedhost/fastapi.log
    StandardError=file:/home/${REMOTE_USER}/fastapi_trustedhost/fastapi_error.log

    [Install]
    WantedBy=multi-user.target" | sudo tee /etc/systemd/system/fastapi_trustedhost.service > /dev/null


    # Configure iptables rules for security
    echo "Configuring iptables rules..."

    # Allow SSH traffic
    sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

    # Allow loopback traffic
    sudo iptables -A INPUT -i lo -j ACCEPT
    sudo iptables -A OUTPUT -o lo -j ACCEPT

    sudo iptables -F # Flush existing rules
    sudo iptables -A INPUT -i lo -j ACCEPT # Allow loopback traffic
    sudo iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT # Allow established connections
    sudo iptables -A INPUT -p tcp -s ${PROXY_IP} --dport 8000 -j ACCEPT # Allow traffic from proxy on port 8000
    sudo iptables -A INPUT -p tcp -s ${GATEKEEPER_IP} --dport 8000 -j ACCEPT # Allow traffic from gatekeeper on port 8000
    sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT # Allow SSH traffic
    sudo iptables -P INPUT DROP # Drop all other traffic by default
    sudo iptables -P FORWARD DROP # Disable packet forwarding

    # Save iptables rules
    sudo apt install iptables-persistent -y
    sudo netfilter-persistent save
    sudo netfilter-persistent reload

    # Reload systemd and start the FastAPI service
    sudo systemctl daemon-reload
    sudo systemctl enable fastapi_trustedhost
    sudo systemctl restart fastapi_trustedhost

    echo "FastAPI trustedhost service has been successfully deployed and started with iptables security."
EOF

# Final message
echo "FastAPI trustedhost server deployed successfully on $TRUSTED_HOST_IP with enhanced iptables security."
