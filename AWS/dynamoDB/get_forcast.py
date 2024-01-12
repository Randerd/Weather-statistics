import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dynamodb_json import json_util as jsonDB
import boto3
import json
import logging
    
time_zone = ZoneInfo("Canada/Eastern")
dynamodb = boto3.client('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Translation maps for conditions to condition index for each provider
accu_weather_conditions = {
    1: {1,2,3,32,33,34,35},
    2: {4,5,6,36,37,38},
    3: {7,8,11},
    4: {12,13,14,18,22,23,39,40,44},
    5: {15,16,17,19,20,21,24,25,26,29,41,42,43},
}
#https://developer.accuweather.com/weather-icons
open_weather_conditions = {
    1: {800,801},
    2: {802,803},
    3: {701,711,721,731,741,751,761,762,804},
    4: {300,301,302,310,311,312,313,314,321,500,501,502,503,511,520,521,522,531,600,601,602,611,612,613,615,616,620,621,622},
    5: {200,201,202,210,211,212,221,230,231,232,504,771,781},
}
#https://openweathermap.org/weather-conditions
weather_api_conditions = {
    1: {1000},
    2: {1003},
    3: {1006,1009,1030,1135},
    4: {1063,1066,1069,1072,1114,1147,1150,1153,1168,1171,1180,1183,1186,1189,1192,1195,1198,1201,1204,1210,1213,1216,1219,1222,1225,1240,1243,1249,1255,1258,1261},
    5: {1087,1117,1207,1237,1246,1252,1264,1273,1276,1279,1282},
}
# https://www.weatherapi.com/docs/conditions.json

def get_forcast(weburl):
    res = requests.get(weburl)
    return res.json() if res.status_code<300 else None

def hour_rounder(date):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    # Used to make sure data is up-to-date
    return (date.replace(second=0, microsecond=0, minute=0, hour=date.hour)
               +timedelta(hours=date.minute//30))

def get_condition_index(condition_index, cond):
    for value, conditions in condition_index.items():
        if cond in conditions:
            return value
    CI_name = f'{condition_index=}'.split('=')[0]
    logger.info(f"No condition for {CI_name}, condition {cond}")
    return -1

def get_accu_weather(location):
    #Accu Weather specific location codes
    #Need multiple API keys to evaluate all locations
    api_keys = {'toronto': os.environ['ACCU_WEATHER_API_KEY1'], 
                'innisfil': os.environ['ACCU_WEATHER_API_KEY2'], 
                'kingston':os.environ['ACCU_WEATHER_API_KEY3']}
    accu_weather_api_key = api_keys[location]
   
    locations = {'toronto': '55488', 'thornhill': '1365404','innisfil': '55080', 'kingston':'49556'}
    #Calling APIs
    twelve_hour_forcast_url = "http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{location}?apikey={api_key}&metric=true&details=true"
    twelve_hour_forcast = get_forcast(twelve_hour_forcast_url.format(location = locations[location], api_key=accu_weather_api_key))
    current_forcast_url = "http://dataservice.accuweather.com/currentconditions/v1/{location}?apikey={api_key}&details=true"
    current_forcast = get_forcast(current_forcast_url.format(location = locations[location], api_key = accu_weather_api_key))
    title = f'Accu_Weather_{location}'
    res = []

    #If either forcast doesn't work, skip storing
    if twelve_hour_forcast == None or current_forcast == None:
        logger.info(title +' | Error')
        return title +' | Error'
    else:
        current_forcast = current_forcast[0]

    #Collect current weather data
        
    cur_time = hour_rounder(datetime.fromtimestamp(current_forcast['EpochTime'], tz=time_zone))
    temp = current_forcast['Temperature']['Metric']['Value']
    condition = get_condition_index(accu_weather_conditions, current_forcast['WeatherIcon'])
    cloud_cov = current_forcast['CloudCover']

    res.append(cur_time.strftime('%Y-%m-%dT%H'))
    res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})

    #If the 1 hour forcast is "supposedly" trying to forcast for the current time
    if cur_time.hour == int(twelve_hour_forcast[0]['DateTime'][11:13]):
        logger.info(f"{title} Current forcast = 1 hour forcast")
        return 
    
    #Collect hourly forcast data
    for hour in twelve_hour_forcast:
        temp = hour['Temperature']['Value']
        condition = get_condition_index(accu_weather_conditions,hour['WeatherIcon'])
        cloud_cov = hour["CloudCover"]
        res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})
        
    logger.info(f"Storing {cur_time.strftime('%Y-%m-%dT%H')} to {title} table")
    save_to_db(title, res)

