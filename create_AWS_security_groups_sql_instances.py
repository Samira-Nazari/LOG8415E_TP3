import boto3
from botocore.exceptions import ClientError
# Initialize EC2 client
ec2_client = boto3.client('ec2', region_name='us-east-1')

def create_sql_instances_security_group(group_name, description, vpc_id):
    """
    Creates a security group and sets up inbound/outbound rules.
    
    Parameters:
        group_name (str): The name of the security group.
        description (str): Description of the security group.
        vpc_id (str): The VPC ID where the security group will be created.
    
    Returns:
        str: The security group ID.
    """
    try:
        # Create the security group
        response = ec2_client.create_security_group(
            GroupName=group_name,
            Description=description,
            VpcId=vpc_id
        )
        security_group_id = response['GroupId']
        print(f'Security Group {group_name} created with ID: {security_group_id}')

        # Add inbound rules (SSH, HTTP, HTTPS)
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,  # SSH
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs 
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,  # HTTP
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,  # HTTPS
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs    
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,  # FastAPI
                    'ToPort': 8000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 3306,  # Replication.
                    'ToPort': 3306,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs
                }
            ]
        )
        print(f"Ingress rules added to security group {group_name}.")

        return security_group_id

    except ClientError as e:
        print(f"Error creating security group: {e}")
        return None