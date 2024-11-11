import boto3
from botocore.exceptions import ClientError

#ec2_client = boto3.client('ec2')
ec2_client = boto3.client('ec2', region_name='us-east-1')
ec2 = boto3.resource('ec2', region_name='us-east-1')
def terminate_instances(instance_ids):
    if not instance_ids:
        print("No instances to terminate.")
        return
    
    try:
        print(f"Terminating instances: {', '.join(instance_ids)}")
        ec2.instances.filter(InstanceIds=instance_ids).terminate()

        for instance_id in instance_ids:
            instance = ec2.Instance(instance_id)
            print(f'Waiting for instance {instance_id} to terminate...')
            instance.wait_until_terminated()
            print(f'Instance {instance_id} has been terminated.')
    except ClientError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")