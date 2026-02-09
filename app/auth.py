"""
JWT validation utility for Lambda functions
"""

import os
import jwt

JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key")

def validate_token(token):
    """
    Validates JWT token and returns user_id
    Returns None if invalid
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
