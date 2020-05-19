import json
import os
import random
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

table_name = os.environ['CONNECTION_TABLE']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

def notify_users_online(connection_id,session_count):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'SessionsCount': session_count
    }
    ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=connection_id
    )

def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    session_count = 0
    response = table.scan()
    session_count = session_count + len(response['Items'])

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey']
            )
    
        session_count = session_count + len(response['Items'])
            
    notify_users_online(connection_id,session_count)
    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }