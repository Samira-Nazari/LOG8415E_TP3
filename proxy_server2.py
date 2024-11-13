import subprocess
import random
import sys

if len(sys.argv) < 5:
    print("Usage: proxy_server.py <manager_ip> <worker_ip1> <worker_ip2> <query> <query_type>")
    sys.exit(1)

# Parse IPs from command-line arguments
MYSQL_MANAGER = sys.argv[1]
MYSQL_NODES = [sys.argv[2], sys.argv[3]]
MYSQL_USER = 'root'  # Update if you're using a different user
MYSQL_PASSWORD = '123456'

def direct_hit(query):
    print(f"Executing write query on manager node: {MYSQL_MANAGER}")
    result = subprocess.run(["mysql", "-h", MYSQL_MANAGER, "-u", MYSQL_USER, "-p" + MYSQL_PASSWORD, "-e", query])
    if result.returncode != 0:
        print(f"Error executing query on manager: {MYSQL_MANAGER}")
    else:
        print(f"End of write query")

def random_node(query):
    selected_node = random.choice(MYSQL_NODES)
    print(f"Executing read (RANDOM) query on node: {selected_node}")
    result = subprocess.run(["mysql", "-h", selected_node, "-u", MYSQL_USER, "-p" + MYSQL_PASSWORD, "-e", query])
    if result.returncode != 0:
        print(f"Error executing query on node: {selected_node}")
    else:
        print(f"End of read query")

def customized_node(query):
    response_times = {node: subprocess.getoutput(f"ping -c 1 {node}").split('time=')[1].split(' ')[0] for node in MYSQL_NODES}
    fastest_node = min(response_times, key=response_times.get)
    print(f"Executing read (CUSTOMIZED) query on node: {fastest_node}")
    result = subprocess.run(["mysql", "-h", fastest_node, "-u", MYSQL_USER, "-p" + MYSQL_PASSWORD, "-e", query])
    if result.returncode != 0:
        print(f"Error executing query on node: {fastest_node}")
    else:
        print(f"End of read query")

def route_request(query, query_type):
    print(f"Try to execute the {query} with {query_type}")
    if query_type == "write":
        direct_hit(query)
    elif query_type == "read_random":
        random_node(query)
    elif query_type == "read_custom":
        customized_node(query)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: proxy_server.py <query> <query_type>")
        sys.exit(1)

    query = sys.argv[1]
    query_type = sys.argv[2]
    route_request(query, query_type)
