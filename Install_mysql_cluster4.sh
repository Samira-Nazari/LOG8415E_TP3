#!/bin/bash
# slave correct, slave has problem
set -e  # Exit on any error.

# Variables
KEY_PATH="TP3_pem_3.pem"
REMOTE_USER="ubuntu"
MAX_RETRIES=5
RETRY_DELAY=30
MASTER_IP=$1      # First argument for Master IP
WORKER1_IP=$2    # Second argument for Worker 1 IP
WORKER2_IP=$3    # Third argument for Worker 2 IP

MYSQL_ROOT_PASSWORD="123456"
REPLICATION_USER="repl_user"
REPLICATION_PASSWORD="repl_pass"

MASTER_LOG_FILE=""
MASTER_LOG_POS=""

# Retry loop to wait for SSH availability
function attempt_ssh() {
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_USER@$1 "echo 'Connected'"
}

function wait_for_ssh() {
    local INSTANCE_IP=$1
    for ((i=1; i<=MAX_RETRIES; i++)); do
        echo "Attempting to connect to ${INSTANCE_IP} (attempt $i of $MAX_RETRIES)..."
        if attempt_ssh "${INSTANCE_IP}"; then
            echo "Connection successful."
            return 0
        else
            echo "SSH not ready. Retrying in $RETRY_DELAY seconds..."
            sleep $RETRY_DELAY
        fi
        if [ $i -eq $MAX_RETRIES ]; then
            echo "Max retries reached. SSH connection to ${INSTANCE_IP} failed."
            exit 1
        fi
    done
}

function install_mysql() {
    local INSTANCE_IP=$1
    wait_for_ssh "$INSTANCE_IP"
    echo "Connecting to instance ${INSTANCE_IP} to install MySQL..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << REMOTE_EOF
        sudo apt update
        sudo apt-get install mysql-server -y

        # Update bind address for remote access
        sudo sed -i 's/bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
        sudo systemctl restart mysql

        # Secure MySQL and setup users
        sudo mysql -u root <<MYSQL_SECURE
        DELETE FROM mysql.user WHERE User='';
        DELETE FROM mysql.user WHERE User='root' AND Host!='localhost';
        DROP DATABASE IF EXISTS test;
        DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
        FLUSH PRIVILEGES;

        CREATE USER 'root'@'%' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}';
        GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

        CREATE USER 'samnaz'@'%' IDENTIFIED BY '1234560';
        GRANT ALL PRIVILEGES ON *.* TO 'samnaz'@'%' WITH GRANT OPTION;

        FLUSH PRIVILEGES;
MYSQL_SECURE


    # Install the Sakila database
    echo "Downloading and installing the Sakila database..."
    wget https://downloads.mysql.com/docs/sakila-db.tar.gz -P /tmp
    tar -xzf /tmp/sakila-db.tar.gz -C /tmp

sudo mysql -u root -p'123456' <<MYSQL_SAKILA
SOURCE /tmp/sakila-db/sakila-schema.sql;
SOURCE /tmp/sakila-db/sakila-data.sql;
MYSQL_SAKILA

    echo "MySQL and Sakila database installation completed."
REMOTE_EOF

    if [ $? -eq 0 ]; then
        echo "MySQL installation completed on ${INSTANCE_IP}."
    else
        echo "MySQL installation failed on ${INSTANCE_IP}."
        exit 1
    fi
}

function configure_master() {
    wait_for_ssh "$MASTER_IP"
    echo "Configuring Master instance at ${MASTER_IP}..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -T $REMOTE_USER@$MASTER_IP << EOF
        # Enable binary logging and set server ID
        sudo sed -i '/\[mysqld\]/a server-id=1\nlog_bin=mysql-bin' /etc/mysql/mysql.conf.d/mysqld.cnf
        sudo systemctl restart mysql

               # Create replication user and grant privileges
        sudo mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "
            CREATE USER '${REPLICATION_USER}'@'%' IDENTIFIED WITH 'mysql_native_password' BY '${REPLICATION_PASSWORD}';
            GRANT REPLICATION SLAVE ON *.* TO '${REPLICATION_USER}'@'%';
            FLUSH PRIVILEGES;
        "

        # Save the master status to a temporary file
        sudo mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SHOW MASTER STATUS\G" > /tmp/master_status.txt
EOF

 # Retrieve the master status file
    scp -i "$KEY_PATH" $REMOTE_USER@${MASTER_IP}:/tmp/master_status.txt ./master_status.txt


 # Parse the master status for log file and position
    MASTER_LOG_FILE=$(grep "File:" master_status.txt | awk '{print $2}')
    MASTER_LOG_POS=$(grep "Position:" master_status.txt | awk '{print $2}')

    # Validate the retrieved log details
    if [[ -z "$MASTER_LOG_FILE" || -z "$MASTER_LOG_POS" ]]; then
        echo "Error: Could not retrieve master log file and position."
        exit 1
    fi

    echo "Master Log File: ${MASTER_LOG_FILE}, Position: ${MASTER_LOG_POS}"
        # # MySQL commands to configure replication
        # sudo mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<EOF2
        # # Enable binary logging and set server ID
        # SET GLOBAL server_id = 1;
        
        # # Acquire a read lock, get master status, and then release the lock
        # FLUSH TABLES WITH READ LOCK;
        # SHOW MASTER STATUS;
        # UNLOCK TABLES;

        # DROP USER IF EXISTS '${REPLICATION_USER}'@'%';
        # CREATE USER '${REPLICATION_USER}'@'%' IDENTIFIED BY '${REPLICATION_PASSWORD}';
        # GRANT REPLICATION SLAVE ON *.* TO '${REPLICATION_USER}'@'%';
        # FLUSH PRIVILEGES;

        # SHOW GRANTS FOR '${REPLICATION_USER}'@'%';
# EOF2

#         # Shell commands to enable binary log and restart MySQL service
#         sudo sed -i '/\[mysqld\]/a server-id=1\nlog_bin=mysql-bin' /etc/mysql/mysql.conf.d/mysqld.cnf
#         sudo systemctl restart mysql

#         sudo mysql -u root -p'123456' -e "SHOW MASTER STATUS\G" > /tmp/master_status.txt

# EOF
#     # Retrieve replication details
#     scp -i "$KEY_PATH" $REMOTE_USER@${MASTER_IP}:/tmp/master_status.txt ./master_status.txt
#     MASTER_LOG_FILE=$(grep "File:" master_status.txt | awk '{print $2}')
#     MASTER_LOG_POS=$(grep "Position:" master_status.txt | awk '{print $2}')
#     echo "Master Log File: ${MASTER_LOG_FILE}, Position: ${MASTER_LOG_POS}"

#     # Return the master's log file and position
#     echo "$MASTER_LOG_FILE $MASTER_LOG_POS"
}

