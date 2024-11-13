import boto3
import boto3.session
from botocore.exceptions import ClientError

# Initialize Boto3 EC2 resource
# The 'ec2' resource allows interaction with EC2 services in the specified AWS region.
ec2 = boto3.resource('ec2', region_name='us-east-1')

def create_ec2_instance(instance_type, count, key_name, security_group_id, KeyName, ValueName):
    """
    Creates one or more EC2 instances of the specified type.

    Parameters:
    - instance_type (str): The type of instance to launch (e.g., 't2.micro').
    - count (int): The number of instances to launch.
    - key_name (str): The name of the EC2 key pair for SSH access.
    - security_group_id (str): The security group ID for network and port access.

    Returns:
    - list: A list of created EC2 instance objects.
    """
    try:
        # Launch EC2 instances with the specified parameters.
        instances = ec2.create_instances(
            ImageId='ami-0e86e20dae9224db8',  # The Amazon Machine Image (AMI) ID to use for the instances (Ubuntu 20.04).
            InstanceType=instance_type,       # The type of instance to create (e.g., 't2.micro', 't2.large').
            KeyName=key_name,                 # Key pair name for SSH access.
            MinCount=1,                       # Minimum number of instances to launch.
            MaxCount=count,                   # Maximum number of instances to launch (based on user input).
            SecurityGroupIds=[security_group_id],  # Security group(s) to attach to the instances.
            TagSpecifications=[               # Tags to help identify and manage instances.
                {
                    'ResourceType': 'instance', 
                    # 'Tags': [{'Key': 'InstanceTest', 'Value': f'{instance_type} instance'}]  
                    #'Tags': [{'Key': 'InstanceTest', 'Value': f'{instance_type} MySQLNodeinstance'}]
                    'Tags': [{'Key': KeyName, 'Value': f'{instance_type} {ValueName}'}]  # Custom tag for instance type.
                }
            ]
        )
    except ClientError as e:
        # Handle exceptions that occur during instance creation (e.g., incorrect permissions).
        print(f"Error creating EC2 instance(s): {e}")
        return []  # Return an empty list if creation fails.
    
    # Wait for each instance to reach the 'running' state and print its public IP.
    for instance in instances:
        try:
            print(f'Waiting for instance {instance.id} to be running...')
            instance.wait_until_running()  # Wait for the instance to transition to 'running' status.
            instance.reload()  # Refresh instance attributes after it reaches 'running' state.
            print(f'MySQL Node with Instance ID: {instance.id} is now running at Public IP: {instance.public_ip_address}')
        except ClientError as e:
            # Handle exceptions that occur while waiting for instance to reach 'running' state.
            print(f"Error waiting for instance {instance.id} to be running: {e}")
    
    return instances  # Return the list of created instances.




