import psycopg2 as db

HOST = "ec2-35-169-9-79.compute-1.amazonaws.com"
DATABASE = "d9evsf0knvksog"
USER = "jalkrxxifnsfhv"
PASSWORD = 'b82b631a3b1139285895f94e3352bdc3082c951df34c4807f7b11c240937cd91'

conn = db.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD)
cursor = conn.cursor()

def test():
    cursor.execute("""
        SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'
    """)

    for table in cursor.fetchall():
        print(table)

    cursor.execute('select * from public."App_theme"')
    print(cursor.fetchall())


def truncate_all():
    talbes = [
        "App_item", "App_theme", "App_pieceparticipation", "App_portfolio",
        "App_price", "App_setparticipation", "App_theme", "App_user", "App_watchlist",
        "auth_group", "auth_group_permissions", "auth_permission", "auth_user", "auth_user_groups",
        "auth_user_user_permissions", "django_admin_log", "django_content_type", "django_migrations",
        "django_session"
    ]

    for table in talbes:
        cursor.execute(f'TRUNCATE "{table}" CASCADE')
        conn.commit()

    cursor.close()
    conn.close()

def main():
    truncate_all()



if __name__ == "__main__":
    main()
