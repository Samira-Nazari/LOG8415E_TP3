import requests
import time
import asyncio
import aiohttp
import argparse
from datetime import datetime
import json  # Import the json module

# Number of requests to send
NUM_REQUESTS = 1000
CONCURRENT_REQUESTS = 50  # Max concurrent requests

# Log file name
LOG_FILE = "benchmark_results.txt"

# Generate read request payloads
def generate_read_requests():
    queries = [
        {"query": f"SELECT * FROM actor WHERE actor_ID = {i}"}
        for i in range(1, NUM_REQUESTS + 1)
    ]
    return queries

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
    else:  # query_type == 'write'
        queries = generate_write_requests()

    url = f"http://{gatekeeper_ip}:8000/validate_request/{strategy}"
    start_time = time.time()

    with open(LOG_FILE, "a") as file:
        for query in queries:
            try:
                response = requests.post(url, json=query)
                result = f"Response: {response.status_code} - {response.text}"
                print(result)  # Print to the shell
                file.write(result + "\n")  # Write to the log file
            except requests.exceptions.RequestException as e:
                error_message = f"Request failed: {e}"
                print(error_message)
                file.write(error_message + "\n")

        duration = time.time() - start_time
        completion_message = f"Synchronous benchmark completed in {duration:.2f} seconds."
        print(completion_message)
        file.write(completion_message + "\n")

# Asynchronous function to send a single request
async def send_request(session, url, query, semaphore, file):
    async with semaphore:  # Limit the number of concurrent requests
        try:
            async with session.post(url, json=query) as response:
                result = await response.text()

                # Convert query to a JSON string
                log_request = json.dumps(query, indent=4)
                print(log_request)
                file.write(log_request + "\n")  # Add newline for readability
                
                log_message = f"Response: {response.status} - {result}"
                print(log_message)
                file.write(log_message + "\n")
        except Exception as e:
            error_message = f"Request failed: {e}"
            print(error_message)
            file.write(error_message + "\n")

# Asynchronous benchmark using aiohttp
async def benchmark_async(gatekeeper_ip, query_type, strategy):
    if query_type == 'read':
        queries = generate_read_requests()
    else:  # query_type == 'write'
        queries = generate_write_requests()

    url = f"http://{gatekeeper_ip}:8000/validate_request/{strategy}"
    start_time = time.time()

    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)  # Limit concurrency

    with open(LOG_FILE, "a") as file:
        async with aiohttp.ClientSession() as session:
            tasks = [send_request(session, url, query, semaphore, file) for query in queries]
            await asyncio.gather(*tasks)

        duration = time.time() - start_time
        completion_message = f"Asynchronous benchmark completed in {duration:.2f} seconds."
        print(completion_message)
        file.write(completion_message + "\n")

# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmarking Script for Gatekeeper")
    parser.add_argument("--gatekeeper", type=str, required=True, help="Gatekeeper IP address")
    parser.add_argument("--query_type", type=str, required=True, choices=["read", "write"], help="Query type")
    parser.add_argument("--strategy", type=str, required=True, choices=["direct", "random", "customized"], help="Routing strategy")
    args = parser.parse_args()

    gatekeeper_ip = args.gatekeeper
    query_type = args.query_type
    strategy = args.strategy

    with open(LOG_FILE, "a") as file:
        # Write start message for synchronous benchmark
        '''
        sync_message = "Starting synchronous benchmark..."
        print(sync_message)
        file.write(sync_message + "\n")
        benchmark_sync(gatekeeper_ip, query_type, strategy)
        '''  

        # Pause before asynchronous benchmark
        pause_message = "\nPausing for 5 seconds before starting asynchronous benchmark..."
        print(pause_message)
        file.write(pause_message + "\n")
        time.sleep(5)

        # Write start message for asynchronous benchmark
        async_message = "\nStarting asynchronous benchmark..."
        print(async_message)
        file.write(async_message + "\n")

        asyncio.run(benchmark_async(gatekeeper_ip, query_type, strategy))
