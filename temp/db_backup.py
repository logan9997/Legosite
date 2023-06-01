import psycopg2
from project_utils.environment_manager import Manager
import pathlib

credentials = Manager().get_database_credentials('local', development='True')
con = psycopg2.connect(**credentials)
cursor = con.cursor()

PATH = pathlib.Path(__file__).parent.parent

sql = '''
    select tablename 
    from pg_tables 
    where schemaname='public' 
'''

cursor.execute(sql)
tables = [t[0] for t in cursor.fetchall()]

for table in tables:
    sql = rf'''
        copy (select * from "{table}") 
        to '{PATH}\csv\{table}.csv' 
        DELIMITER ',' CSV HEADER;
    '''
    cursor.execute(sql)

