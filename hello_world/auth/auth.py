# hello_world/auth/auth.py
import jwt
from jose import JWTError, jwt as jose_jwt
import requests
import boto3

# YOUR REAL VALUES FROM COGNITO
USER_POOL_ID = "us-east-1_OQmaANeqr"
APP_CLIENT_ID = "4niv1oogjm25ln9ummhepvdib3"
REGION = "us-east-1"

JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"

def get_jwks():
    return requests.get(JWKS_URL).json()

def verify_token(token: str) -> dict:
    """Verify Cognito JWT and return payload if valid"""
    try:
        # Get unverified header to find the kid
        unverified_header = jose_jwt.get_unverified_header(token)
        kid = unverified_header['kid']
        
        # Find the correct public key
        jwks = get_jwks()
        key = next((k for k in jwks['keys'] if k['kid'] == kid), None)
        if not key:
            raise ValueError("Public key not found")
        
        # Verify and decode
        payload = jose_jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
        )
        return {"valid": True, "user": payload}
        
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")
    