# proxy_server.py
import sys
import random
import subprocess

if len(sys.argv) < 5:
    print("Usage: proxy_server.py <manager_ip> <worker_ip1> <worker_ip2> <query> <query_type>")
    sys.exit(1)

MYSQL_MANAGER = sys.argv[1]
MYSQL_NODES = [sys.argv[2], sys.argv[3]]

query = sys.argv[4]
query_type = sys.argv[5]

def direct_hit(query):
    print(f"Executing write query on manager node: {MYSQL_MANAGER}")
    result = subprocess.run(
        ["/usr/bin/mysql", "-h", MYSQL_MANAGER, "-u", "root", "-p123456", "-e", query],
        capture_output=True, text=True
    )
    print("Query result:", result.stdout or result.stderr)

def random_node(query):
    selected_node = random.choice(MYSQL_NODES)
    print(f"Executing read query on random node: {selected_node}")
    result = subprocess.run(
        ["/usr/bin/mysql", "-h", selected_node, "-u", "root", "-p123456", "-e", query],
        capture_output=True, text=True
    )
    print("Query result:", result.stdout or result.stderr)

def customized_node(query):
    response_times = {
        node: subprocess.getoutput(f"ping -c 1 {node}").split('time=')[1].split(' ')[0]
        for node in MYSQL_NODES
    }
    fastest_node = min(response_times, key=response_times.get)
    print(f"Executing read query on fastest node: {fastest_node}")
    result = subprocess.run(
        ["/usr/bin/mysql", "-h", fastest_node, "-u", "root", "-p123456", "-e", query],
        capture_output=True, text=True
    )
    print("Query result:", result.stdout or result.stderr)

def route_request(query, query_type):
    print(f"Attempting to execute query: {query} with query type: {query_type}")
    if query_type == "write":
        direct_hit(query)
    elif query_type == "read_random":
        random_node(query)
    elif query_type == "read_custom":
        customized_node(query)
    else:
        print("Invalid query type")

if __name__ == "__main__":
    route_request(query, query_type)
