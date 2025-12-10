# hello_world/authorizer.py
import json

def lambda_handler(event, context):
    """Relaxed Lambda authorizer for API Gateway - allows all requests for testing"""
    # For testing purposes, always allow and set a default user
    principal_id = 'public-test'
    
    # Build the policy to allow the request
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': 'Allow',
                'Resource': event['methodArn']
            }]
        },
        'context': {
            'sub': 'public-test',
            'userId': 'public-test'
        }
    }
    
    return policy