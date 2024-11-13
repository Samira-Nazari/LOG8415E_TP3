# proxy_server.py
import sys
import random
import subprocess


if len(sys.argv) < 5:
    print("Usage: proxy_server.py <manager_ip> <worker_ip1> <worker_ip2> <query> <query_type>")
    sys.exit(1)

# Parse IPs from command-line arguments
MYSQL_MANAGER = sys.argv[1]
MYSQL_NODES = [sys.argv[2], sys.argv[3]]

def direct_hit(query):
    print(f"Executing write query on manager node: {MYSQL_MANAGER}")
    subprocess.run(["mysql", "-h", MYSQL_MANAGER, "-u", "root", "-p123456", "-e", query])
    print(f"End of write query")

def random_node(query):
    selected_node = random.choice(MYSQL_NODES)
    print(f"Executing read (RANDOM) query on node: {selected_node}")
    subprocess.run(["mysql", "-h", selected_node, "-u", "root", "-p123456", "-e", query])
    print(f"End of read query")

def customized_node(query):
    response_times = {node: subprocess.getoutput(f"ping -c 1 {node}").split('time=')[1].split(' ')[0] for node in MYSQL_NODES}
    fastest_node = min(response_times, key=response_times.get)
    print(f"Executing read (CUSTOMIZED) query on node: {fastest_node}")
    subprocess.run(["mysql", "-h", fastest_node, "-u", "root", "-p123456", "-e", query])
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
