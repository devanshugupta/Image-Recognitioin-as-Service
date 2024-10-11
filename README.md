# Image-Recognitioin-as-Service
Auto scaling cloud-based image recognition service using AWS infrastructure. Utilized EC2 for deploying machine learning models, S3 for object storage, and SQS to handle 1,000 concurrent requests via a Flask framework.

# Run
Run the workload_generator.py using the elastic ip (for now closed to save costs). 

The app-tier.py is the Machine learning code.
The web-tier.py auto sclaes upto 20 EC2 instances for 1000 concurrent requests and shuts them down in 30s of no messages in SQS message queue. 


