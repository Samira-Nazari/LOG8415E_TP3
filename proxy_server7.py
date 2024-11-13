import subprocess
import random
import sys

if len(sys.argv) < 5:
    print("Usage: proxy_server.py <manager_ip> <worker_ip1> <worker_ip2> <query> <query_type>")
    sys.exit(1)

# Parse IPs from command-line arguments
MYSQL_MANAGER = sys.argv[1]
MYSQL_NODES = [sys.argv[2], sys.argv[3]]
MYSQL_USER = 'samnaz'  # Updated user
MYSQL_PASSWORD = '1234560'  # Updated password
MYSQL_CLIENT_PATH = '/usr/bin/mysql'  # Full path to MySQL client
DATABASE_NAME = 'sakila'  # Database name

# SSH command to execute MySQL query remotely
def execute_query_remotely(node_ip, query):
    ssh_command = [
        "ssh", "-i", "TP3_pem_3.pem", "-o", "StrictHostKeyChecking=no",
        f"ubuntu@{node_ip}", f"/usr/bin/mysql -u {MYSQL_USER} -p{MYSQL_PASSWORD} -e \"{query}\" {DATABASE_NAME}"
    ]
    print(f"Executing command on {node_ip}: {' '.join(ssh_command)}")
    result = subprocess.run(ssh_command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing query on {node_ip}: {result.stderr}")
    else:
        print(f"Query result from {node_ip}: {result.stdout}")

def direct_hit(query):
    print(f"Executing write query on manager node: {MYSQL_MANAGER}")
    result = subprocess.run([MYSQL_CLIENT_PATH, "-h", MYSQL_MANAGER, "-u", MYSQL_USER, "-p" + MYSQL_PASSWORD, DATABASE_NAME, "-e", query])
    if result.returncode != 0:
        print(f"Error executing query on manager: {MYSQL_MANAGER}")
    else:
        print("End of write query")

def random_node(query):
    selected_node = random.choice(MYSQL_NODES)
    print(f"Executing read (RANDOM) query on node: {selected_node}")
    execute_query_remotely(selected_node, query)

def customized_node(query):
    response_times = {node: subprocess.getoutput(f"ping -c 1 {node}").split('time=')[1].split(' ')[0] for node in MYSQL_NODES}
    fastest_node = min(response_times, key=response_times.get)
    print(f"Executing read (CUSTOMIZED) query on node: {fastest_node}")
    execute_query_remotely(fastest_node, query)

def route_request(query, query_type):
    print(f"Trying to execute the {query} with {query_type}")
    if query_type == "write":
        direct_hit(query)
    elif query_type == "read_random":
        random_node(query)
    elif query_type == "read_custom":
        customized_node(query)

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: proxy_server.py <manager_ip> <worker_ip1> <worker_ip2> <query> <query_type>")
        sys.exit(1)

    # Parse IPs and query arguments correctly
    MYSQL_MANAGER = sys.argv[1]
    MYSQL_NODES = [sys.argv[2], sys.argv[3]]
    query = sys.argv[4]
    query_type = sys.argv[5]

    print(f"Attempting to execute query: {query} with query type: {query_type}")
    route_request(query, query_type)
