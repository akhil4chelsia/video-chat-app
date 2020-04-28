import json
import os

import boto3


def lambda_handler(event, context):
    table_name = os.environ['CONNECTION_TABLE']
    connection_id = event.get('requestContext', {}).get('connectionId')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.put_item(
        Item={
            'connection_id': str(connection_id),
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully connected')
    }
