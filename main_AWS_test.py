from create_AWS_security_groups import create_security_group
from create_AWS_security_groups_gatekeeper import create_gatekeeper_security_group
from create_AWS_security_groups_trustedhost import create_trusted_host_security_group
from create_AWS_EC2_Instances import create_ec2_instance
from terminate import terminate_instances
import json
import subprocess

KEY_PATH="TP3_pem_3.pem" 

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
        #print(f"Error during FastAPI proxy setup for {proxy_ip}: {e.stderr}")
        print(f"Error during proxy setup for {proxy_ip}: {e}")

def setup_gatekeeper(gatekeeper_ip, trusted_host_ip):
    git_bash_path = "C:/Program Files/Git/bin/bash.exe"  # Adjust if Git Bash is installed elsewhere
    try:
        print(f"Starting to set up FastAPI gatekeeper for {gatekeeper_ip}")
        # Pass the three parameters to the bash script
        subprocess.run([git_bash_path, "./setup_fastapi_gatekeeper.sh", gatekeeper_ip, trusted_host_ip], check=True)
        print(f"FastAPI gatekeeper setup completed for {gatekeeper_ip}")
    except subprocess.CalledProcessError as e:
        #print(f"Error during FastAPI gatekeeper setup for {gatekeeper_ip}: {e.stderr}")
        print(f"Error during gatekeeper setup for {gatekeeper_ip}: {e}")

def setup_trusted_host(trusted_host_ip, proxy_ip):
    git_bash_path = "C:/Program Files/Git/bin/bash.exe"  # Adjust if Git Bash is installed elsewhere
    try:
        print(f"Starting to set up FastAPI trusted_host for {trusted_host_ip}")
        # Pass the three parameters to the bash script
        subprocess.run([git_bash_path, "./setup_fastapi_trusted_host.sh", trusted_host_ip, proxy_ip], check=True)
        print(f"FastAPI trusted_host setup completed for {trusted_host_ip}")
    except subprocess.CalledProcessError as e:
        #print(f"Error during FastAPI trusted_host setup for {trusted_host_ip}: {e.stderr}")
        print(f"Error during trusted_host setup for {trusted_host_ip}: {e}")


