# Image-Recognitioin-as-Service

- Auto scaling cloud-based web service for Image Recognition using AWS infrastructure.
- Utilized EC2 for deploying Machine Learning models using PyTorch.
- S3 for object storage
- SQS message queues to handle 1,000 concurrent requests via a Flask framework.

# Uploads

- Upload the relevant ML code, files and import packages (boto3, flask, requests, pandas, PyTorch ...) into an EC2 (app) instance.
- Create an Image of this instance using Instance Volume's Snapshot in AWS console.
- Edit the user data script in web_tier.py to run the app_tier.py for when launching instances.
  
# Run

- Run the web_tier.py to deploy the service with the correct ami-image-id in launch_instance function.
- Run the workload_generator.py (instructions given https://github.com/visa-lab/CSE546-Cloud-Computing/tree/main/workload_generator) using the elastic ip (Use your own).
- Check the results, should be 1000 concurrent requests correct using 20 instances.

# Notes
- The app-tier.py is the Machine learning code deployment.
- The web-tier.py provides Auto Scaling service of upto 20 EC2 instances (free tier limit) for 1000 concurrent requests.
- Shuts the app instances down in 3s of no messages in SQS message queue.
- The files and results will be present in the S3 Input and Output buckets.



