import boto3
from botocore.exceptions import ClientError

# Initialize EC2 client
ec2_client = boto3.client('ec2', region_name='us-east-1')

def create_trusted_host_security_group(group_name, description, vpc_id, gatekeeper_security_group_id):
    """
    Creates a security group for the Trusted Host Node with limited access.
    
    Parameters:
        group_name (str): The name of the security group.
        description (str): Description of the security group.
        vpc_id (str): The VPC ID where the security group will be created.
        gatekeeper_security_group_id (str): The Security Group ID of the Gatekeeper.
    
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

        # Add inbound rules (Allow access from Gatekeeper)
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,  # FastAPI Application Port
                    'ToPort': 8000,
                    'UserIdGroupPairs': [{'GroupId': gatekeeper_security_group_id}]
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

        '''
        # Add outbound rules (Allow all outbound for internal communication)
        ec2_client.authorize_security_group_egress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': '-1',  # All protocols
                    'FromPort': -1,
                    'ToPort': -1,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Open outbound traffic
                }
            ]
        )
        print(f"Egress rules added to security group {group_name}.")

        '''    
        return security_group_id

    except ClientError as e:
        print(f"Error creating security group: {e}")
        return None