def setup_proxy_server(proxy_ip, manager_ip, worker_ips):
    # Transfer the PEM file to the Proxy instance
    print(f"Starting setting up proxy server in IP: {proxy_ip}")
    
    # Copy PEM file to proxy server
    subprocess.run([
        "scp", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no",
        KEY_PATH, f"ubuntu@{proxy_ip}:/home/ubuntu/.ssh/TP3_pem_3.pem"
    ])
    print(f"PEM file copied to {proxy_ip}:/home/ubuntu/.ssh/TP3_pem_3.pem")

    # SSH into the proxy instance and set correct permissions for the PEM file
    ssh_command = [
        "ssh", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no",
        f"ubuntu@{proxy_ip}", "chmod 600 /home/ubuntu/.ssh/TP3_pem_3.pem"
    ]
    subprocess.run(ssh_command)
    print(f"Permissions set for PEM file on {proxy_ip}")

    # Transfer proxy_server.py to the Proxy instance
    subprocess.run([
        "scp", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no",
        "proxy_server.py", f"ubuntu@{proxy_ip}:/home/ubuntu/proxy_server.py"
    ])

    # Run proxy_server.py with the IPs as arguments
    command = f"python3 /home/ubuntu/proxy_server.py {manager_ip} {worker_ips[0]} {worker_ips[1]}"
    subprocess.run([
        "ssh", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no",
        f"ubuntu@{proxy_ip}", command
    ])
    print(f"End of setting up proxy server in IP: {proxy_ip}")



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

    # Creating a security group for gate keeper
    print("Creating a security group for gatekeeper...")
    #security_group_id_gatekeeper = create_gatekeeper_security_group('Gatekeeper_Security_Group', 'Security group for the Gatekeeper instance', vpc_id)
    security_group_id_gatekeeper = 'sg-0e85cae14839a77c4'
    print(f"Created Security Group for gatekeeper ID: {security_group_id_gatekeeper}")

    '''
    # Replace 'vpc_id' and 'gatekeeper_security_group_id' with actual IDs
    vpc_id = "vpc-0abcd1234efgh5678"  # Replace with your VPC ID
    gatekeeper_security_group_id = "sg-0123456789abcdef0"  # Replace with Gatekeeper Security Group ID
    trusted_host_sg_id = create_trusted_host_security_group(
    'Trusted_Host_Security_Group', 
    'Security group for the Trusted Host node', 
    vpc_id, 
    gatekeeper_security_group_id)
    print(f"Created Security Group ID: {trusted_host_sg_id}")
    '''

    # Creating a security group for trusted host
    #security_group_id_trustedhost = create_trusted_host_security_group('Trusted_Host_Security_Group', 'Security group for the Trusted Host node', vpc_id, security_group_id_gatekeeper)
    security_group_id_trustedhost = 'sg-0af8854f032e26287'
    print(f"Created Security Group ID for trustedhost: {security_group_id_trustedhost}")
  

    # Create 3 t2.micros instances
    print("Creating 3 t2.micro instance...")
    #instances = create_ec2_instance('t2.micro', 3, key_name, security_group_id,'InstanceTest', 'MySQLNodeinstance')
    
    # Create 1 t2.large instance for Proxy
    print("Creating 1 t2.large instance for Proxy...")
    #proxy_instance = create_ec2_instance('t2.large', 1, key_name, security_group_id,'Role', 'Proxy')

    # Create 1 t2.large instance for gatekeeper
    print("Creating 1 t2.large instance for gatekeeper...")
    #gatekeeper_instance = create_ec2_instance('t2.large', 1, key_name, security_group_id_gatekeeper,'Role', 'gatekeeper')

    # Create 1 t2.large instance for trusted_host
    print("Creating 1 t2.large instance for trusted_host...")
    #trusted_instance = create_ec2_instance('t2.large', 1, key_name, security_group_id_trustedhost,'Role', 'trsusted_host')

    # Assign roles to instances
    '''
    manager_ip = instances[0].public_ip_address
    worker_ips = [instances[1].public_ip_address, instances[2].public_ip_address]
    proxy_ip = proxy_instance[0].public_ip_address
    gatekeeper_ip = gatekeeper_instance[0].public_ip_address
    trusted_host_ip = trusted_instance[0].public_ip_address
    '''
    manager_ip = '54.208.197.5'
    worker_ips = ['34.239.111.89', '34.238.246.133']
    proxy_ip = '98.81.165.95'
    gatekeeper_ip = '3.84.240.207'
    trusted_host_ip = '18.212.232.217'


    print(f"Manager IP: {manager_ip}")
    print(f"Worker IPs: {worker_ips}")
    print(f"Proxy IP: {proxy_ip}")
    print(f"Gatekeeper IP: {gatekeeper_ip}")
    print(f"Trusted host IP: {trusted_host_ip}")

    # Concating all instances
    #all_instances = instances + proxy_instance + gatekeeper_instance + trusted_instance
    #instance_ids = [instance.id for instance in all_instances]

    # Installing in Instances
    '''
    for instance in instances:
        
        public_ip = instance.public_ip_address
        if public_ip:
            #install_to_instance(public_ip)
        else:
            print(f"No public IP found for instance {instance.id}")
    '''
    #install_to_instance(manager_ip)

    # Deply worker_fastapi.py on the worker instances
    #setup_worker(worker_ips[0])
    #setup_worker(worker_ips[1])
    #setup_manager(manager_ip)
    
    # Deploy proxy_server_fastapi_route.py on the the proxy instance
    #setup_proxy(proxy_ip, manager_ip, worker_ips)

    # Deploy gatekeeper and trusted_host on the related instances
    setup_gatekeeper(gatekeeper_ip, trusted_host_ip)
    #setup_trusted_host(trusted_host_ip, proxy_ip)

    print(f"Manager IP: {manager_ip}")
    print(f"Worker IPs: {worker_ips}")
    print(f"Proxy IP: {proxy_ip}")
    print(f"Gatekeeper IP: {gatekeeper_ip}")
    print(f"Trusted host IP: {trusted_host_ip}")


    #Terminate all_instances (if needed)
    if instance_ids:  # Check if instance_ids list is not empty
        terminate_option = input("Do you want to terminate the all instances? (yes/no): ")
        if terminate_option.lower() == 'yes':
            terminate_instances(instance_ids)
        else:
            print("No instances to terminate.")

if __name__ == "__main__":
    main()