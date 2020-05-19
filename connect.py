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


def lambda_handler(event, context):
    connection_id = event.get('requestContext', {}).get('connectionId')
    response = table.put_item(
        Item={
            "ConnectionId": str(connection_id)
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully connected')
    }
