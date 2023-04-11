import math
import time
import itertools
from datetime import datetime

from .models import (
    User,
    Item, 
    Theme,
    Price,
    Piece,
    Portfolio,
    PieceParticipation,
    SetParticipation,
    Watchlist
)

from django.db.models import (
    Q,
    Sum,
    Count,
) 

from .config import *

def timer(func):
    def inner(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        finish = round(time.time() - start, 5)
        print(f"\n<{func.__name__.upper()}> finished in {finish} seconds.\n")
        return result 
    return inner

def base_url(request) -> str:
    return request.get_host().strip(" ")


def clean_html_codes(string:str):
    codes = {
        "&#41;":")", 
        "&#40;":"(",
        "&#39;": "'"
    }

    for k, v in codes.items():
        if k in string:
            string = string.replace(k ,v)
    return string


def format_item_info(items:tuple, **kwargs) -> list[dict]:
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
        "item_name":clean_html_codes(item[1]),
        "year_released":item[2],
        "item_type":item[3],
        "avg_price":item[4],
        "min_price":item[5],
        "max_price":item[6],
        "total_quantity":item[7],
        "img_path":f"App/minifigures/{item[0]}.png",
        }
    
        if "metric_changes" in kwargs:
            metric_changes = kwargs.get("metric_changes", [])
            item_dict = add_metric_changes(metric_changes, item_dict)

        if "graph_data" in kwargs:
            item_dict = add_graph_data(item_dict, **kwargs)

        if "owned_quantity_new" in kwargs and "owned_quantity_used" in kwargs and kwargs.get("view", '') == "portfolio":
            item_dict = item_owned_quantity(item_dict, **kwargs)

        #only accepts values of type int, v < len(item) to avoid indexing errors
        item_dict.update({
            k : item[v] for k, v in kwargs.items() if type(v) == int and v < len(item)
        })

        item_dicts.append(item_dict)

    return item_dicts


def item_owned_quantity(item_dict:dict, **kwargs):
    owned_quantity_new = DB.get_portfolio_item_quantity(item_dict["item_id"], "N", kwargs.get("user_id", -1))
    owned_quantity_used = DB.get_portfolio_item_quantity(item_dict["item_id"], "U", kwargs.get("user_id", -1))
    item_dict["owned_quantity_new"] = owned_quantity_new
    item_dict["owned_quantity_used"] = owned_quantity_used
    return item_dict


def add_metric_changes(metric_changes:list[str], item_dict:dict, **kwargs):
    item_dict["metric_changes"] = {}
    for metric in metric_changes:
        item_dict["metric_changes"][metric] = DB.get_item_metric_changes(item_dict["item_id"], metric, kwargs.get("user_id", -1))
    return item_dict


def add_graph_data(item_dict:dict, **kwargs):
    item_dict.update({
        "chart_id":f"{item_dict['item_id']}_chart" + f"{kwargs.get('item_group', '')}",
        "dates":append_graph_dates(item_dict['item_id']),
        "dates_id":f"{item_dict['item_id']}_dates" + f"{kwargs.get('item_group', '')}",
    })

    for metric in kwargs.get("graph_data", []):
        item_dict.update({
            f"{metric}_graph":append_item_graph_info(item_dict['item_id'], graph_metric=metric, user_id=kwargs.get("user_id", -1))[0],
            f"{metric}_id":f"{item_dict['item_id']}_{metric}" + f"{kwargs.get('home_view', '')}",
        })
    return item_dict


def format_portfolio_items(items):
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


def format_theme_items(theme_items):
    theme_items_formated = [
        {
            "item_id":item[0],
            "item_type":item[1],
            "img_path":f"App/sets/{item[0]}.png",
        } for item in theme_items
    ]

    return theme_items_formated


def format_sub_sets(pieces):
    set_dicts = []
    for piece in pieces:
        set_dict = {
            "piece_id":piece[0],
            "piece_name":clean_html_codes(piece[1]),
            "colour_id":piece[2],
            "quantity":piece[3],
            "img_path":f"App/pieces/{piece[2]}_{piece[0]}.png",
        }
        set_dicts.append(set_dict)
    return set_dicts


