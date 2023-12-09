import os
import sys
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pymysql
from json import dumps, loads
import logging
    
time_zone = ZoneInfo("Canada/Eastern")

accu_weather_conditions = {
    1: {1,2,3,32,33,34,35},
    2: {4,5,6,36,37,38},
    3: {7,8,11},
    4: {12,13,14,18,22,23,39,40,44},
    5: {15,16,17,19,20,21,24,25,26,41,42,43},
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

# rds settings
user_name = os.environ['USER_NAME']
password = os.environ['PASSWORD']
rds_proxy_host = os.environ['RDS_PROXY_HOST']
db_name = os.environ['DB_NAME']

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.
try:
    conn = pymysql.connect(host=rds_proxy_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    print("ERROR: Unexpected error: Could not connect to MySQL instance.")
    print(e)
    sys.exit(1)
    
logger.info("SUCCESS: Connection to RDS for MySQL instance succeeded")
# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.

def get_forcast(weburl):
    res = requests.get(weburl)
    return res.json() if res.status_code<300 else None

def hour_rounder(date):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (date.replace(second=0, microsecond=0, minute=0, hour=date.hour)
               +timedelta(hours=date.minute//30))

def get_condition_index(condition_index, cond):
    for value, conditions in condition_index.items():
        if cond in conditions:
            return value
    logger.info(f"No condition for {condition_index}, condition {cond}")
    return -1

def get_accu_weather(location):
    accu_weather_api_key = os.environ['ACCU_WEATHER_API_KEY']
    locations = {"toronto": "55488", "thornhill": "1365404","innisfil": "55080", 'kingston':'214971'}

    twelve_hour_forcast_url = "http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{location}?apikey={api_key}&metric=true&details=true"
    twelve_hour_forcast = get_forcast(twelve_hour_forcast_url.format(location = locations[location], api_key=accu_weather_api_key))
    current_forcast_url = "http://dataservice.accuweather.com/currentconditions/v1/{location}?apikey={api_key}&details=true"
    current_forcast = get_forcast(current_forcast_url.format(location = locations[location], api_key = accu_weather_api_key))
    title = f'Accu_Weather_{location}'
    res = []

    if twelve_hour_forcast == None or current_forcast == None:
        return title +' | Error'
    else:
        current_forcast = current_forcast[0]

    # cur_time = current_forcast['LocalObservationDateTime'][:16]
    cur_time = hour_rounder(datetime.fromtimestamp(current_forcast['EpochTime'], tz=time_zone))
    temp = current_forcast['Temperature']['Metric']['Value']
    condition = get_condition_index(accu_weather_conditions, current_forcast['WeatherIcon'])
    cloud_cov = current_forcast['CloudCover']

    res.append(cur_time.strftime('%Y-%m-%dT%H'))
    res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})
    # title+= f'\nCurrent Forcast: \nHour: {time}, Temp: {temp}, Condition: {condition}, Cloud Coverage: %{cloud_cov}\n'
    # title+= f'\nHourly Forcast:\n'
    print(cur_time.hour, twelve_hour_forcast[0]['DateTime'][11:13])
    if cur_time.hour == int(twelve_hour_forcast[0]['DateTime'][11:13]):
        logger.info(f"{title} Current forcast = 1 hour forcast")
        return 
    
    for hour in twelve_hour_forcast:
        # time = hour['DateTime'][:13]
        temp = hour['Temperature']['Value']
        condition = get_condition_index(accu_weather_conditions,hour['WeatherIcon'])
        cloud_cov = hour["CloudCover"]
        res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})
        # title+=f'Hour: {time}, Temp: {temp}, Condition: {condition}, Cloud Cov: %{cloud_cov}\n'
    # title += '\n' + '-'*20
    logger.info(f"Storing {cur_time.strftime('%Y-%m-%dT%H')} to {title} table")
    save_to_db(title, res)