function configure_slave() {
    local SLAVE_IP=$1
    local SERVER_ID=$2
    local MASTER_LOG_FILE=$3
    local MASTER_LOG_POS=$4
    
    wait_for_ssh "$SLAVE_IP"
    echo "Configuring Slave instance at ${SLAVE_IP}..."

    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -T $REMOTE_USER@$SLAVE_IP <<EOF
        # Update my.cnf for slave configuration
        sudo sed -i '/\[mysqld\]/a server-id=${SERVER_ID}\nrelay-log=slave-relay-bin' /etc/mysql/mysql.conf.d/mysqld.cnf
        sudo systemctl restart mysql

        # Set up replication on the slave
        sudo mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "
            CHANGE REPLICATION SOURCE TO
                SOURCE_HOST='${MASTER_IP}',
                SOURCE_USER='${REPLICATION_USER}',
                SOURCE_PASSWORD='${REPLICATION_PASSWORD}',
                SOURCE_LOG_FILE='${MASTER_LOG_FILE}',
                SOURCE_LOG_POS=${MASTER_LOG_POS};
            START REPLICA;
        "
        # Verify replication status
        sudo mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SHOW REPLICA STATUS\G"
EOF

    echo "Slave configuration on ${SLAVE_IP} completed."
}



# function configure_slave() {
#     local SLAVE_IP=$1
#     local SERVER_ID=$2
#     local MASTER_LOG_FILE=$3
#     local MASTER_LOG_POS=$4

#     echo "Start creating Slave for IP ${SLAVE_IP}" 
#     echo "Master Log File: ${MASTER_LOG_FILE}"
#     echo "Master Log Position: ${MASTER_LOG_POS}"

#     # Wait for SSH to be ready on the slave instance
#     wait_for_ssh "$SLAVE_IP"
  
#     echo "Configuring Slave instance at ${SLAVE_IP} with server ID ${SERVER_ID}..."

#     ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no $REMOTE_USER@$SLAVE_IP << EOF

#         # Set server ID and configure slave
#         sudo mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<EOF2
#         SET GLOBAL server_id = ${SERVER_ID};
#         CHANGE MASTER TO 
#             MASTER_HOST='${MASTER_IP}',
#             MASTER_USER='${REPLICATION_USER}',
#             MASTER_PASSWORD='${REPLICATION_PASSWORD}',
#             MASTER_LOG_FILE='${MASTER_LOG_FILE}',
#             MASTER_LOG_POS=${MASTER_LOG_POS};
#         START SLAVE;
#         SHOW SLAVE STATUS\G;
#     EOF2

#         # Update configuration for replication
#         # sudo sed -i '/\[mysqld\]/a server-id=${SERVER_ID}' /etc/mysql/mysql.conf.d/mysqld.cnf

#         cat <<EOF1 > /etc/mysql/mysql.conf.d/mysqld.cnf
#         [mysqld]
#         server-id=${SERVER_ID}
#         relay-log=mysql-relay-bin
#         log-bin=mysql-bin
# EOF1
#         # Restart MySQL to apply changes
#         sudo systemctl restart mysql
# EOF
# }

# Install MySQL on all instances
install_mysql "$MASTER_IP"
install_mysql "$WORKER1_IP"
install_mysql "$WORKER2_IP"

# Configure master and slaves
configure_master
echo "Master was created"
echo "Master Log File: ${MASTER_LOG_FILE}"
echo "Master Log Position: ${MASTER_LOG_POS}"
configure_slave "$WORKER1_IP" 2 "$MASTER_LOG_FILE" "$MASTER_LOG_POS"
configure_slave "$WORKER2_IP" 3 "$MASTER_LOG_FILE" "$MASTER_LOG_POS"

echo "MySQL master-slave cluster setup completed!"
