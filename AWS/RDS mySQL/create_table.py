import sys
import logging
import pymysql
from json import dumps, loads
import os

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

def lambda_handler(event, context):
    """
    This function creates a new RDS database table and writes records to it
    """
    function = event['Function']
    
    table_names = ['Weather_API_toronto', 'Weather_API_kingston', 'Weather_API_innisfil',
    'Open_Weather_toronto','Open_Weather_kingston', 'Open_Weather_innisfil',
    'Accu_Weather_toronto']
    
    if function == 'Create':
        for table_name in table_names:
            create_table = f" create table if not exists {table_name} ( " \
                "Date CHAR(13) NOT NULL, " \
                "cur varchar(255) NOT NULL, "\
                "`1` varchar(255) NOT NULL, "\
                "`2` varchar(255) NOT NULL, "\
                "`3` varchar(255) NOT NULL, "\
                "`4` varchar(255) NOT NULL, "\
                "`5` varchar(255) NOT NULL, "\
                "`6` varchar(255) NOT NULL, "\
                "`7` varchar(255) NOT NULL, "\
                "`8` varchar(255) NOT NULL, "\
                "`9` varchar(255) NOT NULL, "\
                "`10` varchar(255) NOT NULL, "\
                "`11` varchar(255) NOT NULL, "\
                "`12` varchar(255) NOT NULL, "\
                "forcasts varchar(255) NOT NULL, "\
                "PRIMARY KEY (Date))"
            s = dumps({'avg':0,'count':0})
            avg_string = f"insert into {table_name} (Date, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`) "\
                f"values('Averageforcst', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}')"
            with conn.cursor() as cur:
                cur.execute(create_table)
                cur.exccute(avg_string)
                conn.commit()
    elif function == 'Delete':
        for table_name in table_names:
            drop_table = f'DROP TABLE {table_name}'
            with conn.cursor() as cur:
                cur.execute(drop_table)
                conn.commit()
    elif function == 'Clear':
        for table_name in table_names:
            truncate_table = f'TRUNCATE TABLE {table_name};'
            s = dumps({'avg':0,'count':0})
            avg_string = f"insert into {table_name} (Date, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`) "\
                f"values('Averageforcst', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}', '{s}')"
            with conn.cursor() as cur:
                cur.execute(truncate_table)
                cur.execute(avg_string)
                conn.commit()            

    conn.commit()

    return f'Function: {function} exected'
    