def get_open_weather(location):
    open_weather_api_key = os.environ['OPEN_WEATHER_API_KEY']
    locations = {"toronto": [43.6534817,-79.3839347], "thornhill": [43.8161477,-79.4245925],"innisfil": [44.3150892,-79.5461073], 'kingston': [44.230687,-76.481323]}
    cur_lat, cur_long = locations[location][0], locations[location][1]
    
    four_day_hourly_forcast_url = "http://pro.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={lon}&appid={api_key}&units=metric&cnt=12"
    current_forcast_url = "http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    four_day_hourly_forcast = get_forcast(four_day_hourly_forcast_url.format(lat = cur_lat, lon = cur_long, api_key = open_weather_api_key))
    current_forcast = get_forcast(current_forcast_url.format(lat=cur_lat, lon=cur_long, api_key = open_weather_api_key))
    title = f'Open_Weather_{location}'
    res = []

    if four_day_hourly_forcast == None or current_forcast == None:
        return title + " | Error"
    else:
        four_day_hourly_forcast = four_day_hourly_forcast['list']
        
    # time = datetime.fromtimestamp(current_forcast['dt'], tz=time_zone).strftime('%H:%M:%S')
    cur_time = hour_rounder(datetime.fromtimestamp(current_forcast['dt'], tz=time_zone))
    temp = current_forcast['main']['temp']
    condition = get_condition_index(open_weather_conditions,current_forcast['weather'][0]['id'])
    cloud_cov = current_forcast['clouds']['all']

    res.append(cur_time.strftime('%Y-%m-%dT%H'))
    res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})
    # title+=f'\nCurrent Weather: \nHour: {time}, Temp: {temp}, Condition: {condition}, Cloud Cov: %{cloud_cov}\n'
    # title+=f'\nHourly Forcast:\n'
    print(cur_time.hour,datetime.fromtimestamp(four_day_hourly_forcast[0]['dt'], tz=time_zone).hour)
    if cur_time.hour == datetime.fromtimestamp(four_day_hourly_forcast[0]['dt'], tz=time_zone).hour:
        logger.info(f"{title} Current forcast = 1 hour forcast")
        return
    
    for hour in four_day_hourly_forcast:
        # time = datetime.fromtimestamp(hour['dt'], tz=time_zone).strftime('%Y-%m-%d %H')
        temp = hour['main']['temp']
        condition = get_condition_index(open_weather_conditions,hour['weather'][0]['id'])
        cloud_cov = hour['clouds']['all']
        res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})
        # title+=f'Hour: {time}, Temp: {temp}, Condition: {condition}, Cloud Cov: %{cloud_cov}\n'
    # title += '\n' + '-'*20
    logger.info(f"Storing {cur_time.strftime('%Y-%m-%dT%H')} to {title} table")
    save_to_db(title, res)
    
def get_weather_api(location):
    title = f'Weather_API_{location}'
    res = []
    if location in ['thornhill', 'kingston']:
        location += ' CA'
    weather_api_key = os.environ['WEATHER_API_KEY']
    three_day_forcast_url = "http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=2&aqi=no&alerts=no"
    three_day_forcast = get_forcast(three_day_forcast_url.format(api_key=weather_api_key, location=location))
    
    if three_day_forcast == None:
        return title + " | Error"
    else: 
        current, forcast = three_day_forcast['current'], three_day_forcast['forecast']['forecastday']

    today = datetime.now(tz=time_zone)
    cur_hour = today.hour

    cur_time = hour_rounder(datetime.fromtimestamp(current['last_updated_epoch'], tz=time_zone))
    temp = current['temp_c']
    condition = get_condition_index(weather_api_conditions,current["condition"]['code'])
    # time = current['last_updated'][:-3]
    cloud_cov = current['cloud']

    res.append(cur_time.strftime('%Y-%m-%dT%H'))
    res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})   
    # res+=f'\nCurrent Forcast:\nTime: {cur_time}, Temp: {cur_temp}, Condition: {cur_condition}, Cloud Cov: %{cur_cloud_cov}\n'
    # res+=f'\nHourly Forcast:\n'
    hours = forcast[0]['hour'][cur_hour+1:] + forcast[1]['hour']
    print(cur_time.hour,datetime.fromtimestamp(hours[0]['time_epoch'], tz=time_zone).hour)
    if cur_time.hour == datetime.fromtimestamp(hours[0]['time_epoch'], tz=time_zone).hour:
        logger.info(f"{title} Current forcast = 1 hour forcast")
        return
    
    for hour in hours[:12]:
        # time = hour['time'][:-3]
        temp = hour['temp_c']
        condition = get_condition_index(weather_api_conditions, hour['condition']['code'])
        cloud_cov = hour['cloud']
        res.append({'Temp': temp, 'Condition': condition, 'Cloud Cov': cloud_cov})
        # res+=f'Hour: {time}, Temp: {temp}, Condition: {condition}, Cloud Cov: %{cloud}\n'
    logger.info(f"Storing {cur_time.strftime('%Y-%m-%dT%H')} to {title} table")
    save_to_db(title, res)
    
def save_to_db(table_name, data):
    date, hc, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12 = data
    forcasts = {}
    sql_string = f"insert into {table_name} (Date, cur, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, forcasts) "\
    f"values('{date}', '{dumps(hc)}', '{dumps(h1)}', '{dumps(h2)}', '{dumps(h3)}', '{dumps(h4)}', '{dumps(h5)}', '{dumps(h6)}', '{dumps(h7)}', '{dumps(h8)}', '{dumps(h9)}', '{dumps(h10)}', '{dumps(h11)}', '{dumps(h12)}', '{dumps(forcasts)}')"
    
    with conn.cursor() as cur:
        cur.execute(sql_string)
        conn.commit()
    logger.info(f"Successfully stored to {table_name}")
    return 
    
def lambda_handler(event, context):
    locations = ['toronto', 'kingston', 'innisfil']
    for location in locations:
        print(get_weather_api(location))
        print(get_open_weather(location))
    
    get_accu_weather('toronto')
    response = {
        "statusCode": 200,
        "body": "yehaw"
    }

    return response
