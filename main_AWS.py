from create_AWS_security_groups import create_security_group
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
    

def setup_proxy_server(proxy_ip, manager_ip, worker_ips):
    # Transfer the proxy_server.py to the Proxy instance
    print(f"Starting setting up proxy server in IP: {proxy_ip}")
    subprocess.run([
        "scp", "-i", "TP3_pem_3.pem", "-o", "StrictHostKeyChecking=no",
        "proxy_server7.py", f"ubuntu@{proxy_ip}:/home/ubuntu/proxy_server7.py"
    ])

    # Run proxy_server.py with the IPs as arguments
    command = f"python3 /home/ubuntu/proxy_server7.py {manager_ip} {worker_ips[0]} {worker_ips[1]}"
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

    # Create 3 t2.micros instances
    print("Creating 3 t2.micro instance...")
    instances = create_ec2_instance('t2.micro', 3, key_name, security_group_id,'InstanceTest', 'MySQLNodeinstance')
    
    # Create 1 t2.large instance
    print("Creating 1 t2.large instance for Proxy...")
    proxy_instance = create_ec2_instance('t2.large', 1, key_name, security_group_id,'Role', 'Proxy')

    # Assign roles to instances
    manager_ip = instances[0].public_ip_address
    worker_ips = [instances[1].public_ip_address, instances[2].public_ip_address]
    proxy_ip = proxy_instance[0].public_ip_address

    print(f"Manager IP: {manager_ip}")
    print(f"Worker IPs: {worker_ips}")
    print(f"Proxy IP: {proxy_ip}")

    # Concating all instances
    all_instances = instances + proxy_instance
    instance_ids = [instance.id for instance in all_instances]

    # Installing in Instances
    for instance in instances:
        # Wait until instance is running and public IP is available
        #instance.wait_until_running()
        #instance.reload()
    
        public_ip = instance.public_ip_address
        if public_ip:
            install_to_instance(public_ip)
        else:
            print(f"No public IP found for instance {instance.id}")

     # Deploy proxy_server.py on the Proxy instance with the correct IP addresses
    setup_proxy_server(proxy_ip, manager_ip, worker_ips)

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