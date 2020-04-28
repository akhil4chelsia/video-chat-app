import json
import os

import boto3

table_name = os.environ['CONNECTION_TABLE']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

def update_offer(connection_id, offer):
    response = table.update_item(
        Key={
            'connection_id': connection_id
        },
        UpdateExpression="set Offer = :r, Connected = :c",
        ExpressionAttributeValues={
            ':r': offer,
            ':c':'false'
        }
    )

def notify_peer(peer_connection_id, my_connection_id, offer):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'ConnectionID' : my_connection_id,
        'Offer':offer
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=peer_connection_id
    )
    
def signal_answer(connection_id, offer):
    scan_response = table.scan()
    if len(scan_response['Items']) > 1:
        for item in scan_response['Items']:
            if item['connection_id'] != connection_id and item['Connected'] == 'false':
                notify_peer(connection_id, item['connection_id'] , offer)
                

def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    body = json.loads(event.get('body'))
    offer = body.get('Offer')
    print('akhil',offer)
    print('connectionId',connection_id)
    update_offer(connection_id, offer)
    signal_answer(connection_id, offer)

    return {
        'statusCode': 200,
        'body': 'Waiting for peers'
    }
