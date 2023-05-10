from .general import General
from config.config import (
    ITEM_TYPE_CONVERT,
    ALL_METRICS
)
from scripts.database import DatabaseManagment


DB = DatabaseManagment()
GENERAL = General()


class Formatter():

    def format_item_info(self, items:tuple, **kwargs) -> list[dict]:
        '''
        function to convert tuples returned from SQL queries into a readable dict
        structure. Hard coded key value pairs inside the decleration of the item_dict
        variable appears for all items. Kwargs will add any additional key : value pairs
        where the value is the index of the field returned from the SQL query.

        ADDITIONAL KWARGS (excluding kwargs that specify a tuple index)
        - graph_data:list[str] - a list of all graph metrics to be displayed on the items graph
        - metric_trends:list[str] - a list metrics to show % change of first and last records
        - item_group:str - used to create different chart ids when the same item appears multiple times on the same page 
        - view:str - used for distinguishing between portfolio and watchlist views
        '''

        item_dicts = []
        for item in items:
            item_dict = {
            "item_id":item[0],
            "item_name":GENERAL.clean_html_codes(item[1]),
            "year_released":item[2],
            "item_type":item[3],
            "avg_price":item[4],
            "min_price":item[5],
            "max_price":item[6],
            "total_quantity":item[7],
            "img_path":f"App/{ITEM_TYPE_CONVERT[item[3]]}s/{item[0]}.png",
            }
        
            if "metric_changes" in kwargs:
                metric_changes = kwargs.get("metric_changes", [])
                item_dict = AdditionalItemData().add_metric_changes(metric_changes, item_dict)

            if "graph_data" in kwargs:
                item_dict = AdditionalItemData().add_graph_data(item_dict, **kwargs)

            if "owned_quantity_new" in kwargs and "owned_quantity_used" in kwargs and kwargs.get("view", '') == "portfolio":
                item_dict = AdditionalItemData().add_item_owned_quantity(item_dict, **kwargs)

            #only accepts values of type int, v < len(item) to avoid indexing errors
            item_dict.update({
                k : item[v] for k, v in kwargs.items() if type(v) == int and v < len(item)
            })
            item_dicts.append(item_dict)
        return item_dicts


    def format_theme_items(self, theme_items):
        theme_items_formated = [
            {
                "item_id":item[0],
                "item_type":item[1],
                "img_path":f"App/{ITEM_TYPE_CONVERT[item[1]]}/{item[0]}.png",
            } for item in theme_items
        ]

        return theme_items_formated
    
    def format_sub_sets(self, pieces):
        pieces_dicts = []
        for piece in pieces:
            set_dict = {
                "piece_id":piece[0],
                "piece_name":GENERAL.clean_html_codes(piece[1]),
                "colour_id":piece[2],
                "quantity":piece[3],
                "img_path":f"App/pieces/{piece[2]}_{piece[0]}.png",
            }
            pieces_dicts.append(set_dict)
        return pieces_dicts
    

    def format_super_sets(self, sets):
        set_dicts = []
        for _set in sets:
            set_dict = {
                "set_id":_set[0],
                "set_name":GENERAL.clean_html_codes(_set[1]),
                "year_released":_set[2],
                "quantity":_set[3],
                "img_path":f"App/sets/{_set[0]}.png",
            }
            set_dicts.append(set_dict)
        return set_dicts
    

    def format_biggest_theme_trends(self, themes):
        themes_formated = [
            {
                "theme_path":theme[0],
                "change":theme[1]
            } 
            for theme in themes]
        
        themes_formated = [theme for theme in themes_formated if theme["change"] != None]
        themes_formated = sorted(themes_formated, key=lambda x:x["change"], reverse=True)

        losers_and_winners = {
            "biggest_winners":themes_formated[:5],
            "biggest_losers":sorted(themes_formated[-5:], key=lambda x:x["change"])
        }
        return losers_and_winners 
    
    
    def format_portfolio_items(self, items):
        item_dicts = []
        for _item in items:

            if _item[3] != None:
                date_added = _item[3].strftime("%Y-%m-%d")
            else:
                date_added = _item[3]

            if _item[4] != None:
                date_sold = _item[4].strftime("%Y-%m-%d")
            else:
                date_sold = _item[4]

            item_dicts.append({
                "condition":_item[0],
                "bought_for":_item[1],
                "sold_for":_item[2],
                "date_added":date_added,
                "date_sold":date_sold,
                "notes":_item[5],
                "entry_id":_item[6]
            })
        return item_dicts
    

    def format_metric_changes(self, metrics) -> list[dict]:
        changes = {
            GENERAL.split_capitalize(ALL_METRICS[i], "_") : change
            for i, change in enumerate(metrics)
        }

        return changes
    

class AdditionalItemData():

    def add_graph_data(self, item_dict:dict, **kwargs):
        item_id = item_dict['item_id']
        item_dict.update({
            "chart_id":f"{item_id}_chart" + f"{kwargs.get('item_group', '')}",
            "dates":self.append_item_graph_info(item_id, 'date', **kwargs),
            "dates_id":f"{item_id}_dates" + f"{kwargs.get('item_group', '')}",
        })

        for metric in kwargs.get("graph_data", []):
            item_dict.update({
                f"{metric}_graph":self.append_item_graph_info(item_id, metric, **kwargs),
                f"{metric}_id":f"{item_id}_{metric}" + f"{kwargs.get('home_view', '')}",
            })
        return item_dict
    
    
    def add_item_owned_quantity(self, item_dict:dict, **kwargs):
        owned_quantity_new = DB.get_portfolio_item_quantity(item_dict["item_id"], "N", kwargs.get("user_id", -1))
        owned_quantity_used = DB.get_portfolio_item_quantity(item_dict["item_id"], "U", kwargs.get("user_id", -1))
        item_dict["owned_quantity_new"] = owned_quantity_new
        item_dict["owned_quantity_used"] = owned_quantity_used
        return item_dict
    

    def add_metric_changes(self, metric_changes:list[str], item_dict:dict, **kwargs):
        item_dict["metric_changes"] = {}
        for metric in metric_changes:
            item_dict["metric_changes"][metric] = DB.get_item_metric_changes(item_dict["item_id"], metric, kwargs.get("user_id", -1))
        return item_dict
    

    def append_item_graph_info(self, item_id:str, metric_or_date, **kwargs):
        '''
        return, all records of metric_or_date (avg_price / min_price / max_price
        / total_quantity / date) for a particular item
        **kwargs : user_id, view
        '''
        metric_data = DB.get_item_graph_info(item_id, metric_or_date, **kwargs)
        return metric_data
