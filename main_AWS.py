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

    # Create 3 t2.micros and one t2.large instance
    print("Creating 3 t2.micro instance...")
    instances = create_ec2_instance('t2.micro', 1, key_name, security_group_id)

    instance_ids = [instance.id for instance in instances]

    for instance in instances:
        # Wait until instance is running and public IP is available
        #instance.wait_until_running()
        #instance.reload()
    
        public_ip = instance.public_ip_address
        if public_ip:
            install_to_instance(public_ip)
        else:
            print(f"No public IP found for instance {instance.id}")

    #Terminate instances (if needed)
    if instance_ids:  # Check if instance_ids list is not empty
        terminate_option = input("Do you want to terminate the instances? (yes/no): ")
        if terminate_option.lower() == 'yes':
            terminate_instances(instance_ids)
        else:
            print("No instances to terminate.")

if __name__ == "__main__":
    main()