import boto3
import time

AWS_ACCESS_KEY_ID='Enter the access key id'
AWS_SECRET_ACCESS_KEY = 'Enter the secret access key'
REGION = 'us-east-1'

# Initialize the AWS services clients
ec2_client = boto3.client(
    'ec2',
    region_name='us-east-1',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
s3_client = boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
sqs_client = boto3.client(
    'sqs',
    region_name='us-east-1',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

# Function to create an EC2 instance
def create_ec2_instance():
    instance = ec2_client.run_instances(
        ImageId="ami-0a0e5d9c7acc336f1",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'TestInstance'}]
        }]
    )

    return instance

# Function to create an S3 bucket
def create_s3_bucket(bucket_name):
    s3_client.create_bucket(Bucket=bucket_name)
    print(f"S3 bucket '{bucket_name}' created.")
    return s3_client

# Function to create an SQS queue
def create_sqs_queue(queue_name):
    response = sqs_client.create_queue(QueueName=queue_name,
                                       Attributes={
                                            'FifoQueue': 'true',
                                           'ContentBasedDeduplication': 'true'
                                           }
                                       )

    return response

# Function to list EC2 instances, S3 buckets, and SQS queues
def list_resources():
    print("Listing resources:")
    # List EC2 instances
    ec2_instances = ec2_client.describe_instances()
    instance_ids = [i['InstanceId'] for r in ec2_instances['Reservations'] for i in r['Instances']]
    print(f"EC2 Instances: {instance_ids}")

    # List S3 buckets
    s3_buckets = s3_client.list_buckets()['Buckets']
    bucket_names = [bucket['Name'] for bucket in s3_buckets]
    print(f"S3 Buckets: {bucket_names}")

    # List SQS queues
    sqs_queues = sqs_client.list_queues()
    queue_urls = sqs_queues.get('QueueUrls', [])
    print(f"SQS Queues: {queue_urls}")

# Function to upload a file to S3
def upload_to_s3(bucket_name, file_name, s3_file_name):
    try:
        s3_client.upload_file(file_name, bucket_name, s3_file_name)
        print(f"File '{file_name}' successfully uploaded to bucket '{bucket_name}' as '{s3_file_name}'.")
    except Exception as e:
        print(f"Error uploading file: {str(e)}")

# Function to send a message to SQS
def send_sqs_message(queue_url, message_name, message_body, message_group_id):
    sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body, MessageGroupId=message_group_id, MessageAttributes={
        'Name': {
            'StringValue': message_name,
            'DataType': 'String'
        }
    })
    print("Message sent.")

# Function to check the number of messages in an SQS queue
def get_message_count(queue_url):
    response = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    message_count = response['Attributes']['ApproximateNumberOfMessages']
    print(f"Messages in SQS queue: {message_count}")
    return message_count

# Function to pull a message from SQS
def receive_sqs_message(queue_url):
    response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, MessageAttributeNames=['All'])
    messages = response.get('Messages', [])
    if messages:
        message = messages[0]
        print(f"Message name: {message['MessageAttributes']['Name']['StringValue']}")
        print(f"Message body: {message['Body']}")
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])
    else:
        print("No messages received.")

# Function to delete resources
def delete_resources(instance_id, bucket_name, queue_url, s3_file_name):
    # Terminate EC2 instance
    ec2_client.terminate_instances(InstanceIds=[instance_id])
    print(f"EC2 instance {instance_id} terminated.")

    # Delete S3 bucket and its contents
    s3_client.delete_object(Bucket=bucket_name, Key=s3_file_name)
    s3_client.delete_bucket(Bucket=bucket_name)
    print(f"S3 bucket '{bucket_name}' deleted.")

    # Delete SQS queue
    sqs_client.delete_queue(QueueUrl=queue_url)
    print(f"SQS queue deleted.")

# Main script logic
def main():
    # Create resources

    instance = create_ec2_instance()
    instance_id = instance['Instances'][0]['InstanceId']
    print(f"EC2 instance {instance_id} created.")

    bucket_name = "cse546test-bucket"
    file_name, s3_file_name = "CSE546test.txt", "CSE546test.txt"
    queue_name = "cse546test-queue.fifo"

    response = create_sqs_queue(queue_name)
    queue_url = response['QueueUrl']
    print(f"SQS queue '{queue_name}' created.")

    s3_client = create_s3_bucket(bucket_name)

    print("Request sent, waiting for 1 min")
    time.sleep(60)

    # List resources
    list_resources()

    print('Uploading file to S3 bucket')
    # Upload empty text file to S3
    upload_to_s3(bucket_name, file_name, s3_file_name)

    print('Sending message to SQS queue')
    # Send message to SQS
    send_sqs_message(queue_url, 'test message',"This is a test message", 'group1')

    # Check number of messages in the queue
    get_message_count(queue_url)

    # Receive and print the message
    receive_sqs_message(queue_url)

    # Check number of messages again
    get_message_count(queue_url)

    print("Waiting for 10 seconds")
    time.sleep(10)

    # Delete all resources
    delete_resources(instance_id, bucket_name, queue_url, s3_file_name)

    print("Deleted resources, Waiting for 20 seconds")
    time.sleep(20)

    # List resources again
    list_resources()
main()