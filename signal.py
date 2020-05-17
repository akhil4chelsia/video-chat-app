import json
import os

import boto3

from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

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

def notify_all_peers():
    scan_resp = table.scan()
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    for item in scan_resp['Items']:
        data = {
            'PeerStatus':'Connected',
            'PeerConnectionId' : get_my_peer_id(item['connection_id'], scan_resp)
        }
        response = ws_client.post_to_connection(
            Data=json.dumps(data),
            ConnectionId=item['connection_id']
        )

def who_am_I_reply(connection_id):
    whoamI = 'InitPeer'
    scan_resp = table.scan()
    if len(scan_resp['Items'])==2:
        whoamI = 'NonInitPeer'
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'WhoAmI':whoamI
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
        notify_all_peers()
    if 'IceCandidate' == step:
        print('Ice Candidate signal.')
        send_candidate_to_peer(connection_id, body.get('Data'))
    if 'Offer' == step:
        send_offer_to_peer(connection_id, body.get('Data'))
    if 'Answer' == step:
        send_answer_to_peer(connection_id, body.get('Data'))
        
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
