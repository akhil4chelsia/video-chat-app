import json
import os

import boto3


def lambda_handler(event, context):
    table_name = os.environ['CONNECTION_TABLE']
    connection_id = event.get('requestContext', {}).get('connectionId')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.delete_item(
        Key={
            'connection_id': connection_id
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully disconnected')
    }
