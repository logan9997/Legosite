import psycopg2 as pc
from project_utils.environment_manager import Manager

DEV_credentials = Manager().get_database_credentials('local', development='True')
DEV_con = pc.connect(**DEV_credentials)
DEV_cursor = DEV_con.cursor()

HER_credentials = Manager().get_database_credentials('postgres', development='False')
HER_con = pc.connect(**DEV_credentials)
HER_cursor = HER_con.cursor()

def get_tables():


    sql = '''
        select tablename 
        from pg_tables 
        where schemaname='public' 
    '''

    DEV_cursor.execute(sql)
    tables = DEV_cursor.fetchall()
    return [t[0] for t in tables]

def extract_table_data(table):
    sql = f'''
        select *
        from "{table}"
    '''
    DEV_cursor.execute(sql)
    return DEV_cursor.fetchall()


def insert_table_data(table, data):
    for row in data[:1]:
        sql = f'''
            insert into "{table}" values {row}
        '''
        HER_cursor.execute(sql)


tables = get_tables()

for table in tables[:2]:
    data = extract_table_data(table)
    insert_table_data(table, data)