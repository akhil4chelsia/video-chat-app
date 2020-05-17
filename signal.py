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


def get_my_peer_id(session_id, connection_id):
    query_resp = table.query(
        KeyConditionExpression=Key('SessionId').eq(session_id)
    )
    session = query_resp['Items'][0]
    if session['InitPeerConnectionId'] == connection_id:
        return session['NonInitPeerConnectionId']
    else:
        return session['InitPeerConnectionId']


def send_answer_to_peer(session_id, connection_id, answer):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'Answer': answer
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=get_my_peer_id(session_id, connection_id)
    )


def send_offer_to_peer(session_id, connection_id, offer):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'Offer': offer
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=get_my_peer_id(session_id, connection_id)
    )


def send_candidate_to_peer(session_id, connection_id, candidate):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'IceCandidate': candidate
    }
    response = ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=get_my_peer_id(session_id, connection_id)
    )


def update_session_connected(connection_id, session_id):
    table.update_item(
        Key={
            'SessionId': session_id
        },
        UpdateExpression="set NonInitPeerConnectionId = :p, ConnectionStatus=:s",
        ExpressionAttributeValues={
            ':p': connection_id,
            ':s': "CONNECTED"
        }
    )


def notify_peer(session_id, connection_id):
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'PeerDisconnected': 'true'
    }
    ws_client.post_to_connection(
        Data=json.dumps(data, cls=DecimalEncoder),
        ConnectionId=get_my_peer_id(session_id, connection_id)
    )


def update_as_init_peer(session_id, connection_id, session):
    if connection_id == session['InitPeerConnectionId']:
        table.update_item(
            Key={
                'SessionId': session_id
            },
            UpdateExpression="set NonInitPeerConnectionId = :p, InitPeerConnectionId = :n, ConnectionStatus=:s",
            ExpressionAttributeValues={
                ':p': '',
                ':n': connection_id,
                ':s': "WAITING"
            }
        )


def delete_session(session_id):
    table.delete_item(
        Key={
            'SessionId': session_id
        })


def get_session(session_id):
    query_resp = table.query(
        KeyConditionExpression=Key('SessionId').eq(session_id)
    )
    return query_resp['Items'][0]


def close_session(connection_id, session_id):
    session = get_session(session_id)
    if session['ConnectionStatus'] == 'CONNECTED':
        update_as_init_peer(session_id, connection_id, session)
    else:
        delete_session(session_id)

    notify_peer(session_id, connection_id)


def notify_all_peers(connection_id, session_id):
    query_resp = table.query(
        KeyConditionExpression=Key('SessionId').eq(session_id)
    )
    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    session = query_resp['Items'][0]
    update_session_connected(connection_id, session_id)
    data = {
        'PeerStatus': 'Connected',
        'PeerConnectionId': str(connection_id)
    }
    ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=session['InitPeerConnectionId']
    )
    data = {
        'PeerStatus': 'Connected',
        'PeerConnectionId': session['InitPeerConnectionId']
    }
    ws_client.post_to_connection(
        Data=json.dumps(data),
        ConnectionId=connection_id
    )


def get_waiting_peers():
    response = table.scan(
        FilterExpression=Attr('ConnectionStatus').eq('WAITING')
    )
    return response['Items']


def make_as_init_peer(connection_id):
    session_id = uuid.uuid4()
    response = table.put_item(
        Item={
            "SessionId": str(session_id),
            "InitPeerConnectionId": str(connection_id),
            "NonInitPeerConnectionId": "",
            "ConnectionStatus": "WAITING"
        }
    )
    return session_id


def who_am_I_reply(connection_id):
    whoamI = 'InitPeer'
    session_id = "000"
    waiting_peers = get_waiting_peers()
    if len(waiting_peers) > 0:
        whoamI = 'NonInitPeer'
        rand_index = random.randint(0, len(waiting_peers) - 1)
        peer = waiting_peers[rand_index]
        session_id = peer['SessionId']
    else:
        session_id = make_as_init_peer(connection_id)

    ws_client = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WS_CONNECTION_URL'])
    data = {
        'WhoAmI': whoamI,
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
    session_id = body.get('SessionId')

    if 'WhoAmI' == step:
        who_am_I_reply(connection_id)
    if 'PeerConnected' == step:
        notify_all_peers(connection_id, session_id)
    if 'IceCandidate' == step:
        print('Ice Candidate signal.')
        send_candidate_to_peer(session_id, connection_id, body.get('Data'))
    if 'Offer' == step:
        send_offer_to_peer(session_id, connection_id, body.get('Data'))
    if 'Answer' == step:
        send_answer_to_peer(session_id, connection_id, body.get('Data'))
    if 'CloseConnection' == step:
        close_session(connection_id, session_id)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