def get_open_weather(location):
    #Open Weather lon & lat cords
    open_weather_api_key = os.environ['OPEN_WEATHER_API_KEY']
    locations = {"toronto": [43.6534817,-79.3839347], "thornhill": [43.8161477,-79.4245925],"innisfil": [44.3150892,-79.5461073], 'kingston': [44.230687,-76.481323]}
    cur_lat, cur_long = locations[location][0], locations[location][1]
    
    #Calling APIs
    four_day_hourly_forcast_url = "http://pro.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={lon}&appid={api_key}&units=metric&cnt=12"
    current_forcast_url = "http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    four_day_hourly_forcast = get_forcast(four_day_hourly_forcast_url.format(lat = cur_lat, lon = cur_long, api_key = open_weather_api_key))
    current_forcast = get_forcast(current_forcast_url.format(lat=cur_lat, lon=cur_long, api_key = open_weather_api_key))
    title = f'Open_Weather_{location}'
    res = []

    #If either forcast doesn't work, skip storing
    if four_day_hourly_forcast == None or current_forcast == None:
        logger.info(title +' | Error')
        return title + " | Error"
    else:
        four_day_hourly_forcast = four_day_hourly_forcast['list']

    #Collect current weather data
    cur_time = hour_rounder(datetime.fromtimestamp(current_forcast['dt'], tz=time_zone))
    temp = current_forcast['main']['temp']
    condition = get_condition_index(open_weather_conditions,current_forcast['weather'][0]['id'])
    cloud_cov = current_forcast['clouds']['all']

    res.append(cur_time.strftime('%Y-%m-%dT%H'))
    res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})

    #If the 1 hour forcast is "supposedly" trying to forcast for the current time
    if cur_time.hour == datetime.fromtimestamp(four_day_hourly_forcast[0]['dt'], tz=time_zone).hour:
        logger.info(f"{title} Current forcast = 1 hour forcast")
        return
    
    #Collect hourly forcast data
    for hour in four_day_hourly_forcast:
        temp = hour['main']['temp']
        condition = get_condition_index(open_weather_conditions,hour['weather'][0]['id'])
        cloud_cov = hour['clouds']['all']
        res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})
 
    logger.info(f"Storing {cur_time.strftime('%Y-%m-%dT%H')} to {title} table")
    save_to_db(title, res)
    
def get_weather_api(location):
    #Before new naming convention
    title = f'Weather_API_{location}' 
    res = []
    
    #WeatherAPI specific location naming convention
    if location in ['thornhill', 'kingston']:
        location += ' CA'

    #Calling API
    weather_api_key = os.environ['WEATHER_API_KEY']
    three_day_forcast_url = "http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=2&aqi=no&alerts=no"
    three_day_forcast = get_forcast(three_day_forcast_url.format(api_key=weather_api_key, location=location))
    
    #If forcast doesn't work, skip storing
    if three_day_forcast == None:
        logger.info(title +' | Error')
        return title + " | Error"
    else: 
        current, forcast = three_day_forcast['current'], three_day_forcast['forecast']['forecastday']

    #Get current hour
    today = datetime.now(tz=time_zone)
    cur_hour = today.hour
    
    #Collect current weather data
    cur_time = hour_rounder(datetime.fromtimestamp(current['last_updated_epoch'], tz=time_zone))
    temp = current['temp_c']
    condition = get_condition_index(weather_api_conditions,current["condition"]['code'])
    cloud_cov = current['cloud']

    res.append(cur_time.strftime('%Y-%m-%dT%H'))
    res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})   

    hours = forcast[0]['hour'][cur_hour+1:] + forcast[1]['hour']    #Only collect data after current time
    #If the 1 hour forcast is "supposedly" trying to forcast for the current time (probably impossible in this case but might as well just incase)
    if cur_time.hour == datetime.fromtimestamp(hours[0]['time_epoch'], tz=time_zone).hour:
        logger.info(f"{title} Current forcast = 1 hour forcast")
        return
    
    #Collect hourly forcast data
    for hour in hours[:12]:
        temp = hour['temp_c']
        condition = get_condition_index(weather_api_conditions, hour['condition']['code'])
        cloud_cov = hour['cloud']
        res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})
    logger.info(f"Storing {cur_time.strftime('%Y-%m-%dT%H')} to {title} table")
    save_to_db(title, res)
    
def save_to_db(table_name, data):
    date, hc, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12 = data
    new_item = {
        'Date': date, 
        'cur': hc,
        'f1': h1,
        'f2': h2,
        'f3': h3,
        'f4': h4,
        'f5': h5,
        'f6': h6,
        'f7': h7,
        'f8': h8,
        'f9': h9,
        'f10': h10,
        'f11': h11,
        'f12': h12,
        'forcasts': {}
        }
    
    new_item = json.loads(jsonDB.dumps(new_item))
    dynamodb.put_item(TableName = table_name, Item=new_item)
    logger.info(f"Successfully stored to {table_name}") 
    
def lambda_handler(event, context):
    locations = ['toronto', 'kingston', 'innisfil']
    for location in locations:
        get_weather_api(location)
        get_open_weather(location)
        get_accu_weather(location)
        
    response = {
        "statusCode": 200,
        "body": "yehaw"
    }

    return response