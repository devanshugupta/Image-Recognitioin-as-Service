# Image-Recognitioin-as-Service
- Auto scaling cloud-based web service for Image Recognition using AWS infrastructure.
- Utilized EC2 for deploying machine learning models
- S3 for object storage
- SQS to handle 1,000 concurrent requests via a Flask framework.

# Run
Run the workload_generator.py (instructions given https://github.com/visa-lab/CSE546-Cloud-Computing/tree/main/workload_generator) using the elastic ip (for now closed to save costs). 

- The app-tier.py is the Machine learning code deployment.
- The web-tier.py provides Auto Scaling service of upto 20 EC2 instances (free tier limit) for 1000 concurrent requests and shuts them down in 3s of no messages in SQS message queue.



