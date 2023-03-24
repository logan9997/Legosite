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


def clean_html_codes(string:str):
    codes = {
        "&#41;":")", 
        "&#40;":"("
    }

    for k, v in codes.items():
        if k in string:
            string = string.replace(k ,v)
    return string


def format_item_info(items, **kwargs):
    #view:str ,price_trend:bool, popular_items:bool
    #graph_data:bool new_items:bool

    if kwargs.get("view") == "search":
        user_item_ids_portfolio = Portfolio.objects.filter(user_id=kwargs.get("user_id")).values_list("item_id", flat=True).annotate(items=Count("item_id"))
        user_item_ids_watchlist = Watchlist.objects.filter(user_id=kwargs.get("user_id")).values_list("item_id", flat=True).annotate(items=Count("item_id"))

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
        "img_path":f"App/images/{item[0]}.png",
        }

        if kwargs.get("view") == "portfolio":
            item_dict.update({
                "owned_quantity_new":item[8],
                "owned_quantity_used":item[9],
            })

        elif kwargs.get("view") == "search":
            item_dict.update({
                "in_portfolio":item[0] in user_item_ids_portfolio,
                "in_watchlist":item[0] in user_item_ids_watchlist,
            })

        if kwargs.get("price_trend", False) and kwargs.get("view") == "portfolio":
            item_dict.update({
                "price_change":item[11]
            })

        elif kwargs.get("price_trend", False):
            item_dict["metric_changes"] = {}
            for metric in  kwargs.get("price_trend"):
                item_dict["metric_changes"][f"{metric}_change"] = item[8]

        if kwargs.get("popular_items"):
            item_dict.update({
                "views":item[8], 
            })        
            

        graph_data = kwargs.get("graph_data", False)

        if graph_data != False:
            user_id = kwargs.get("user_id")
            item_dict.update({
                "chart_id":f"{item[0]}_chart" + f"{kwargs.get('home_view', '')}",
                "dates":append_graph_dates(item[0]),
                "dates_id":f"{item[0]}_dates" + f"{kwargs.get('home_view', '')}",
            })

            for metric in graph_data:
                item_dict.update({
                    f"{metric}_graph":append_item_graph_info(item[0], graph_metric=metric, user_id=user_id)[0],
                    f"{metric}_id":f"{item[0]}_{metric}" + f"{kwargs.get('home_view', '')}",
                })

        item_dicts.append(item_dict)

    return item_dicts


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
            "img_path":f"App/images/{item[0]}.png",
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
            "img_path":f"App/images/{piece[2]}_{piece[0]}.png",
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
            "img_path":f"App/images/{_set[0]}.png",
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
        "biggest_winners":themes_formated[:5],
        "biggest_losers":themes_formated[-5:][::-1]
    }

    return losers_winners 

def get_current_page(request, portfolio_items:list, items_per_page) -> int:
    #current page
    page = int(request.GET.get("page", 1)) 
    #number of pages, ITEMS_PER_PAGE items per page
    pages = math.ceil(len(portfolio_items) / items_per_page) 
    #boundaries for next and back page
    back_page = page - 1
    next_page = page + 1
    if page == pages: 
        next_page = page
    elif page == 1:
        back_page = page

    if back_page <= 0:
        back_page = 1

    return back_page, page, next_page


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


def sort_items(items, sort , **order) -> list[str]:
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


def clear_session_url_params(request, *keys, **sub_dict):
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


def similar_items_iterate(single_words:list[str], item_name:str, item_type:str, item_id:str, items:list[str], i:int) -> tuple[int, list]:
    for sub in itertools.combinations(single_words, i):
        sql_like = "AND " + ''.join([f"item_name LIKE '%{word}%' AND " for word in sub])[:-4]
        items = DB.get_similar_items(item_name, item_type, item_id, sql_like)
        if len(items) > 1:
            items.extend(items)
            items = list(dict.fromkeys(items))
            return i, items 
        
        if len(sub) <= 3 and len(items) > 10:
            return i, items

    return i, []


def get_similar_items(item_name:str, item_type:str, item_id:str) -> list:
    single_words = [
        ''.join(char for char in word if char not in REMOVE_CHARS) 
        for word in item_name.split(" ")
        if len(word) > 3 and ''.join(char for char in word if char not in REMOVE_CHARS) not in REMOVE_WORDS
    ]

    i = len(single_words) ; items = []

    #shorten i if too many words to parse through
    length_single_words_convert = {
        len(single_words) < 5:1,
        len(single_words) >= 5 and len(single_words) < 9: 2,
        len(single_words) >= 9:3
    }
    i = i // length_single_words_convert[True]

    while True:
        i, items = similar_items_iterate(single_words, item_name, item_type, item_id, items, i)

        if len(items) > MAX_SIMILAR_ITEMS or i <= 1:
            break

        i -= 1
    return items[:MAX_SIMILAR_ITEMS]
