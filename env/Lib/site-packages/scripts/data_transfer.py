import psycopg2 as pc
from project_utils.environment_manager import Manager

def get_data():
    credentials = Manager().get_database_credentials('local', development='True')
    con = pc.connect(**credentials)
    cursor = con.cursor()

    sql = '''
        select PR.*
        from "App_item" I, "App_price" PR
        where I.item_id = PR.item_id
            and I.item_id like 'sw%'
            and item_type = 'M'
            and (date='2023-01-24' or date='2023-05-26')
        
    '''
    cursor.execute(sql)
    missing_items = cursor.fetchall()

    return missing_items

def insert_items(items):
    credentials = Manager().get_database_credentials('postgres', development='False')
    print(credentials)
    con = pc.connect(**credentials)
    cursor = con.cursor()

    for item in items[::-1]:
        item = list(item)
        item[1] = str(item[1])
        sql = f'''
            insert into "App_price"
            values {tuple(item)}
        '''
        print(sql)
        try:
            cursor.execute(sql)
            con.commit()
        except:
            print(item[0], 'skipped')

missing_items = get_data()
insert_items(missing_items)