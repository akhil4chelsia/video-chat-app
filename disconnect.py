import json
import os
import random
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

table_name = os.environ['SESSION_TABLE']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)
        
def notify_all_peers(connection_id):
    query_resp = table.scan()
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    items = query_resp['Items']
    for item in items:
        if item['ConnectionId'] != connection_id:
            data = {
            'PeerDisconnected':'true',
            'PeerConnectionId': connection_id
            }
            ws_client.post_to_connection(
                Data=json.dumps(data),
                ConnectionId=item['ConnectionId']
            )

def delete_connection(connection_id):
    table.delete_item(
        Key={
            'ConnectionId': connection_id
        })
    
def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    delete_connection(connection_id)
    notify_all_peers(connection_id)
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully disconnected')
    }