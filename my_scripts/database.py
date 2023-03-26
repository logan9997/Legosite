import sqlite3
import datetime
import sys 
import psycopg2

class DatabaseManagment():

    def __init__(self) -> None:
        self.con = psycopg2.connect('''
            user=jalkrxxifnsfhv dbname=d9evsf0knvksog 
            host=ec2-35-169-9-79.compute-1.amazonaws.com port=5432
            password=b82b631a3b1139285895f94e3352bdc3082c951df34c4807f7b11c240937cd91
        ''')
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
            self.cursor.execute(f'''
                INSERT INTO "App_price" (
                    'item_id','date','avg_price',
                    'min_price','max_price','total_quantity'
                )
                VALUES
                (
                    '{item["item"]["no"]}', '{today}', '{round(float(item["avg_price"]), 2)}',
                    '{round(float(item["min_price"]),2)}', '{round(float(item["max_price"]),2)}',
                    '{item["total_quantity"]}'
                )
            ''')
        except sqlite3.IntegrityError:
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
            SELECT I.item_id, item_name, year_released, quantity
            FROM "App_item" I, "App_setparticipation" SP
            WHERE I.item_id in (
                SELECT set_id
                FROM "App_setparticipation" SP 
                WHERE item_id = '{item_id}'
            )
                AND SP.set_id = I.item_id
            GROUP BY I.item_id
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
            SELECT COUNT()
            FROM "App_price"
            WHERE date = '{today}'
        '''
        return self.SELECT(sql)


    def get_most_viewed_items(self) -> list[str]:
        sql = '''
            SELECT item_id
            FROM "App_item"
            ORDER BY views DESC
        '''
        return self.SELECT(sql)

    def increment_item_views(self, item_id) -> None:
        self.cursor.execute(f'''
            UPDATE "App_item"
            SET views = views + 1
            WHERE item_id = '{item_id}'
        ''')
        self.con.commit()


    def get_minifig_prices(self, minifig_id) -> list[str]:
        sql = f'''
            SELECT date, avg_price, min_price, max_price, total_quantity
            FROM "App_price"
            WHERE item_id = '{minifig_id}'
        '''
        
        return self.SELECT(sql)


    def get_dates(self, minifig_id) -> list[str]:
        sql = f'''
            SELECT date
            FROM "App_price"
            WHERE item_id = '{minifig_id}'
        '''
        return self.SELECT(sql)     

    
    def get_biggest_trends(self, change_metric) -> list[str]:

        sql = f'''
            SELECT I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity, ABS(ROUND((
                (SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                    ) 
            ) - {change_metric}) *-1.0 /  (
            SELECT {change_metric}
            FROM "App_price" P2
            WHERE P2.item_id = P1.item_id
                AND date = (
                    SELECT min(date)
                    FROM "App_price"
                ) 
            ) * 100, 2)) AS [percentage change]
            FROM "App_price" P1, "App_item" I
            WHERE I.item_id = P1.item_id 
                AND date = (
                    SELECT max(date)
                    FROM "App_price"
                ) 
            ORDER BY [percentage change] DESC
        '''

        result = self.SELECT(sql)
        losers = result[len(result)-10:][::-1]
        winners = result[:10]
        return winners


    def group_by_items(self) -> list[str]:
        sql = '''
            SELECT item_id, item_type
            FROM "App_item"
            GROUP BY item_id
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
        if sort_field[0] == "item_id":
            sort_field[0] = "I.item_id"
        sql = f'''
            SELECT I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity, date
            FROM "App_item" I, "App_theme" T, "App_price" P1
            WHERE T.item_id = I.item_id
                AND I.item_id = P1.item_id
                AND theme_path = '{theme_path}'
                AND item_type = 'M'
                AND date = (
                    SELECT MAX(date) 
                    FROM "App_price" P2 
                    GROUP BY item_id
                )
            GROUP BY I.item_id
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
    

    def get_item_metric_changes(self, item_id, change_metric):
        sql = f'''
            SELECT round(
                ((
                SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND I.item_id = '{item_id}'
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                        WHERE item_id = '{item_id}'
                    ) 
                ) - {change_metric}) *-1.0 / (
                SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND I.item_id = '{item_id}'
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                        WHERE item_id = '{item_id}'
                    )
            ) *100, 2) as '%change'

            FROM "App_price" P1, "App_item" I
            WHERE I.item_id = P1.item_id 
                AND I.item_id = '{item_id}'
                AND date = (
                    SELECT max(date)
                    FROM "App_price"
                    WHERE item_id = '{item_id}'
                ) 
            GROUP BY I.item_id
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
            min_price, max_price, total_quantity, round(
                ((
                SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND I.item_id = '{item_id}'
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                        WHERE item_id = '{item_id}'
                    ) 
                ) - {change_metric}) *-1.0 / (
                SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND I.item_id = '{item_id}'
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                        WHERE item_id = '{item_id}'
                    )
            ) *100) as "%change"

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

    def get_not_null_years(self) -> list[str]:
        sql = '''
            SELECT item_id
            FROM "App_item"
            WHERE year_released is null
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
            self.cursor.execute(f'''
                INSERT INTO "App_theme" ('theme_path', 'item_id') VALUES ('{theme_details["path"]}', '{item}')
            ''')
            self.con.commit()


    def get_user_items(self, user_id, view) -> list[str]:

        sql_select = "SELECT I.item_id, item_name, year_released, item_type,avg_price, min_price, max_price, total_quantity"
        if view == "portfolio":
            sql_select += f''',
                (SELECT COUNT() FROM App_portfolio P2 WHERE user_id = 1 AND condition = 'N' AND _view1.item_id = P2.item_id GROUP BY item_id) as 'N',
                (SELECT COUNT() FROM App_portfolio P2 WHERE user_id = 1 AND condition = 'U' AND _view1.item_id = P2.item_id GROUP BY item_id) as 'U'
            '''

        sql = f'''
            {sql_select}
            FROM "App_{view}" _view1, "App_item" I, "App_price" P
            WHERE user_id = {user_id}
                AND (date, I.item_id) IN (SELECT MAX(date), item_id FROM "App_price" GROUP BY item_id)
                AND I.item_id = _view1.item_id 
                AND I.item_id = P.item_id
            GROUP BY I.item_id 
        '''
        return self.SELECT(sql)


    def is_item_in_user_items(self, user_id, view, item_id) -> bool:

        if view == "portfolio":
            sql_select = "SELECT condition, COUNT()" 
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
            FROM App_portfolio PO, "App_price" PR, "App_item" I
            WHERE PO.user_id = {user_id}
                AND PO.item_id = I.item_id
                AND I.item_id = PR.item_id
            GROUP BY I.item_id, condition
        '''
        return self.SELECT(sql)


    def user_items_total_price(self, user_id, metric, view) -> list[str]:
        sql = f'''
        SELECT ROUND(SUM({metric}), 2)
        FROM "App_{view}" _view, "App_item" I, "App_price" P
        WHERE user_id = {user_id}
            AND (date, I.item_id) IN (SELECT MAX(date), item_id FROM "App_price" GROUP BY item_id)
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


    def get_pieces_colours(self):
        sql = '''
            SELECT piece_id, colour_id
            FROM "App_pieceparticipation"
            GROUP BY piece_id, colour_id
        '''
        return self.SELECT(sql)


    def get_portfolio_item_quantity(self, item_id, condition, user_id) -> int:
        sql = f'''
            SELECT quantity
            FROM App_portfolio
            WHERE item_id = '{item_id}'
                AND condition = '{condition}'
                AND user_id = '{user_id}'
        '''
        return int(self.SELECT(sql)[0][0])


    def get_portfolio_price_trends(self, user_id) -> list[str]:
        sql = f'''
            SELECT date, ROUND(SUM(avg_price * quantity) ,2)
            FROM App_portfolio PO, "App_price" PR, "App_item" I
            WHERE user_id = {user_id}
                AND PO.item_id = I.item_id
                AND PR.item_id = I.item_id
            GROUP BY date
        '''
        return self.SELECT(sql)


    def biggest_portfolio_changes(self, user_id, metric) -> list[str]:
        sql = f'''
            SELECT I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity, ROUND(
            (
                SELECT {metric}
                FROM "App_price" P1
                WHERE date IN (
                    SELECT MAX(date) 
                    FROM "App_price" 
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
                WHERE date IN (
                    SELECT MIN(date) 
                    FROM "App_price" 
                    GROUP BY item_id
                )
                AND user_id = {user_id}
                AND P1.item_id = I.item_id
                AND I.item_id = PO.item_id
            )
            ,2) AS [Change]

            FROM "App_price" P2 , App_portfolio PO, "App_item" I
            WHERE user_id = {user_id}
                AND PO.item_id = I.item_id
                AND I.item_id = P2.item_id
            GROUP BY I.item_id
            ORDER BY ABS([change]) DESC
        '''
        return self.SELECT(sql)


    def biggest_theme_trends(self, change_metric) -> list[str]:
        sql = f'''
            SELECT theme_path, round((
                (SELECT {change_metric}
                FROM "App_price" P2
                WHERE P2.item_id = P1.item_id
                    AND date = (
                        SELECT min(date)
                        FROM "App_price"
                    ) 
            ) - {change_metric}) *-1.0 /  (
            SELECT {change_metric}
            FROM "App_price" P2
            WHERE P2.item_id = P1.item_id
                AND date = (
                    SELECT min(date)
                    FROM "App_price"
                ) 
            ) * 100, 2) AS [percentage change]
            FROM "App_price" P1, "App_item" I, "App_theme" T
            WHERE I.item_id = P1.item_id 
                AND T.item_id = I.item_id
                AND date = (
                    SELECT max(date)
                    FROM "App_price"
                ) 
            GROUP BY theme_path
            ORDER BY [percentage change] DESC
        '''
        return self.SELECT(sql)

    
    def get_portfolio_items_condition(self, user_id) -> list[str]:
        sql = f'''
            SELECT item_id, condition
            FROM App_portfolio
            WHERE user_id = {user_id}
        '''
        return self.SELECT(sql)


    def total_portfolio_price_trend(self, user_id) -> list[str]:
        sql = f'''
            SELECT SUM(max_price), date
            FROM "App_price" price, App_portfolio portfolio, "App_item" item, "App_user" user
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
        return self.SELECT(sql)


    def insert_item_info(self, item_info) -> None:
        type_convert = {"MINIFIG":"M", "SET":"S"}
        self.cursor.execute(f'''
            INSERT INTO "App_item"
            ('item_id', 'item_name', 'year_released', 'item_type')
            VALUES ('{item_info["no"]}', '{item_info["name"].replace("'", "")}', '{item_info["year_released"]}', '{type_convert[item_info["type"]]}')
        ''')
        self.con.commit()


    def add_to_user_items(self, user_id, item_id, view, date_added, **portfolio_args) -> None:
        
        
        sql_fields = "('user_id', 'item_id', 'date_added'"
        sql_values = f"VALUES ({user_id},'{item_id}','{date_added}'"

        if view == "portfolio":
            condition = portfolio_args["condition"]
            bought_for = portfolio_args["bought_for"]

            sql_fields += ",'condition', 'bought_for')"
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
        if kwargs.get("user_id") != None and kwargs.get("view") != None:
            sql = f'''
                SELECT {metric}, date
                FROM "App_price" P, "App_{kwargs.get("view")}" View, "App_item" I
                WHERE user_id = {kwargs.get("user_id")}
                    AND I.item_id = '{item_id}'
                    AND P.item_id = I.item_id
                    AND I.item_id = View.item_id
                GROUP BY I.item_id, P.date
            '''
        else:
            sql = f'''
                SELECT {metric}, date
                FROM "App_price" P, "App_item" I
                WHERE I.item_id = '{item_id}'
                    AND P.item_id = I.item_id
                GROUP BY {metric}, I.item_id, P.date
            '''        

        return self.SELECT(sql)
    

    def get_sub_theme_set(self ,theme_path:str, sub_theme_indent:int):
        for char in ["/", " "]:
            if char in theme_path:
                theme_path = theme_path.replace(char, "~")

        sql = f'''
            SELECT theme_path, I.item_id
            FROM "App_theme" T, "App_item" I
            WHERE T.item_id = I.item_id
                AND item_type = 'S'
                AND theme_path LIKE '{theme_path}%'
                AND LENGTH(theme_path) - LENGTH(REPLACE(theme_path, '~', '')) = {sub_theme_indent}
            GROUP BY theme_path
        '''

        result = self.SELECT(sql)
        if result == None:
            return 'No-Image'
        return result


    def parent_themes(self, user_id:int, view:str, metric:str) -> list[str]:           
        sql = f'''
            SELECT theme_path, COUNT(), ROUND(SUM({metric}),2)
            FROM "App_price" P, "App_theme" T, "App_{view}" _view, "App_item" I
            WHERE user_id = {user_id}
                AND theme_path NOT LIKE '%~%'
                AND (date, P.item_id) IN (SELECT MAX(date), item_id FROM "App_price" GROUP BY item_id)
                AND I.item_id = P.item_id
                AND I.item_id = _view.item_id
                AND I.item_id = T.item_id
            GROUP BY theme_path

        '''
        return self.SELECT(sql)


    def sub_themes(self, user_id:int, theme_path:str, view:str, metric:str) -> list[str]:
        sql = f'''
            SELECT theme_path, COUNT(), ROUND(SUM({metric}),2), P.item_id
            FROM "App_price" P, "App_theme" T, "App_{view}" _view, "App_item" I
            WHERE user_id = {user_id}
                AND theme_path LIKE '{theme_path}%'
                AND theme_path != '{theme_path}'
                AND (date, P.item_id) IN (SELECT MAX(date), item_id FROM "App_price" GROUP BY item_id)
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
            GROUP BY I.item_id
            ORDER BY views DESC

        '''
        return self.SELECT(sql)
    

    def get_weekly_item_metric_change(self, item_id, last_weeks_date, metric) -> int:

        print(metric)
        
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
        ) AS 'change'
        FROM "App_item"
        WHERE item_id = '{item_id}'
        '''
        return self.SELECT(sql, fetchone=True)
    
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
                SELECT item_id
                FROM "App_{view}"
                WHERE item_id = '{item_id}'
                GROUP BY user_id
            '''
            return len(self.SELECT(sql))
        else:
            sql = f'''
                SELECT count()
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
            SELECT I.item_id, item_name, year_released, item_type, avg_price, 
            min_price, max_price, total_quantity
            FROM "App_item" I, "App_theme" T, "App_price" P
            WHERE I.item_id = T.item_id
                AND P.item_id = I.item_id
                AND theme_path IN (SELECT theme_path FROM "App_theme" WHERE item_id = '{item_id}')
                AND item_name != '{item_name}'
                AND item_type = '{item_type}'
                {sql_like}
            GROUP BY I.item_id
        '''

        if self.SELECT(sql) == None:
            return []
        return self.SELECT(sql)

