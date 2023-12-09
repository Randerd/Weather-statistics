import logging
import math
import json
from dynamodb_json import json_util as jsonDB
import boto3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

#Needed because Lambda runs on a different timezone
time_zone = ZoneInfo("Canada/Eastern")
table_names = ['Weather_API_toronto', 'Weather_API_kingston', 'Weather_API_innisfil',
    'Open_Weather_toronto','Open_Weather_kingston', 'Open_Weather_innisfil',
    'Accu_Weather_toronto']

logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.client('dynamodb')

def get_value(table_name, date):
    item = dynamodb.get_item(TableName = table_name, Key= {'Date':{'S': date}})
    return jsonDB.loads(item)['Item']
    
def update_table(table_name, date, var, update):
    response = dynamodb.update_item(TableName=table_name, 
        Key={
            'Date': {'S':date}
        },
        UpdateExpression=f'set {var} = :r',
        ExpressionAttributeValues={
            ':r': {"M": update},
        },
        ReturnValues="UPDATED_NEW"
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        logger.info(f"Issue updating {date}-{var} in table {table_name}")
        
def put_value(table_name, update):
    update = json.loads(jsonDB.dumps(update))
    dynamodb.put_item(TableName = table_name, Item = update)
    
def date_format(date: datetime):
    #Formate for table key
    return date.strftime('%Y-%m-%dT%H')

def new_hour(cur_hour, diff):
    new_hour = cur_hour-diff
    return new_hour if new_hour>0 else new_hour-24

def temp_score(temp):
    #Temperature score
    return (2**(temp/7)) - 1

def cond_score(cond):
    #Condition score
    return (2**(cond/3)) - 1

def cloud_score(cloud):
    #Cloud score
    return (2**(cloud/105)) - 1

def hour_accuracy(temp, cond, cloud):
    #Accuracy score for hour type
    return round(math.exp( -(temp_score(temp) + cond_score(cond))**2) + math.exp(-(cloud_score(cloud))**2) - 1 , 4)*100

def date_accuracy(max, min, cond):
     #Accuracy score for date type
     return round(math.exp( -(temp_score(max)+ temp_score(min) + cond_score(cond))**2) , 4)*100

def lambda_handler(event, context):
    #Get current data and convert to table key format
    cur_date = datetime.now(tz=time_zone)
    fcur_date = date_format(cur_date)

    for table_name in table_names:
        try:#Get current weather and running average data
            logger.info(f"Calculating statistics for {table_name} at {fcur_date}")
            avgs = get_value(table_name, 'AverageForcast')
            cur_weather = get_value(table_name, fcur_date)['cur']
        except:
            logger.info(f"No Data entry for {fcur_date} in {table_name}")
            continue
        
        #Incase I missed a condition mapping
        #Or incase they actually use one of the ones I didn't know how to classify. 
            #What type of weather is "Hot"? What does that mean? Hot and cloudy? hot and rainy?
        if cur_weather['Condition'] == -1:
            logger.info(f"{fcur_date} missing condition data")
            continue
        
        #Compare with forcasted data from previous hours
        for hour in range(1,13): 
            #Date with wanted forcast range
            new_date = cur_date - timedelta(hours = hour)
            fnew_date = date_format(new_date)
            try:#Get forcasted value for current hour 
                data = get_value(table_name, fnew_date)
                cur_forcast, forcast_scores = data[f'f{hour}'], data['forcasts']
            except:
                logger.info(f'Forcast {hour} does not exist for {fnew_date} in {table_name}')
                continue
            
            #I'm not going to rant again. But seriously.. Cold? Hot? Come on AccuWeather
            if cur_forcast['Condition'] == -1:
                logger.info(f"{fnew_date} missing condition data for {hour} hour forcast ")
                continue
            
            #Calculate tempurature and condition differences
            t_diff = round(abs(cur_weather['Temp'] - cur_forcast['Temp']),2)
            d_diff = round(abs(cur_weather['Condition'] - cur_forcast['Condition']),2)
            # c_diff = round(abs(cur_weather['Cloud Cov'] - cur_forcast['Cloud Cov']),2)
            c_diff = 0  #Cloud score was providing WAY to much variance, also kinda covered in condition

            #Calculate accuracy score    
            score = round(hour_accuracy(t_diff, d_diff, c_diff),4)

            #Save forcasted for specific hour back to data in past
                #Can use these incase I want to implement variable date accessing
            forcast_scores[f'f{hour}'] = score
            update_table(table_name, fnew_date, 'forcasts',forcast_scores)
            
            #Update current forcast score running average
            forcast_avg = avgs[f'f{hour}']
            cur_avg, cur_count = forcast_avg['avg'], forcast_avg['count']
            cur_count+=1
            new_avg = round(cur_avg + (score-cur_avg) / cur_count,2)
            avgs[f'f{hour}'] = {'avg':new_avg, 'count':cur_count}
        
        #Update running averages
        put_value(table_name, avgs)

    return {
        'statusCode': 200,
        'body': json.dumps('Cowboy') #Yehaw
    }

