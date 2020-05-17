import json
import os

import boto3

table_name = os.environ['CONNECTION_TABLE']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

def get_my_peer_id(connection_id, scan_response):
    for item in scan_response['Items']:
        if connection_id != item['connection_id']:
            return item['connection_id']

def notify_peer(connection_id):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'PeerDisconnected':'true'
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=get_my_peer_id(connection_id,table.scan())
    )

def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    response = table.delete_item(
        Key={
            'connection_id': connection_id
        }
    )

    notify_peer(connection_id)

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully disconnected')
    }