def format_super_sets(sets):
    set_dicts = []
    for _set in sets:
        set_dict = {
            "set_id":_set[0],
            "set_name":clean_html_codes(_set[1]),
            "year_released":_set[2],
            "quantity":_set[3],
            "img_path":f"App/sets/{_set[0]}.png",
        }
        set_dicts.append(set_dict)
    return set_dicts


def biggest_theme_trends():
    themes = DB.biggest_theme_trends("avg_price")
    themes_formated = [
        {
            "theme_path":theme[0],
            "change":theme[1]
        } for theme in themes
    ]

    losers_winners = {
        "biggest_winners":sorted(themes_formated[:5], key=lambda x:x["change"]),
        "biggest_losers":sorted(themes_formated[-5:][::-1], key=lambda x:x["change"], reverse=True)
    }

    return losers_winners 

def get_current_page(request, portfolio_items:list, items_per_page) -> int:

    current_page = int(request.GET.get("page", 1)) 

    pages = math.ceil(len(portfolio_items) / items_per_page) 
    #boundaries for next and back page
    back_page = current_page - 1
    next_page = current_page + 1

    if current_page == pages: 
        next_page = current_page
    elif current_page == 1:
        back_page = current_page

    if back_page <= 0:
        back_page = 1

    return back_page, current_page, next_page


def get_change_password_error_message(rules:list[dict[str, str]]) -> str:
    for rule in rules:
        rule = rule.popitem()
        if not rule[0]:
            return rule[1]


def sort_themes(field:str, order:str, sub_themes:list[str]) -> list[str]:
    order_convert = {"asc":False, "desc":True}
    order = order_convert[order]
    if field == "theme_name":
        return sorted(sub_themes, key=lambda x:x["sub_theme"], reverse=order)
    return sub_themes

    #elif field == "popularity":
    #elif field == "avg_growth":
    #else:


def sort_items(items, sort , **order) -> list[dict]:
    sort_field = sort.split("-")[0]
    order = {"asc":False, "desc":True}[sort.split("-")[1]]
    items = sorted(items, key=lambda field:field[sort_field], reverse=order)
    return items


def sort_dropdown_options(options:list[dict[str,str]], field:str) -> list[dict[str,str]]:
    #loop through all options. If options["value"] matches to desired sort field, assign to variable
    selected_field = [option for option in options if option["value"] == field][0]

    #push selected element to front of list, remove its old position
    options.insert(0, options.pop(options.index(selected_field)))
    
    return options

def get_sub_themes(user_id:int, parent_themes:list[str], themes:list[dict], indent:int, view:str, metric:str) -> list[str]:

    indent += 1
    for theme in parent_themes:
        sub_themes = DB.sub_themes(user_id, theme[0], view, metric)
        sub_themes = [theme_path for theme_path in sub_themes if theme_path.count("~") == indent]

        themes.append({
            "theme_path":theme[0],
            "count":theme[1],
            "metric_total":theme[2],
            "sub_themes":sub_themes,
        })

        get_sub_themes(user_id, sub_themes, themes, indent, view, metric)

    return themes


def clear_session_url_params(request, *keys:str, **sub_dict:dict):
    #options to del values from a sub dict of request.session eg request.session["dict_name"]
    if sub_dict.get("sub_dict") != None:
        if sub_dict.get("sub_dict") in request.session:
            _dict = request.session[sub_dict.get("sub_dict")]
        else:
            _dict = request.session
    else:
        _dict = request.session

    for key in keys:
        if key in _dict:
            del _dict[key]
    return request


def check_page_boundaries(current_page, list_len:int, items_per_page:int):

    try:
        current_page = int(current_page)
    except:
        return 1

    conditions = [
        current_page <= math.ceil(list_len / items_per_page),
        current_page > 0,
    ]

    if not all(conditions):
        return 1
    
    return current_page


