import json
import boto3 
from dynamodb_json import json_util as jsonDB

table_names = ['Weather_API_toronto', 'Weather_API_kingston', 'Weather_API_innisfil',
    'Open_Weather_toronto','Open_Weather_kingston', 'Open_Weather_innisfil',
    'Accu_Weather_toronto']
forcasts = ['f1', 'f2','f3','f4','f5','f6','f7','f8','f9','f10','f11','f12']
dynamodb = boto3.client('dynamodb')

def get_value(table_name, date):
    item = dynamodb.get_item(TableName = table_name, Key= {'Date':{'S': date}})
    return jsonDB.loads(item)['Item']
    
def lambda_handler(event, context):
    ret = []
    for table_name in table_names:
        avgs = get_value(table_name, 'AverageForcast')
        temp = []
        for forcast in forcasts:
            data = avgs[forcast]
            temp.append([data['avg'],data['count']])    #Get avg and count data from AverageForcast item for each table
        ret.append(temp)
    ret.append([['-',0]]*12)    #missing accu weather kingston
    ret.append([['-',0]]*12)    #missing accu weather innisfil
    print(ret)
    return {
        'statusCode': 200,
        'headers': {
            # 'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            # 'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(ret)
    }
