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
        
def notify_peer(peer_connection_id):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'PeerDisconnected':'true'
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=peer_connection_id
    )

def delete_session(session_id):
    table.delete_item(
        Key={
            'SessionId': session_id
        })

def remove_user(connection_id):
    conn_table_name = os.environ['CONNECTION_TABLE']
    conn_dynamodb = boto3.resource('dynamodb')
    conn_table = conn_dynamodb.Table(conn_table_name)
    conn_table.delete_item(
        Key={
            'ConnectionId': connection_id
        })
        
def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    remove_user(connection_id)
    response = table.scan(
         FilterExpression=Attr("NonInitPeerConnectionId").eq(connection_id) | Attr("InitPeerConnectionId").eq(connection_id)
    )
    session = response['Items'][0]
    delete_session(session['SessionId'])
    peer_connection_id = session['NonInitPeerConnectionId'] if connection_id==session['InitPeerConnectionId'] else session['InitPeerConnectionId']
    notify_peer(peer_connection_id)
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully disconnected')
    }