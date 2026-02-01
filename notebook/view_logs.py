# Add this cell to your notebook to view logs

import boto3
import json

logs = boto3.client("logs", endpoint_url="http://localhost:4566", region_name="us-east-1")

def get_lambda_logs(function_name, limit=20):
    """Fetch recent Lambda logs"""
    log_group = f"/aws/lambda/{function_name}"
    
    try:
        # Get log streams
        streams = logs.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams['logStreams']:
            print(f"❌ No logs found for {function_name}")
            return
        
        stream_name = streams['logStreams'][0]['logStreamName']
        
        # Get log events
        events = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=limit
        )
        
        print(f"\n📋 Recent logs for {function_name}:\n")
        print("=" * 80)
        for event in events['events']:
            print(event['message'].strip())
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error fetching logs: {e}")

# Usage:
get_lambda_logs("task_lambda")
get_lambda_logs("notification_lambda")
