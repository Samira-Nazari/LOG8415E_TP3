import boto3
from botocore.exceptions import ClientError

# Initialize EC2 client
ec2_client = boto3.client('ec2', region_name='us-east-1')

def create_proxy_security_group(group_name, description, vpc_id, trustedhost_security_group_id, security_group_id_sql_instances):
    """
    Creates a security group for the proxy Host Node with limited access.
    
    Parameters:
        group_name (str): The name of the security group.
        description (str): Description of the security group.
        vpc_id (str): The VPC ID where the security group will be created.
        trustedhost_security_group_id (str): The Security Group ID of the Trustedhost.
    
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

        # Add inbound rules (Allow access from Trustedhost)
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                # Allow SSH access temporarily (optional)
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Replace with your IP range for security
                }, 
                {   
                    'IpProtocol': 'icmp', 
                    'FromPort': -1, 
                    'ToPort': -1, 
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,  # FastAPI Application Port
                    'ToPort': 8000,
                    'UserIdGroupPairs': [{'GroupId': trustedhost_security_group_id}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,  
                    'ToPort': 80,
                    'UserIdGroupPairs': [{'GroupId': trustedhost_security_group_id}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,  
                    'ToPort': 443,
                    'UserIdGroupPairs': [{'GroupId': trustedhost_security_group_id}]
                     #'IpRanges': [{'CidrIp': f"{trustedhost_private_ip}/32"}],  # Restrict to Trustedhost IP
                }  
            ]
        )
        print(f"Ingress rules added to security group {group_name}.")

        
        # Add outbound rules (Allow all outbound for internal communication)
        ec2_client.authorize_security_group_egress(
            GroupId=security_group_id,
            IpPermissions=[
                # Allow HTTP traffic to the Proxy
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,  
                    'ToPort': 80,
                    'UserIdGroupPairs': [{'GroupId': security_group_id_sql_instances}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,  
                    'ToPort': 443,
                    'UserIdGroupPairs': [{'GroupId': security_group_id_sql_instances}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,  # FastAPI Application Port
                    'ToPort': 8000,
                    'UserIdGroupPairs': [{'GroupId': security_group_id_sql_instances}]
                }  
            ]
        )
        print(f"Egress rules added to security group {group_name}.")

            
        return security_group_id

    except ClientError as e:
        print(f"Error creating security group: {e}")
        return None


