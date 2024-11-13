#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Variables
KEY_PATH="TP3_pem_3.pem"             
REMOTE_USER="ubuntu"                
MAX_RETRIES=5                       
RETRY_DELAY=30                      

# Check if all IP parts are provided
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
  echo "Usage: ./install_mysql.sh <part1> <part2> <part3> <part4>"
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

# Connect to the instance and install MySQL
echo "Connecting to the instance and installing MySQL..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no $REMOTE_USER@${INSTANCE_IP} << EOF
    sudo apt update
    sudo apt-get install mysql-server -y

    sudo sed -i 's/bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
    sudo systemctl restart mysql

    sudo mysql -u root <<EOF2
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host!='localhost';
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF2

    sudo mysql -u root <<EOF3
CREATE USER 'root'@'%' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

# Create 'samnaz' user and grant privileges
CREATE USER 'samnaz'@'%' IDENTIFIED BY '1234560';
GRANT ALL PRIVILEGES ON *.* TO 'samnaz'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EXIT
EOF3
EXIT
EOF3

    # Install the Sakila database
    echo "Downloading and installing the Sakila database..."
    wget https://downloads.mysql.com/docs/sakila-db.tar.gz -P /tmp
    tar -xzf /tmp/sakila-db.tar.gz -C /tmp

    sudo mysql -u root -p'123456' <<EOF4
SOURCE /tmp/sakila-db/sakila-schema.sql;
SOURCE /tmp/sakila-db/sakila-data.sql;
EOF4

    echo "MySQL and Sakila database installation completed."

    # Install sysbench for benchmarking
    echo "Installing sysbench for benchmarking..."
    sudo apt-get install sysbench -y

    # Prepare the Sakila database for sysbench testing
    echo "Preparing sysbench benchmark..."
    sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-db=sakila --mysql-user=root --mysql-password=123456 prepare

    # Run sysbench benchmark on Sakila database
    echo "Running sysbench benchmark..."
    sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-db=sakila --mysql-user=root --mysql-password=123456 run

EOF

# Verify Sakila database installation
echo "Verifying Sakila database installation..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no $REMOTE_USER@${INSTANCE_IP} << EOF
    # Connect to MySQL and verify Sakila database installation
    sudo mysql -u root -p'123456' <<EOF5
USE sakila;
SHOW FULL TABLES;
EOF5
EOF

echo "MySQL with Sakila database has been successfully installed, configured, and benchmarked on ${INSTANCE_IP}."
