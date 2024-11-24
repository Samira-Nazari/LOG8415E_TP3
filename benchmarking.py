import requests
import time
import asyncio
import aiohttp
import argparse
from datetime import datetime


# Number of requests to send
NUM_REQUESTS = 205
CONCURRENT_REQUESTS = 50  # Max concurrent requests

# Generate read request payloads
def generate_read_requests():
    queries = [
        {"query": f"SELECT * FROM actor WHERE actor_ID = {i}"}
        for i in range(1, NUM_REQUESTS + 1)
    ]
    return queries

'''
# Generate write request payloads
def generate_write_requests():
    queries = [
        {"query": f"INSERT INTO actor (first_name, last_name, last_update) VALUES (\"Sam{i}\", \"Nzr{i}\", \"2024-11-21 10:58:11\"}
        for i in range(1, NUM_REQUESTS + 1)
    ]
    return queries
'''

# Generate write request payloads
def generate_write_requests():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    queries = [
        {"query": f"INSERT INTO actor (first_name, last_name, last_update) VALUES (\"Sam{i}\", \"Nzr{i}\", \"{current_time}\")"}
        for i in range(1, NUM_REQUESTS + 1)
    ]
    return queries

# Synchronous benchmark using requests
def benchmark_sync(gatekeeper_ip, query_type, strategy):
    if query_type == 'read':
        queries = generate_read_requests()

    else: #query_type == 'write':
        queries = generate_write_requests()

    url = f"http://{gatekeeper_ip}:8000/validate_request/{strategy}"
    start_time = time.time()

    for query in queries:
        try:
            response = requests.post(url, json=query)
            print(f"Response: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

    duration = time.time() - start_time
    print(f"Synchronous benchmark completed in {duration:.2f} seconds.")

# Asynchronous function to send a single request
async def send_request(session, url, query, semaphore):
    async with semaphore:  # Limit the number of concurrent requests
        try:
            async with session.post(url, json=query) as response:
                result = await response.text()
                print(f"Response: {response.status} - {result}")
        except Exception as e:
            print(f"Request failed: {e}")

# Asynchronous benchmark using aiohttp
async def benchmark_async(gatekeeper_ip, query_type, strategy):
    if query_type == 'read':
        queries = generate_read_requests()

    else: #query_type == 'write':
        queries = generate_write_requests()

    url = f"http://{gatekeeper_ip}:8000/validate_request/{strategy}"
    start_time = time.time()

    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)  # Limit concurrency
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, url, query, semaphore) for query in queries]
        await asyncio.gather(*tasks)

    duration = time.time() - start_time
    print(f"Asynchronous benchmark completed in {duration:.2f} seconds.")

# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmarking Script for Gatekeeper")
    parser.add_argument("--gatekeeper", type=str, required=True, help="Gatekeeper IP address")
    parser.add_argument("--query_type", type=str, required=True, choices=["read", "write"], help="query type")
    parser.add_argument("--strategy", type=str, required=True, choices=["direct", "random", "customized"], help="Routing strategy")
    args = parser.parse_args()

    gatekeeper_ip = args.gatekeeper
    query_type = args.query_type
    strategy = args.strategy

    print("Starting synchronous benchmark...")
    benchmark_sync(gatekeeper_ip, query_type, strategy)

    # Pause for 10 seconds before starting the asynchronous benchmark
    print("\nPausing for 10 seconds before starting asynchronous benchmark...")
    time.sleep(10)

    print("\nStarting asynchronous benchmark...")
    asyncio.run(benchmark_async(gatekeeper_ip, query_type, strategy))
