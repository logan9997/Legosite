import datetime
import psycopg2
import os

class DatabaseManagment():

    def __init__(self) -> None:
        DEVELOPMENT = True

        if not DEVELOPMENT:
            file_name = "./heroku_database_credentials.txt"
        else:
            file_name = "./localhost_database_credentials.txt"
            if not os.path.exists(file_name):
                file_name = "../localhost_database_credentials.txt"

        with open(file_name, "r") as file:
            credentials = {param.rstrip("\n").split("=")[0] : param.rstrip("\n").split("=")[1]  for param in file.readlines()}
        self.con = psycopg2.connect(**credentials)
        self.cursor = self.con.cursor()
        

    def SELECT(self, sql, **kwargs):
        self.cursor.execute(sql)
        if kwargs.get("fetchone"):
            return self.cursor.fetchone()
        return self.cursor.fetchall()
    

    def add_pieces(self, info):
        sql = f'''
            INSERT INTO "App_piece"('piece_name', 'piece_id', 'type') 
            VALUES ('{info["piece_name"]}', '{info["piece_id"]}', '{info["type"]}')
        '''
        self.cursor.execute(sql)
        self.con.commit()


    def add_piece_participation(self, info):
        sql = f'''
            INSERT INTO "App_pieceparticipation" ('item_id', 'piece_id', 'quantity', 'colour_id') 
            VALUES ('{info["item_id"]}', '{info["piece_id"]}', '{info["quantity"]}', '{info["colour_id"]}')
        '''
        self.cursor.execute(sql)
        self.con.commit()   


    def add_price_info(self, item) -> None:
        today = datetime.date.today().strftime('%Y-%m-%d')
        try:
            self.cursor.execute(f"""
                INSERT INTO "App_price" (
                    item_id,date,avg_price,
                    min_price,max_price,total_quantity
                )
                VALUES
                (
                    '{item["item"]["no"]}', '{today}', '{round(float(item["avg_price"]), 2)}',
                    '{round(float(item["min_price"]),2)}', '{round(float(item["max_price"]),2)}',
                    '{item["total_quantity"]}'
                )
            """)
        except psycopg2.IntegrityError:
            pass
        self.con.commit() 


    def add_set_participation(self, info):
        sql = f'''
            INSERT INTO "App_setparticipation" ('quantity', 'item_id', 'set_id')
            VALUES ('{info["quantity"]}', '{info["item_id"]}', '{info["set_id"]}') 
        '''
        self.cursor.execute(sql)
        self.con.commit()


    def get_all_piece_ids(self):
        sql = '''
            SELECT piece_id
            FROM App_piece
        '''
        return self.SELECT(sql)
    

    def get_todays_price_records(self):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        sql = f'''
            SELECT item_id
            FROM "App_price"
            WHERE date = '{today}'
        '''
        return self.SELECT(sql)

    def get_item_subsets(self, item_id) -> list[tuple[str]]:
        sql = f'''
            SELECT P.piece_id, piece_name, colour_id, quantity
            FROM "App_piece"P, "App_pieceparticipation" PP
            WHERE P.piece_id = PP.piece_id
                AND item_id = '{item_id}'
        '''
        return self.SELECT(sql)
    

    def get_item_supersets(self, item_id):
        sql = f'''
            SELECT DISTINCT ON (I.item_id) I.item_id, item_name, year_released, quantity
            FROM "App_item" I, "App_setparticipation" SP
            WHERE I.item_id in (
                SELECT set_id
                FROM "App_setparticipation" SP 
                WHERE item_id = '{item_id}'
            )
                AND SP.set_id = I.item_id
        '''
        return self.SELECT(sql)


    def get_all_items(self) -> list[str]:
        sql = '''
            SELECT item_id
            FROM "App_price"
            GROUP BY item_id
        '''
        return self.SELECT(sql)

    def check_for_todays_date(self) -> int:
        today = datetime.date.today()
        sql = f'''
            SELECT count(*)
            FROM "App_price"
            WHERE date = '{today}'
        '''
        return self.SELECT(sql)


    def theme_item_ids(self):
        sql = '''
            SELECT DISTINCT ON (theme_path) I.item_id
            FROM "App_theme" TH, "App_item" I
            WHERE TH.item_id = I.item_id
                AND item_type = 'S'
        '''
        return self.SELECT(sql)

    
    def get_biggest_trends(self, change_metric, **kwargs) -> list[str]:
        min_date_sql = kwargs.get("min_date", "")
        if "min_date" in kwargs:
            min_date_sql = f"WHERE date >= '{min_date_sql}'"
    
        max_date_sql = kwargs.get("max_date", "")
        if "max_date" in kwargs:
            max_date_sql = f"AND date <= '{max_date_sql}'"
        
        limit_sql = kwargs.get("limit", "")
        if "limit" in kwargs:
            limit_sql = f"LIMIT {limit_sql}"

        sql = f'''
            SELECT DISTINCT ON (I.item_id, Change) I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity, ABS(ROUND(CAST(
                ((
                    SELECT {change_metric}
                    FROM "App_price" P2
                    WHERE P2.item_id = P1.item_id
                        AND (I.item_id, date) = ANY (SELECT DISTINCT ON (item_id) item_id, min(date) FROM "App_price" GROUP BY item_id)  
                ) 
                - {change_metric}) *-1.0 /  NULLIF(
                (
                    SELECT {change_metric}
                    FROM "App_price" P2
                    WHERE P2.item_id = P1.item_id
                        AND (I.item_id, date) = ANY (SELECT DISTINCT ON (item_id) item_id, min(date) FROM "App_price" GROUP BY item_id) 
                )
                ,0) 
            AS numeric)* 100,2)) as Change

            FROM "App_price" P1, "App_item" I
            WHERE I.item_id = P1.item_id 
                AND (I.item_id, date) = any (
                    SELECT DISTINCT ON (item_id) item_id, max(date) 
                    FROM "App_price" P2
                    {min_date_sql}  
                    {max_date_sql} 
                    GROUP BY item_id
                )
            ORDER BY Change DESC, I.item_id
            {limit_sql}
        '''
        return self.SELECT(sql)
    

    def get_parent_themes(self) -> list[str]:
        sql = '''
            SELECT REPLACE(REPLACE(theme_path, '/', ''), ' ', '-')
            FROM "App_item", "App_theme"
            WHERE theme_path NOT LIKE '%~%'
                AND item_type = 'M'
                AND "App_item".item_id = "App_theme".item_id
            GROUP BY theme_path
        '''
        return self.SELECT(sql)
    

    def get_theme_items(self, theme_path, sort_field) -> list[str]:
        distinct = f"(I.item_id, {sort_field[0]})"
        if sort_field[0] == "item_id":
            sort_field[0] = "I.item_id"
            distinct = "(I.item_id)"
        sql = f'''
            SELECT DISTINCT ON {distinct} I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity
            FROM "App_item" I, "App_theme" T, "App_price" P1
            WHERE T.item_id = I.item_id
                AND I.item_id = P1.item_id
                AND theme_path = '{theme_path}'
                AND item_type = 'M'
                AND (I.item_id, date) = any (
                    SELECT DISTINCT ON (item_id) item_id, max(date) 
                    FROM "App_price" P2  
                    GROUP BY item_id
                )
            ORDER BY {sort_field[0]} {sort_field[1]}
        '''
        return self.SELECT(sql)      



    def get_star_wars_sets(self):
        sql = '''
            SELECT I.item_id
            FROM "App_item" I, "App_theme" T
            WHERE I.item_id = T.item_id
                AND item_type = 'S'
                AND theme_path = 'Star_Wars'
            GROUP BY I.item_id
        '''
        return self.SELECT(sql)
    

    def get_item_metric_changes(self, item_id, change_metric, **kwargs):
        min_date = kwargs.get("min_date", f"""(SELECT MIN(date) FROM "App_price" WHERE item_id = '{item_id}')""")     
        max_date = kwargs.get("max_date", f"""(SELECT MAX(date) FROM "App_price" WHERE item_id = '{item_id}')""")      


        sql = f'''
            SELECT ROUND(CAST((
                (SELECT {change_metric}
                    FROM "App_price" P2
                    WHERE P2.ITEM_ID = P1.ITEM_ID
                        AND I.ITEM_ID = '{item_id}'
                        AND date = {min_date} ) - {change_metric}) * - 1.0 /
                NULLIF((SELECT {change_metric}
                    FROM "App_price" P2
                    WHERE P2.ITEM_ID = P1.ITEM_ID
                        AND I.ITEM_ID = '{item_id}'
                        AND date = {min_date}), 0) * 100 AS numeric),2)
            FROM "App_price" P1,"App_item" I
            WHERE I.ITEM_ID = P1.ITEM_ID
                AND I.ITEM_ID = '{item_id}'
                AND date = {max_date}
            '''
        return self.SELECT(sql, fetchone=True)[0]


    def most_recent_set_appearance(self, item_id):
        sql = f'''
            SELECT year_released
            FROM "App_setparticipation" SP, "App_item" I
            WHERE SP.set_id = I.item_id
            AND year_released = (
                SELECT MAX(year_released)
                FROM "App_item" I, "App_setparticipation" SP
                WHERE SP.set_id = I.item_id
                    AND SP.item_id = '{item_id}'
            )
            AND SP.item_id = '{item_id}'
            GROUP BY I.item_id
        '''
        result = self.SELECT(sql, fetchone=True)
        if result == None:
            return None
        return result[0]


    def insert_year_released(self, year_released, item_id) -> None:
        self.cursor.execute(f'''
            UPDATE "App_item"
            SET year_released = '{year_released}'
            WHERE item_id = '{item_id}'
        ''')
        self.con.commit()


    def get_item_info(self, item_id, change_metric) -> list[str]:
        sql = f'''
            SELECT I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity, (
                (SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND I.item_id = '{item_id}'
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                        WHERE item_id = '{item_id}'
                    ) 
                ) - ({change_metric}) *-1.0) / NULLIF((
                SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND I.item_id = '{item_id}'
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                        WHERE item_id = '{item_id}'
                    )
            ) * 100, 0)

            FROM "App_price" P1, "App_item" I
            WHERE I.item_id = P1.item_id 
                AND I.item_id = '{item_id}'
                AND date = (
                    SELECT max(date)
                    FROM "App_price"
                    WHERE item_id = '{item_id}'
                ) 
            
        '''
        return self.SELECT(sql)


    def get_sub_themes(self, parent_theme):
        sql = f'''
            SELECT REPLACE(theme_path, '{parent_theme}~', '')
            FROM "App_theme", "App_item"
            WHERE "App_theme".item_id = "App_item".item_id
                AND theme_path LIKE '{parent_theme}_%'
            GROUP BY theme_path
        '''
        return self.SELECT(sql)


    def get_starwars_ids(self) -> list[str]:
        sql = '''
            SELECT item_id
            FROM "App_item"
            WHERE item_type = 'M'
                AND item_id LIKE 'sw%'
        '''
        return self.SELECT(sql)


    def fetch_theme_details(self) -> list[str]:
        sql = '''
            SELECT item_type, theme_path
            FROM "App_item" I, "App_theme" T
            WHERE I.item_id = T.item_id
        '''
        return self.SELECT(sql)


    def add_theme_details(self, theme_details, item_type) -> None:
        for item in theme_details[item_type]:
            if theme_details["path"] not in self.get_item_themes(item):
                self.cursor.execute(f'''
                    INSERT INTO "App_theme" ("theme_path", "item_id") VALUES ('{theme_details["path"]}', '{item}')
                ''')
                self.con.commit()


    def get_user_items(self, user_id, view) -> list[str]:

        print(view)
        sql_select = "SELECT DISTINCT ON (I.item_id) _view1.item_id, item_name, year_released, item_type,avg_price, min_price, max_price, total_quantity"
        if view == "portfolio":
            sql_select += f''',
                (SELECT COUNT(*) FROM "App_portfolio" P2 WHERE user_id = 1 AND condition = 'N' AND _view1.item_id = P2.item_id GROUP BY P2.item_id),
                (SELECT COUNT(*) FROM "App_portfolio" P2 WHERE user_id = 1 AND condition = 'U' AND _view1.item_id = P2.item_id GROUP BY P2.item_id)
            '''

        sql = f'''
            {sql_select}
            FROM "App_{view}" _view1, "App_item" I, "App_price" P
            WHERE user_id = {user_id}
                AND (date, _view1.item_id) IN (SELECT MAX(date), item_id FROM "App_price" GROUP BY date, item_id)
                AND I.item_id = _view1.item_id 
                AND I.item_id = P.item_id
            
        '''
        return self.SELECT(sql)


    def is_item_in_user_items(self, user_id, view, item_id) -> bool:

        if view == "portfolio":
            sql_select = "SELECT condition, COUNT(*)" 
            sql_group = "GROUP BY condition"
        else:
            sql_select = "SELECT item_id" 
            sql_group = ""

        sql = f'''
            {sql_select}
            FROM "App_{view}"
            WHERE user_id = {user_id}
                AND item_id = '{item_id}'
            {sql_group}
        '''
        
        return self.SELECT(sql)



    def portfolio_total_item_price(self, user_id) -> list[str]:
        sql = f'''
            SELECT ROUND(avg_price * PO.quantity, 2), I.item_id, condition
            FROM "App_portfolio" PO, "App_price" PR, "App_item" I
            WHERE PO.user_id = {user_id}
                AND PO.item_id = I.item_id
                AND I.item_id = PR.item_id
            GROUP BY I.item_id, condition
        '''
        return self.SELECT(sql)


    def user_items_total_price(self, user_id, metric, view) -> list[str]:
        sql = f'''
        SELECT ROUND(CAST(SUM({metric}) AS numeric), 2)
        FROM "App_{view}" _view, "App_item" I, "App_price" P
        WHERE user_id = {user_id}
            AND (I.item_id, date) = any (
                    SELECT DISTINCT ON (item_id) item_id, max(date) 
                    FROM "App_price" P2  
                    GROUP BY item_id
                )
            AND I.item_id = _view.item_id 
            AND I.item_id = P.item_id
        '''
        result = self.SELECT(sql, fetchone=True)[0]
        if result == None:
            return 0.0
        return result


    def update_portfolio_item_quantity(self, user_id, item_id, condition, quantity) -> None:
        self.cursor.execute(f'''
            UPDATE App_portfolio
            SET quantity = quantity + {quantity}
            WHERE item_id = '{item_id}'
                AND user_id = {user_id}
                AND condition = '{condition}'
        ''')
        self.con.commit()


    def get_portfolio_item_quantity(self, item_id, condition, user_id) -> int:
        sql = f'''
            SELECT COUNT(*)
            FROM "App_portfolio"
            WHERE item_id = '{item_id}'
                AND condition = '{condition}'
                AND user_id = '{user_id}'
        '''
        return int(self.SELECT(sql)[0][0])


    def get_portfolio_price_trends(self, user_id) -> list[str]:
        sql = f'''
            SELECT date, ROUND(CAST(SUM(avg_price * quantity) AS numeric), 2)
            FROM "App_portfolio" PO, "App_price" PR, "App_item" I
            WHERE user_id = {user_id}
                AND PO.item_id = I.item_id
                AND PR.item_id = I.item_id
            GROUP BY date
        '''
        return self.SELECT(sql)


    def biggest_portfolio_changes(self, user_id, metric) -> list[str]:
        sql = f'''
            SELECT DISTINCT ON (I.item_id) I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity, ROUND(CAST(
                (
                    SELECT {metric}
                    FROM "App_price" P1
                    WHERE (I.item_id, date) = any (
                        SELECT DISTINCT ON (item_id) item_id, max(date) 
                        FROM "App_price" P2  
                        GROUP BY item_id
                    )
                    AND user_id = {user_id}
                    AND P1.item_id = I.item_id
                    AND I.item_id = PO.item_id
                ) 
                - 
                (
                    SELECT {metric}
                    FROM "App_price" P1
                    WHERE (I.item_id, date) = any (
                        SELECT DISTINCT ON (item_id) item_id, min(date) 
                        FROM "App_price" P2  
                        GROUP BY item_id
                    )
                    AND user_id = {user_id}
                    AND P1.item_id = I.item_id
                    AND I.item_id = PO.item_id
                )
            AS numeric), 2)

            FROM "App_price" P2 , "App_portfolio" PO, "App_item" I
            WHERE user_id = {user_id}
                AND PO.item_id = I.item_id
                AND I.item_id = P2.item_id
        '''
        return self.SELECT(sql)


    def biggest_theme_trends(self, change_metric) -> list[str]:
        sql = f'''
            SELECT DISTINCT ON (theme_path) theme_path, ROUND(CAST((
            (
                SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                    ) 
            ) - {change_metric}) *-1.0 /  (
            (
                SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                    ) 
                ) + 0.00001) * 100
            AS numeric) ,2)
            FROM "App_price" P1, "App_item" I, "App_theme" T
            WHERE I.item_id = P1.item_id 
                AND T.item_id = I.item_id
                AND (I.item_id, date) = any (
                    SELECT DISTINCT ON (item_id) item_id, max(date) 
                    FROM "App_price" P2  
                    GROUP BY item_id
                )          
        '''
        return self.SELECT(sql)

    
    def get_portfolio_items_condition(self, user_id) -> list[str]:
        sql = f'''
            SELECT item_id, condition
            FROM "App_portfolio"
            WHERE user_id = {user_id}
        '''
        return self.SELECT(sql)


    def total_portfolio_price_trend(self, user_id) -> list[str]:
        sql = f'''
            SELECT SUM(max_price), date
            FROM "App_price" price, "App_portfolio" portfolio, "App_item" item, "App_user" user
            WHERE user.user_id = {user_id}
                AND price.item_id = item.item_id
                AND item.item_id = portfolio.item_id
                AND portfolio.user_id = user.user_id
            GROUP BY date
        '''
        return self.SELECT(sql)


    def get_all_itemIDs(self) -> list[str]:
        sql = '''
            SELECT item_id
            FROM "App_item"
            WHERE item_id LIKE 'sw%' 
                AND item_type = 'M'
        '''
        return [_item[0] for _item in self.SELECT(sql)]


    def insert_item_info(self, item_info) -> None:
        type_convert = {"MINIFIG":"M", "SET":"S"}
        self.cursor.execute(f'''
            INSERT INTO "App_item"
            ("item_id", "item_name", "year_released", "item_type", "views")
            VALUES ('{item_info["no"]}', '{item_info["name"].replace("'", "")}', '{item_info["year_released"]}', '{type_convert[item_info["type"]]}', 0)
        ''')
        self.con.commit()


    def add_to_user_items(self, user_id, item_id, view, date_added, **portfolio_args) -> None:
        
        
        sql_fields = "(user_id, item_id, date_added"
        sql_values = f"VALUES ({user_id},'{item_id}','{date_added}'"

        if view == "portfolio":
            condition = portfolio_args["condition"]
            bought_for = portfolio_args["bought_for"]

            sql_fields += ",condition, bought_for)"
            sql_values += f",'{condition}', {bought_for})"
        else:
            sql_fields += ")"
            sql_values += ")"

        self.cursor.execute(f'''
            INSERT INTO "App_{view}"
            {sql_fields}
            {sql_values}
        ''')
        self.con.commit()


    def get_item_graph_info(self,item_id, metric, **kwargs) -> list[str]:
        if kwargs.get("user_id") != -1 and kwargs.get("view", "item") != "item":
            sql = f'''
                SELECT {metric}, date
                FROM "App_price" P, "App_{kwargs.get("view")}" _view, "App_item" I
                WHERE _view.user_id = {kwargs.get("user_id", -1)}
                    AND I.item_id = '{item_id}'
                    AND P.item_id = I.item_id
                    AND I.item_id = _view.item_id
                GROUP BY I.item_id, P.date
                ORDER BY date ASC
            '''
        else:
            sql = f'''
                SELECT {metric}, date
                FROM "App_price" P, "App_item" I
                WHERE I.item_id = '{item_id}'
                    AND P.item_id = I.item_id
                GROUP BY {metric}, I.item_id, P.date
                ORDER BY date ASC
                '''        
        return self.SELECT(sql)
    

    def get_sub_theme_set(self ,theme_path:str, sub_theme_indent:int):
        for char in ["/", " "]:
            if char in theme_path:
                theme_path = theme_path.replace(char, "~")

        sql = f'''
            SELECT DISTINCT ON (theme_path) theme_path, I.item_id
            FROM "App_theme" T, "App_item" I
            WHERE T.item_id = I.item_id
                AND item_type = 'S'
                AND I.item_id IN (
                    SELECT DISTINCT ON (theme_path) I.item_id
                    FROM "App_theme" TH, "App_item" I
                    WHERE TH.item_id = I.item_id
                        AND item_type = 'S'
                )
                AND theme_path LIKE '{theme_path}%'
                AND LENGTH(theme_path) - LENGTH(REPLACE(theme_path, '~', '')) = {sub_theme_indent}
        '''

        result = self.SELECT(sql)
        if result == None:
            return 'No-Image'
        return result


    def parent_themes(self, user_id:int, view:str, metric:str) -> list[str]:           
        sql = f'''
            SELECT theme_path, COUNT(*), ROUND(CAST(SUM({metric}) AS numeric), 2)
            FROM "App_price" P, "App_theme" T, "App_{view}" _view, "App_item" I
            WHERE user_id = {user_id}
                AND theme_path NOT LIKE '%~%'
                AND (I.item_id, date) = any (
                    SELECT DISTINCT ON (item_id) item_id, max(date) 
                    FROM "App_price" P2  
                    GROUP BY item_id
                )
                AND I.item_id = P.item_id
                AND I.item_id = _view.item_id
                AND I.item_id = T.item_id
            GROUP BY theme_path

        '''
        return self.SELECT(sql)
        

    def get_item_themes(self, item_id):
        sql = f'''
            SELECT theme_path
            FROM "App_theme"
            WHERE item_id = '{item_id}'
        '''
        return [theme[0] for theme in self.SELECT(sql)]


    def sub_themes(self, user_id:int, theme_path:str, view:str, metric:str) -> list[str]:
        sql = f'''
            SELECT theme_path, COUNT(*), ROUND(CAST(SUM({metric}) AS numeric), 2)
            FROM "App_price" P, "App_theme" T, "App_{view}" _view, "App_item" I
            WHERE user_id = {user_id}
                AND theme_path LIKE '{theme_path}%'
                AND theme_path != '{theme_path}'
                AND (I.item_id, date) = any (
                    SELECT DISTINCT ON (item_id) item_id, max(date) 
                    FROM "App_price" P2  
                    GROUP BY item_id
                )
                AND I.item_id = P.item_id
                AND I.item_id = _view.item_id
                AND I.item_id = T.item_id
            GROUP BY theme_path
        '''
        return self.SELECT(sql)
    

    def get_popular_items(self) -> list[str]:
        sql = '''
            SELECT I.item_id, item_name, year_released, item_type, avg_price, 
                min_price, max_price, total_quantity, views
            FROM "App_item" i, "App_price" P
            WHERE views > 0
                AND I.item_id = P.item_id
                AND date = (SELECT MAX(date) FROM "App_price")
            GROUP BY avg_price, min_price, max_price, total_quantity, I.item_id
            ORDER BY views DESC

        '''
        return self.SELECT(sql)
    

    def get_weekly_item_metric_change(self, item_id, last_weeks_date, metric) -> int:        
        sql = f'''
            SELECT (
            (SELECT AVG({metric})
            FROM "App_price"
            WHERE date = '{last_weeks_date}'
                AND item_id = '{item_id}'
            ) 
            - 
            (SELECT AVG({metric})
            FROM "App_price"
            WHERE date = '{datetime.datetime.today().strftime("%Y-%m-%d")}'
                AND item_id = '{item_id}'
            )
        ) 
        FROM "App_item"
        WHERE item_id = '{item_id}'
        '''
        result = self.SELECT(sql, fetchone=True)[0]
        if result == None:
            return 0
        return result
    
    def get_new_items(self) -> list[str]:
        #REMOVE WHERE CLAUSE, only items where y_released = 1900 is stored in "App_price"
        sql = '''
            SELECT I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity
            FROM "App_item" I, "App_price" P
            WHERE I.item_id LIKE 'sw%'
                AND I.item_id = P.item_id
                AND date = (SELECT MAX(date) FROM "App_price")
            ORDER BY year_released DESC
        '''
        return self.SELECT(sql)
    

    def get_most_weekly_viewed_themes(self) -> list[str]:
        sql = '''
            SELECT theme_path, SUM(views) as [total_views]
            FROM "App_theme" T, "App_item" I
            WHERE T.item_id = I.item_id
            GROUP BY theme_path
            ORDER BY [total_views] DESC
        '''
        return self.SELECT(sql)


    def get_total_owners_or_watchers(self ,view, item_id):
        if view == "portfolio":
            sql = f'''
                SELECT DISTINCT ON (user_id) item_id
                FROM "App_{view}"
                WHERE item_id = '{item_id}'
            '''
            return len(self.SELECT(sql))
        else:
            sql = f'''
                SELECT count(*)
                FROM "App_watchlist"
                WHERE item_id = '{item_id}'
                GROUP BY user_id
            '''
            result = self.SELECT(sql, fetchone=True)
            if result == None:
                return 0
            return result[0]

        
    def get_similar_items(self, item_name, item_type, item_id, sql_like):
        sql = f'''
            SELECT DISTINCT ON (I.item_id) I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity
            FROM "App_item" I, "App_theme" T, "App_price" P
            WHERE I.item_id = T.item_id
                AND P.item_id = I.item_id
                AND theme_path IN (SELECT theme_path FROM "App_theme" WHERE item_id = '{item_id}')
                AND item_name != '{item_name}'
                AND item_type = '{item_type}'
                {sql_like}
        '''

        if self.SELECT(sql) == None:
            return []
        return self.SELECT(sql)
    

    def get_item_parent_theme(self, item_id):
        sql = f'''
            SELECT theme_path
            FROM "App_item" I, "App_theme" TH
            WHERE TH.item_id = I.item_id
                AND LENGTH(theme_path) = LENGTH(REPLACE(theme_path, '~', '')) 
				AND I.item_id = '{item_id}'
        '''
        return self.SELECT(sql, fetchone=True)[0]
    

    def get_item_type(self, item_id):
        sql = f'''
            SELECT item_type
            FROM "App_item"
            WHERE item_id = '{item_id}'
        '''
        return self.SELECT(sql, fetchone=True)[0]


    def get_most_common_words(self, field, item_type, *args, **kwargs):
        min_word_length = kwargs.get("min_word_length", 3)
        limit = kwargs.get("limit", 100)

        if len(args) != 0:

            replace_sql = f""
            for i, char in enumerate(args):
                if i == 0:
                    replace_sql += f"REPLACE({field}, '{char}', '')"
                else:
                    replace_sql = "REPLACE(" + replace_sql
                    replace_sql += f", '{char}', '')"
            replace_sql += ", ' '"
        else:
            replace_sql = "item_name, ''"

        sql = f'''
            SELECT word
            FROM 
            (
                SELECT UNNEST(
                string_to_array(
                    {replace_sql}
                )) AS word
                FROM "App_item" I
                WHERE item_type = '{item_type}'
            ) AS sub_query
            WHERE LENGTH(word) >= {min_word_length}
            GROUP BY word
            ORDER BY COUNT(*) DESC 
            LIMIT {limit}      
        '''
        return [word[0] for word in self.SELECT(sql)]