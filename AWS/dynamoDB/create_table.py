import logging
# from json import dumps, loads
import json
from dynamodb_json import json_util as jsonDB
import boto3

dynamodb = boto3.client('dynamodb')
waiter1 = dynamodb.get_waiter('table_exists')
waiter2 = dynamodb.get_waiter('table_not_exists')
table_names = ['Weather_API_toronto', 'Weather_API_kingston', 'Weather_API_innisfil',
    'Open_Weather_toronto','Open_Weather_kingston', 'Open_Weather_innisfil',
    'Accu_Weather_toronto', 'Accu_Weather_kingston', 'Accu_Weather_innisfil']

def create_tables():
    for table_name in table_names:
        response = dynamodb.create_table(
            TableName= table_name,
            AttributeDefinitions=[
                {
                    'AttributeName': 'Date',
                    'AttributeType': 'S',
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'Date',
                    'KeyType': 'HASH',
                },
            ],
            BillingMode = 'PAY_PER_REQUEST',
        )

    for table_name in table_names:    
        forcast_item = {
            'Date': 'AverageForcast',
            'f1': {'avg':0,'count':0},
            'f2': {'avg':0,'count':0},
            'f3': {'avg':0,'count':0},
            'f4': {'avg':0,'count':0},
            'f5': {'avg':0,'count':0},
            'f6': {'avg':0,'count':0},
            'f7': {'avg':0,'count':0},
            'f8': {'avg':0,'count':0},
            'f9': {'avg':0,'count':0},
            'f10': {'avg':0,'count':0},
            'f11': {'avg':0,'count':0},
            'f12': {'avg':0,'count':0},
        }
        forcast_item = json.loads(jsonDB.dumps(forcast_item))
        waiter1.wait(
            TableName=table_name,
            WaiterConfig={
                'Delay': 5,
                'MaxAttempts': 5
            }
        )
        dynamodb.put_item(TableName = table_name, Item = forcast_item)

def lambda_handler(event, context):
    """
    This function creates a new RDS database table and writes records to it
    """
    function = event['Function']    
    if function == 'Create':
        create_tables()
    elif function == 'Delete':
        for table_name in table_names:
            response = dynamodb.delete_table(TableName = table_name)

    elif function == 'Clear':
        for table_name in table_names:
            response = dynamodb.delete_table(TableName = table_name)
        for table_name in table_names:
            waiter2.wait(
                TableName=table_name,
                WaiterConfig={
                    'Delay': 5,
                    'MaxAttempts': 5
                }
            )
        create_tables()
        
    return f'Function: {function} exected'
    