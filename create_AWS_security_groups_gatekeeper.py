import boto3
from botocore.exceptions import ClientError

# Initialize EC2 client
ec2_client = boto3.client('ec2', region_name='us-east-1')

def create_gatekeeper_security_group(group_name, description, vpc_id):
    """
    Creates a security group for the Gatekeeper with secure settings.
    
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

        # Add inbound rules (SSH, HTTP, Application Port)
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,  # SSH
                    'ToPort': 22,
                    #'IpRanges': [{'CidrIp': '70.53.177.126/32'}]  # Replace with your IP
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs 
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,  # HTTP
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allow HTTP from all IPs
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,  # HTTPS
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs    
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,  # FastAPI Application Port
                    'ToPort': 8000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allow public access to Gatekeeper
                },
                {   
                    'IpProtocol': 'icmp', 
                    'FromPort': -1, 
                    'ToPort': -1, 
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }   
            ]
        )
        print(f"Ingress rules added to security group {group_name}.")
        
        
        # Add outbound rules (Allow all outbound traffic for internal communication)
        ec2_client.authorize_security_group_egress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'icmp',  # ICMP protocol
                    'FromPort': -1,        # -1 indicates all ICMP types
                    'ToPort': -1,          # -1 indicates all ICMP codes
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allow ICMP from all IPs (for ping)
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,  # SSH
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs 
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,  # FastAPI Application Port
                    'ToPort': 8000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allow public access to Gatekeeper
                }
            ]
        )
        print(f"Egress rules added to security group {group_name}.")

        # Add inbound rules (Allow access from Gatekeeper)
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,  # FastAPI Application Port
                    'ToPort': 8000,
                    #'UserIdGroupPairs': [{'GroupId': trustedhost_security_group_id}]
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,  # SSH
                    'ToPort': 22,
                    #'IpRanges': [{'CidrIp': '70.53.177.126/32'}]  # Replace 'YOUR_IP/32' with your IP
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open to all IPs 
                },
            ]
        )
        print(f"Ingress rules added to security group {group_name}.")
        
        return security_group_id

    except ClientError as e:
        print(f"Error creating security group: {e}")
        return None


