# config.py

import boto3
import os

def get_aws_client(service_name):
    """
    Returns a boto3 client for the service, handling LocalStack endpoint automatically.
    """
    region = os.environ.get("AWS_REGION", "us-east-1")
    endpoint_url = os.environ.get("AWS_ENDPOINT_URL")

    # Use localhost default if endpoint not set and not running in Lambda
    if not endpoint_url and not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        endpoint_url = "http://localhost:4566"

    kwargs = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url

    return boto3.client(service_name, **kwargs)
