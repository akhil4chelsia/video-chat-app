import json
import os

import boto3

table_name = os.environ['CONNECTION_TABLE']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)


def trigget_init(connection_id):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'trigger' : "InitPeer"
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=connection_id
    )
    
def pick_offer(connection_id,peer_connection_id, offer):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'ConnectionID' : peer_connection_id,
        'Offer':offer
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=connection_id
    )
    
                

def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    scan_response = table.scan()
    if len(scan_response['Items']) == 1:
        trigget_init(connection_id)
    else:
        for item in scan_response['Items']:
            if item['connection_id'] != connection_id:
                pick_offer(connection_id, item['connection_id'], item['Offer'])

    return {
        'statusCode': 200,
        'body': 'Answer sent. Waiting for confirmation'
    }
