"""
API Gateway Lambda Authorizer - JWT validation
"""

import json
import os
import jwt

JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key")

def lambda_handler(event, context):
    """
    Validates JWT token from Authorization header
    """
    token = event.get("authorizationToken", "").replace("Bearer ", "")
    
    try:
        # Decode JWT
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        # Generate IAM policy
        return generate_policy(user_id, "Allow", event["methodArn"])
        
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

def generate_policy(principal_id, effect, resource):
    """
    Generate IAM policy for API Gateway
    """
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource
                }
            ]
        },
        "context": {
            "userId": principal_id
        }
    }
