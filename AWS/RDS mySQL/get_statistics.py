import sys
import logging
import pymysql
from json import dumps, loads
import math
from datetime import datetime, timedelta
import os
from zoneinfo import ZoneInfo

time_zone = ZoneInfo("Canada/Eastern")

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
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit(1)

logger.info("SUCCESS: Connection to RDS for MySQL instance succeeded")

def get_value(query):
    #go into sql database and get value from data and time
    # query = f'select {key} from {table_name}'
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()
    return cur.fetchone()

def update_table(query):
    logger.info(f"Update: {query}")
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()

def date_format(date: datetime):
    return date.strftime('%Y-%m-%dT%H')

def new_hour(cur_hour, diff):
    new_hour = cur_hour-diff
    return new_hour if new_hour>0 else new_hour-24

def temp_score(temp):
    return (2**(temp/7)) - 1

def cond_score(cond):
    return (2**(cond/3)) - 1

def cloud_score(cloud):
    return (2**(cloud/105)) - 1

def hour_accuracy(temp, cond, cloud):
    # return round(math.exp( -(temp_score(temp) + cond_score(cond))**2) + math.exp(-(cloud_score(cloud))**2) , 4)*50
    return round(math.exp( -(temp_score(temp) + cond_score(cond))**2) + math.exp(-(cloud_score(cloud))**2) - 1 , 4)*100

def date_accuracy(max, min, cond):
     return round(math.exp( -(temp_score(max)+ temp_score(min) + cond_score(cond))**2) , 4)*100

def lambda_handler(event, context):
    table_names = ['Weather_API_toronto', 'Weather_API_kingston', 'Weather_API_innisfil',
    'Open_Weather_toronto','Open_Weather_kingston', 'Open_Weather_innisfil',
    'Accu_Weather_toronto']
    # table_names = ['Open_Weather_toronto']
    cur_date = datetime.now(tz=time_zone)# - timedelta(hours = 1)        #asdasdadasdasda
    fcur_date = date_format(cur_date)
    for table_name in table_names:
        try:
            logger.info(f"Calculating statistics for {table_name} at {fcur_date}")
            avgs = list(get_value(f'select * from {table_name} where Date = "Averageforcst"'))
            cur_weather = get_value(f'select cur from {table_name} where Date = "{fcur_date}"')
            cur_weather = loads(cur_weather[0])
        except:
            logger.info(f"No Data entry for {fcur_date}" in {table_name})
            continue
        if cur_weather['Condition'] == -1:
            logger.info(f"{fcur_date} missing condition data")
            continue
        
        for hour in range(1,13): 
            new_date = cur_date - timedelta(hours = hour)
            fnew_date = date_format(new_date)
            try:
                logger.info(f"Calculating statistics for {table_name} at {fcur_date} hour {hour}")
                cur_forcast, forcast_scores = get_value(f'select `{hour}`, forcasts from {table_name} where Date = "{fnew_date}"')
                cur_forcast, forcast_scores = loads(cur_forcast), loads(forcast_scores)
            except:
                logger.info(f'Forcast {hour} does not exist for {fnew_date} in {table_name}')
                # print(f'Hour {new_date.hour} does not exist')
                continue
            
            if cur_forcast['Condition'] == -1:
                logger.info(f"{fnew_date} missing condition data")
                continue

            t_diff = round(abs(cur_weather['Temp'] - cur_forcast['Temp']),2)
            d_diff = round(abs(cur_weather['Condition'] - cur_forcast['Condition']),2)
            c_diff = round(abs(cur_weather['Cloud Cov'] - cur_forcast['Cloud Cov']),2)
            c_diff = 0
            score = round(hour_accuracy(t_diff, d_diff, c_diff),4)
            forcast_scores[str(hour)] = score
            update_table(f"UPDATE {table_name} SET forcasts = '{dumps(forcast_scores)}' WHERE Date = '{fnew_date}'")
            # print(f'Forcast: {hour} h\t Score: {score}\t Temp Diff: {t_diff}\t Cond Diff: {d_diff}\t Cloud Diff: {c_diff}')
            forcast_avg = loads(avgs[hour+1])
            cur_avg, cur_count = forcast_avg['avg'], forcast_avg['count']
            cur_count+=1
            new_avg = round(cur_avg + (score-cur_avg) / cur_count,2)
            avgs[hour+1] = dumps({'avg':new_avg, 'count':cur_count})

        update_avg_query = f"UPDATE {table_name} SET `{1}` = '{avgs[1+1]}'"
        for hour in range(2,13):
            update_avg_query+= f", `{hour}` = '{avgs[hour+1]}'"
        update_avg_query += " where Date = 'Averageforcst'"
        update_table(update_avg_query)
        
        # update_avg_query = f"UPDATE {table_name} SET `{1}` = '{dumps({'avg':0, 'count':0})}'"
        # for hour in range(2,13):
        #     update_avg_query+= f", `{hour}` = '{dumps({'avg':0, 'count':0})}'"
        # update_avg_query += " where Date = 'Averageforcst'"
        # update_table(update_avg_query)