def slice_num_pages(list_len:int, current_page:int, items_per_page:int):
    num_pages = [i+1 for i in range((list_len // items_per_page ) + 1)]
    last_page = num_pages[-1] -1

    list_slice_start = current_page - (PAGE_NUM_LIMIT // 2)
    list_slice_end = current_page - (PAGE_NUM_LIMIT // 2) + PAGE_NUM_LIMIT 

    if list_slice_end > len(num_pages):
        list_slice_end = len(num_pages) -1
        list_slice_start = list_slice_end - PAGE_NUM_LIMIT
    if list_slice_start < 0 :
        list_slice_end -= list_slice_start
        list_slice_start = 0

    num_pages = num_pages[list_slice_start:list_slice_end]

    #remove last page. if len(items) % != 0 by ITEMS_PER_PAGE -> blank page with no items
    if list_len % items_per_page == 0:
        num_pages.pop(-1)

    if 1 not in num_pages:
        num_pages.insert(0, 1)

    if last_page not in num_pages:
        num_pages.append(last_page)

    if 0 in num_pages:
        num_pages.remove(0)

    if len(num_pages) == 1:
        return []

    return num_pages


def append_item_graph_info(item_id:str, graph_metric:str, **kwargs):
    prices = [] ; dates = []
    for price_date_info in DB.get_item_graph_info(item_id, graph_metric, view=kwargs.get("view"), user_id=kwargs.get("user_id")):
        prices.append(price_date_info[0])
    return prices, dates


def append_graph_dates(item_id, **kwargs):
    dates = []
    for price_date_info in DB.get_item_graph_info(item_id, "avg_price", view=kwargs.get("view"), user_id=kwargs.get("user_id")):
        dates.append(price_date_info[1])
    return dates



def save_POST_params(request) -> tuple[dict, dict]:
    if "url_params" in request.session:
        for k, v in request.POST.items():
            request.session["url_params"][k] = v
        options = request.session["url_params"]
    else:
        request.session["url_params"] = {}
        options = {}

    request.session.modified = True
    return request, options


def extend_remove_words(words:list, *args) -> list:

    for arg in args:
        words.extend(arg)

    for func in [str.capitalize]:
        words.extend(list(map(func, words)))
    return words



def similar_items_iterate(single_words:list[str], item_name:str, item_type:str, item_id:str, items:list[str], i:int) -> tuple[int, list]:
    for sub in itertools.combinations(single_words, i):
        sql_like = "AND " + ''.join([f"item_name LIKE '%{word}%' AND " for word in sub])[:-4]
        new_items = DB.get_similar_items(item_name, item_type, item_id, sql_like)
        # print(sub, len(items), [item[0] for item in items])

        for item in new_items:
            if len(items) < MAX_SIMILAR_ITEMS and item not in items:
                items.append(item)
                if len(items) >= MAX_SIMILAR_ITEMS:
                    return i, list(dict.fromkeys(items))

        print(len(sub), len(items), i)
        if len(sub) <= 3 and len(items) >= 3:
            return i, items

    return i, []


def get_similar_items(item_name:str, item_type:str, item_id:str) -> list:

    item_type = DB.get_item_type(item_id)
    remove_words = list(DB.get_most_common_words("item_name", item_type, ',', '(', ')', min_word_length=2, limit=25))
    remove_words = extend_remove_words(remove_words, COLOURS, EXTRA_WORDS)

    single_words = [
        ''.join(char for char in word if char not in REMOVE_CHARS) 
        for word in item_name.split(" ")
        if len(word) > 3 and ''.join(char for char in word if char not in REMOVE_CHARS) not in remove_words
    ]

    i = len(single_words) ; items = []

    #shorten i if too many words to parse through
    length_single_words_convert = {
        len(single_words) < 5:1,
        len(single_words) >= 5 and len(single_words) < 9: 2,
        len(single_words) >= 9:3
    }
    i = i // length_single_words_convert[True]
    
    if i > 3:
        i = 3

    while True:
        i, items = similar_items_iterate(single_words, item_name, item_type, item_id, items, i)

        if len(items) >= MAX_SIMILAR_ITEMS or i <= 1:
            break

        i -= 1
    return items[:MAX_SIMILAR_ITEMS]


def get_metric_changes(item_id, **kwargs) -> list[dict]:

    changes = [
        {"metric":" ".join(list(map(str.capitalize, metric_change.split("_")))), 
        "change":DB.get_item_metric_changes(item_id, metric_change, **kwargs)} 
        for metric_change in ["avg_price", "min_price", "max_price", "total_quantity"]
    ]
    return changes