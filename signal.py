import json
import os

import boto3
import random

from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
import uuid

table_name = os.environ['CONNECTION_TABLE']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)
        
def get_my_peer_id(connection_id, scan_response):
    for item in scan_response['Items']:
        if connection_id != item['connection_id']:
            return item['connection_id']

def send_answer_to_peer(connection_id, answer):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'Answer':answer
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=get_my_peer_id(connection_id,table.scan())
    )
    
def send_offer_to_peer(connection_id, offer):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'Offer':offer
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=get_my_peer_id(connection_id,table.scan())
    )

def send_candidate_to_peer(connection_id, candidate):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'IceCandidate':candidate==null
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=get_my_peer_id(connection_id,table.scan())
    )

def update_session_connected(connection_id, session_id):
    table.update_item(
    Key={
        'Status': 'WAITING',
        'SessionId': session_id
    },
    UpdateExpression="set NonInitPeerConnectionId = :p, Status=:s",
    ExpressionAttributeValues={
        ':p': connection_id,
        ':s': "CONNECTED"
    }
    )

def close_session(connection_id, session_id):
    table.update_item(
    Key={
        'Status': 'CONNECTED',
        'SessionId': session_id
    },
    UpdateExpression="set NonInitPeerConnectionId = :p, Status=:s",
    ExpressionAttributeValues={
        ':p': connection_id,
        ':s': "WAITING"
    }
    )

def notify_all_peers(connection_id, session_id):
    query_resp = table.query(
    KeyConditionExpression=Key('Status').eq('WAITING') & Key('SessionId').eq(session_id)
    )
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    session = query_resp['Items'][0]:
    update_session_connected(connection_id, session_id)
    data = {
        'PeerStatus':'Connected',
        'PeerConnectionId' : str(connection_id)
    }
    ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=session['InitPeerConnectionId']
    )
    data = {
        'PeerStatus':'Connected',
        'PeerConnectionId' : session['InitPeerConnectionId']
    }
    ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=connection_id
    )

def get_waiting_peers():
    response = table.query(
    KeyConditionExpression=Key('Status').eq('WAITING')
    )
    return response['Items']

def make_as_init_peer(connection_id):
    session_id = uuid.uuid4()
    response = table.put_item(
        Item={
            "SessionId" : str(session_id)
            "InitPeerConnectionId" : str(connection_id),
            "NonInitPeerConnectionId" : ""
            "Status" : "WAITING"
        }
    )
    return session_id

def who_am_I_reply(connection_id):
    whoamI = 'InitPeer'
    session_id = "000"
    waiting_peers  = get_waiting_peers()
    if len(waiting_peers)>0:
        whoamI = 'NonInitPeer'
        rand_index = random.randint(0, len(waiting_peers)-1)
        peer = waiting_peers[rand_index]
        session_id = peer['SessionId']
    else
        session_id = make_as_init_peer(connection_id)

    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'WhoAmI':whoamI,
        'SessionId': str(session_id)
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=connection_id
    )

def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    body = json.loads(event.get('body'))
    step = body.get('Step')
    if 'WhoAmI' == step:
        who_am_I_reply(connection_id)
    if 'PeerConnected' == step:
        session_id = body.get('Data').get('SessionId')
        notify_all_peers(connection_id,session_id)
    if 'IceCandidate' == step:
        print('Ice Candidate signal.')
        send_candidate_to_peer(connection_id, body.get('Data'))
    if 'Offer' == step:
        send_offer_to_peer(connection_id, body.get('Data'))
    if 'Answer' == step:
        send_answer_to_peer(connection_id, body.get('Data'))
    if 'CloseConnection' == step:
        session_id = body.get('Data').get('SessionId')
        close_session(connection_id, session_id)
        
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
