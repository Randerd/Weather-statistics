import json
import os
import sys
import pymysql
import logging

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

table_names = ['Weather_API_toronto', 'Weather_API_kingston', 'Weather_API_innisfil',
    'Open_Weather_toronto','Open_Weather_kingston', 'Open_Weather_innisfil',
    'Accu_Weather_toronto']
    
def get_value(query):
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()
    return cur.fetchone()
    
def lambda_handler(event, context):
    ret = []
    for table_name in table_names:
        avgs = list(get_value(f'select * from {table_name} where Date = "Averageforcst"'))[2:-1]
        lst = [json.loads(avg)['avg'] for avg in avgs]
        lst2 = [json.loads(avg)['count'] for avg in avgs]
        ret.append([lst, lst2])
        print(table_name, lst)
    ret.append(['-']*12)    #missing accu weather kingston
    ret.append(['-']*12)    #missing accu weather innisfil
    return {
        'statusCode': 200,
        'headers': {
            # 'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            # 'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(ret)
    }
