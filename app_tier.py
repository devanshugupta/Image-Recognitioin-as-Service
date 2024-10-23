import boto3
import subprocess
import os

aws_access_key_id='' # Enter your keys here
aws_secret_access_key=''


S3_INPUT_BUCKET_NAME = 'in-bucket'
S3_OUTPUT_BUCKET_NAME = 'out-bucket'

REQ_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/242201280391/req-queue'
RESP_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/242201280391/resp-queue'


print('Instance Started ...')
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
while True:
    response = sqs.receive_message(
        QueueUrl=REQ_QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=1,

    )

    if 'Messages' in response:

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        filename = message['Body']

        local_file_path = './'+ filename
        print(filename)
        s3.download_file(S3_INPUT_BUCKET_NAME, filename, local_file_path)

        result = subprocess.check_output(['python3', 'face_recognition.py', local_file_path])
        result = result.decode('utf-8').strip()

        filename = filename.split('.')[0]

        print('app tier: ', filename, result)
        s3.put_object(Bucket=S3_OUTPUT_BUCKET_NAME, Body=result, Key=filename)

        sqs.delete_message(
            QueueUrl=REQ_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )

        sqs.send_message(
            QueueUrl=RESP_QUEUE_URL,
            MessageBody=filename
        )

        os.remove(local_file_path)
