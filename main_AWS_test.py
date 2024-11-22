from create_AWS_security_groups import create_security_group
from create_AWS_EC2_Instances import create_ec2_instance
from terminate import terminate_instances
import json
import subprocess

def install_to_instance(ip_address):
    ip_parts = ip_address.split('.')
    git_bash_path = "C:/Program Files/Git/bin/bash.exe"
    try:
        print(f"Starting Installing Mysql, Sakila, Sysbench for {ip_address}")
        subprocess.run([git_bash_path, "./Install_mysql_sakila_sysbench.sh", *ip_parts], check=True)
        print(f"Installed Mysql, Sakila, Sysbench correctly for {ip_address}")
    except subprocess.CalledProcessError as e:
        print(f"Error during Installing MMysql, Sakila, Sysbench for {ip_address}: {e.stderr}")

def setup_worker(ip_address):
    ip_parts = ip_address.split('.')
    git_bash_path = "C:/Program Files/Git/bin/bash.exe"
    try:
        print(f"Starting Installing fastapi worker for {ip_address}")
        subprocess.run([git_bash_path, "./setup_fastapi_worker.sh", *ip_parts], check=True)
        print(f"Installed fastapi worker correctly for {ip_address}")
    except subprocess.CalledProcessError as e:
        print(f"Error during Installing fastapi worker for {ip_address}: {e.stderr}")

def setup_manager(ip_address):
    ip_parts = ip_address.split('.')
    git_bash_path = "C:/Program Files/Git/bin/bash.exe"
    try:
        print(f"Starting Installing fastapi manager for {ip_address}")
        subprocess.run([git_bash_path, "./setup_fastapi_manager.sh", *ip_parts], check=True)
        print(f"Installed fastapi manager correctly for {ip_address}")
    except subprocess.CalledProcessError as e:
        print(f"Error during Installing fastapi manager for {ip_address}: {e.stderr}")


def setup_proxy(proxy_ip, manager_ip, worker_ips):
    git_bash_path = "C:/Program Files/Git/bin/bash.exe"  # Adjust if Git Bash is installed elsewhere
    # Convert the list of worker IPs to a comma-separated string
    worker_ips_str = ",".join(worker_ips)
    try:
        print(f"Starting to set up FastAPI proxy for {proxy_ip}")
        # Pass the three parameters to the bash script
        subprocess.run([git_bash_path, "./setup_fastapi_proxy.sh", proxy_ip, manager_ip, worker_ips_str], check=True)
        print(f"FastAPI proxy setup completed for {proxy_ip}")
    except subprocess.CalledProcessError as e:
        print(f"Error during FastAPI proxy setup for {proxy_ip}: {e.stderr}")
    

def setup_proxy_server(proxy_ip, manager_ip, worker_ips):
    # Transfer the proxy_server.py to the Proxy instance
    print(f"Starting setting up proxy server in IP: {proxy_ip}")
    subprocess.run([
        "scp", "-i", "TP3_pem_3.pem", "-o", "StrictHostKeyChecking=no",
        "proxy_server8.py", f"ubuntu@{proxy_ip}:/home/ubuntu/proxy_server8.py"
    ])

    # Run proxy_server.py with the IPs as arguments
    command = f"python3 /home/ubuntu/proxy_server8.py {manager_ip} {worker_ips[0]} {worker_ips[1]}"
    subprocess.run([
        "ssh", "-i", "TP3_pem_3.pem", "-o", "StrictHostKeyChecking=no",
        f"ubuntu@{proxy_ip}", command
    ])
    print(f"End of setting up proxy server in IP: {proxy_ip}")


'''
def setup_proxy_server(proxy_ip, manager_ip, worker_ips):
    # Transfer the proxy_server.py to the Proxy instance
    print(f"Setting up proxy server on IP: {proxy_ip}")
    subprocess.run([
        "scp", "-i", "TP3_pem_3.pem", "-o", "StrictHostKeyChecking=no",
        "proxy_server.py", f"ubuntu@{proxy_ip}:/home/ubuntu/proxy_server.py"
    ])
    print(f"Proxy server setup completed on IP: {proxy_ip}")
'''

def main():
    # Load the JSON file
    with open('AWS_creds.json', 'r') as file:
        creds = json.load(file)

    key_name = creds['key_name']
    vpc_id = creds['vpc_id']
    subnets = creds['subnets']

    print("Creating a security group...")
    #security_group_id = create_security_group('TP3_security_3', 'Security group for EC2 instances', vpc_id)
    security_group_id = 'sg-0f0a0ae8d68301cac'


    if not security_group_id:
        print("Failed to create security group. Exiting.")
        return

    manager_ip  = '3.94.114.40'
    worker_ips  = ['18.212.64.238', '3.87.182.93']
    proxy_ip = '98.84.98.234'
    

   
    print(f"Manager IP: {manager_ip}")
    print(f"Worker IPs: {worker_ips}")
    print(f"Proxy IP: {proxy_ip}")

    # Deploy proxy_server.py on the Proxy instance with the correct IP addresses
    #setup_proxy_server(proxy_ip, manager_ip, worker_ips)

    # Deply worker_fastapi.py on the worker instances
    #setup_worker(worker_ips[1])

    # Deploy proxy_server_fastapi_route.py on the the proxy instance
    #setup_proxy(proxy_ip, manager_ip, worker_ips)

    # Deply manager_fastapi.py on the worker instances
    setup_manager(manager_ip)


    print(f"Manager IP: {manager_ip}")
    print(f"Worker IPs: {worker_ips}")
    print(f"Proxy IP: {proxy_ip}")

    #Terminate all_instances (if needed)
    if instance_ids:  # Check if instance_ids list is not empty
        terminate_option = input("Do you want to terminate the all instances? (yes/no): ")
        if terminate_option.lower() == 'yes':
            terminate_instances(instance_ids)
        else:
            print("No instances to terminate.")

if __name__ == "__main__":
    main()