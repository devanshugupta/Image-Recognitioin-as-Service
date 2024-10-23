import boto3
import time
from flask import Flask, request
import threading

app = Flask(__name__)

aws_access_key_id='' # Enter your keys here
aws_secret_access_key=""

user_data_script = """#!/bin/bash
cd /home/ubuntu/
nohup sudo -u ubuntu python3 app_tier.py > /home/ubuntu/app_tier.log 2>&1 &
"""

ec2_client = boto3.client('ec2', region_name='us-east-1', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

s3 = boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
    )
sqs = boto3.client(
    'sqs',
    region_name='us-east-1',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
    )
'''
def create_sqs_queue(queue_name):
    response = sqs.create_queue(QueueName=queue_name+'.fifo',
                                       Attributes={
                                            'FifoQueue': 'true',
                                           'ContentBasedDeduplication': 'true'
                                           }
                                       )

    return response
'''

S3_INPUT_BUCKET_NAME = 'in-bucket'
S3_OUTPUT_BUCKET_NAME = 'out-bucket'

REQ_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/242201280391/-req-queue'
RESP_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/242201280391/-resp-queue'
MAX_INSTANCES = 20
MIN_INSTANCES = 0
app_instances = 0

def get_num_instances(ec2_client):
    try:
        instance_count = 0
        reservations = ec2_client.describe_instances(Filters=[
            {
                "Name": "instance-state-name",
                "Values": ['running', 'pending']
            }
        ]).get("Reservations", [])

        # Count the instances in all reservations
        for reservation in reservations:
            instance_count += len(reservation.get("Instances", []))

        return instance_count

    except Exception as e:
        print(f"Error retrieving instance count: {str(e)}")
        return 0


def get_instance(num):
    tagname = f'app-tier-instance-{num}'
    reservations = ec2_client.describe_instances(Filters=[
        {
            "Name": "instance-state-name",
            "Values": ['running']
        },
        {
            'Name': f'tag:Name',
            'Values': [tagname]
        }
    ]).get("Reservations",[])

    instance_id = []
    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id.append(instance["InstanceId"])
    return instance_id

# Web Tier Autoscaling logic

def delete_instance(app_instances):
    try:
        instance_id = get_instance(app_instances)
        ec2_client.terminate_instances(InstanceIds=instance_id)
    except:
        print('Instance not found for delete')

# Launch new app-tier EC2 instance
def wait_for_instance(instance_id):
    while True:
        response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
        statuses = response.get('InstanceStatuses', [])
        if statuses and statuses[0]['InstanceState']['Name'] == 'running':
            break
def launch_new_instance(instance_num):
    response = ec2_client.run_instances(
        ImageId='ami-034c1b27c50a6f62d',
        MinCount=1,
        MaxCount=1,
        InstanceType='t2.micro',
        KeyName='my_key_pair',  # Replace with your key pair
        SecurityGroups=['launch-wizard-1'],
        UserData=user_data_script,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': f"app-tier-instance-{instance_num}"}]
        }]
    )
    instance_id = response['Instances'][0]['InstanceId']
    return instance_id
def auto_scale():
    while True:
        app_instances = get_num_instances(ec2_client)-1
        response = sqs.get_queue_attributes(QueueUrl=REQ_QUEUE_URL, AttributeNames=['ApproximateNumberOfMessages'])
        message_count = int(response['Attributes']['ApproximateNumberOfMessages'])

        print(f'{message_count} req, {app_instances} instances.')

        if message_count > app_instances and app_instances < MAX_INSTANCES:
            print('launching new instance: ', app_instances+1)
            instance_id = launch_new_instance(app_instances+1)
            #wait_for_instance(instance_id)

        elif message_count==0 and app_instances > MIN_INSTANCES:
            print('terminating instance: ', app_instances)
            delete_instance(app_instances)
        time.sleep(3)
classification_results = {}

@app.route("/", methods=["POST"])
def handle_request():
    if 'inputFile' not in request.files:
        return "No file uploaded", 400

    file = request.files['inputFile']
    filename = file.filename
    print(filename, 'web_tier')
    # Upload image to S3
    s3.put_object(Bucket=S3_INPUT_BUCKET_NAME, Key=filename, Body=file)

    sqs.send_message(
        QueueUrl=REQ_QUEUE_URL,
        MessageBody=filename
    )
    filename = filename.split('.')[0]

    while True:
        response = sqs.receive_message(
            QueueUrl=RESP_QUEUE_URL,
            MaxNumberOfMessages=1
        )
        if 'Messages' in response and response['Messages'][0]['Body'] == filename:
            result_message = response['Messages'][0]
            receipt_handle = result_message['ReceiptHandle']

            output_body = s3.get_object(Bucket=S3_OUTPUT_BUCKET_NAME, Key=filename)
            prediction = output_body['Body'].read().decode('utf-8')
            result = filename + ':' + prediction

            sqs.delete_message(
                QueueUrl=RESP_QUEUE_URL,
                ReceiptHandle=receipt_handle
            )
            return result, 200

autoscaling_thread = threading.Thread(target=auto_scale)
autoscaling_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
