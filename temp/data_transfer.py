import psycopg2 as pc
from psycopg2.errors import UniqueViolation
from project_utils.environment_manager import Manager
from multiprocessing import Pool

DEV_credentials = Manager().get_database_credentials('local', development='True')
DEV_con = pc.connect(**DEV_credentials)
DEV_cursor = DEV_con.cursor()

HER_credentials = Manager().get_database_credentials('postgres', development='False')
HER_con = pc.connect(**HER_credentials)
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


def is_all_data_inserted(table):
    sql = f'''
        select *
        from "{table}"
    '''
    DEV_cursor.execute(sql)
    DEV_data = DEV_cursor.fetchall() 

    sql = f'''
        select *
        from "{table}"
    '''
    HER_cursor.execute(sql)
    HER_data = HER_cursor.fetchall() 

    if len(HER_data) == len(DEV_data):
        return True
    return False


def is_row_inserted(table, row):
    sql = f'''
        select *
        from "{table}"
    '''
    HER_cursor.execute(sql)
    data = HER_cursor.fetchall()
    pks = [d[0] for d in data]

    if row[0] in pks:
        return True
    return False


def insert_table_data(table, data):
    for row in data:
        if not is_row_inserted(table, row):
            sql = f'''
                insert into "{table}" values {row}
            '''
            print(sql)
            try:
                HER_cursor.execute(sql)
                HER_con.commit()
            except UniqueViolation:
                pass
    

tables = get_tables()

def main():
    for table in tables[:2]:
        if not is_all_data_inserted(table):
            data = extract_table_data(table)
            insert_table_data(table, data)


if __name__ == '__main__':
    main()