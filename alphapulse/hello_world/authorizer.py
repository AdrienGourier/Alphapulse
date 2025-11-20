# hello_world/authorizer.py
import json
from auth.auth import verify_token

def lambda_handler(event, context):
    """Lambda authorizer for API Gateway"""
    token = event.get('headers', {}).get('Authorization', '')
    if not token.startswith('Bearer '):
        return generate_policy('user', 'Deny', event['methodArn'])
    
    token = token.split(' ')[1]
    
    try:
        result = verify_token(token)
        if result['valid']:
            principal_id = result['user']['sub']
            return generate_policy(principal_id, 'Allow', event['methodArn'], result['user'])
    except Exception as e:
        print(f"Auth failed: {e}")
    
    return generate_policy('user', 'Deny', event['methodArn'])

def generate_policy(principal_id, effect, resource, context=None):
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }
    if context:
        policy['context'] = context
    return policy