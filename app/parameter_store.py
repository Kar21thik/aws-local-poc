import boto3
import os

def get_ssm_client():
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    return boto3.client('ssm', endpoint_url=endpoint_url, region_name=region)

def get_parameter(name):
    ssm = get_ssm_client()
    return ssm.get_parameter(Name=name)['Parameter']['Value']

_cache = {}

def get_cached_parameter(name):
    if name not in _cache:
        _cache[name] = get_parameter(name)
    return _cache[name]