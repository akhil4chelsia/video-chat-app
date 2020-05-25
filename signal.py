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


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)


def send_answer_to_peer(connection_id, answer):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'Answer': answer
    }
    scan_resp = table.scan()
    items = scan_resp['items']
    for item, in items:
        if item['ConnectionId'] != connection_id
        ws_client.post_to_connection(
            Data=json.dumps(data, cls=DecimalEncoder),
            ConnectionId=item['ConnectionId']
        )


def send_offer_to_peer(connection_id, offer):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'Offer': offer
    }
    scan_resp = table.scan()
    items = scan_resp['Items']
    for item in items:
        if item['ConnectionId'] != connection_id:
            ws_client.post_to_connection(
                Data=json.dumps(data, cls=DecimalEncoder),
                ConnectionId=item['ConnectionId']
            )


def send_candidate_to_peer(connection_id, candidate):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'IceCandidate': candidate
    }
    scan_resp = table.scan()
    items = scan_resp['Items']
    for item in items:
        if item['ConnectionId'] != connection_id:
            ws_client.post_to_connection(
                Data=json.dumps(data, cls=DecimalEncoder),
                ConnectionId=item['ConnectionId']
            )

def notify_all_peers():
    query_resp = table.scan()
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    items = query_resp['Items']
    for item in items:
        data = {
            'PeerStatus': 'Connected',
            'PeerConnectionId': item['ConnectionId']
        }
        ws_client.post_to_connection(
            Data=json.dumps(data),
            ConnectionId=item['ConnectionId']
        )

def who_am_I_reply(connection_id):
    whoamI = 'InitPeer'
    waiting_peers = table.scan()['Items']
    if len(waiting_peers) > 1:
        whoamI = 'NonInitPeer'

    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'WhoAmI': whoamI
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
        send_candidate_to_peer(connection_id, body.get('Data'))
    if 'Offer' == step:
        send_offer_to_peer(connection_id, body.get('Data'))
    if 'Answer' == step:
        send_answer_to_peer(connection_id, body.get('Data'))
    if 'CloseConnection' == step:
        close_session(connection_id)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
