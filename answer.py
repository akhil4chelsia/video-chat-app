import json
import os

import boto3

table_name = os.environ['CONNECTION_TABLE']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

def update_answer(connection_id, answer):
    response = table.update_item(
        Key={
            'connection_id': connection_id
        },
        UpdateExpression="set Answer = :r",
        ExpressionAttributeValues={
            ':r': answer
        }
    )

def signal_answer(connection_id, answer, peer_connection_id):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'ConnectionID' : connection_id,
        'Answer':answer
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=peer_connection_id
    )
                

def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    body = json.loads(event.get('body'))
    answer = body.get('Answer')
    peer_connection_id = body.get('ConnectionID')
    print('akhil',answer)
    print('connectionId',connection_id)
    update_answer(connection_id, answer)
    signal_answer(connection_id, answer, peer_connection_id)

    return {
        'statusCode': 200,
        'body': 'Answer sent. Waiting for confirmation'
    }
