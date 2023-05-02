import math
import time
import itertools

from datetime import datetime as dt

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
        "img_path":f"App/{ITEM_TYPE_CONVERT[item[3]]}s/{item[0]}.png",
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


def add_metric_changes(metric_changes:list[str], item_dict:dict):
    item_dict["metric_changes"] = {}
    for metric in metric_changes:
        item_dict["metric_changes"][metric] = DB.get_item_metric_changes(item_dict["item_id"], metric, kwargs.get("user_id", -1))
    return item_dict


def add_graph_data(item_dict:dict, **kwargs):
    item_dict.update({
        "chart_id":f"{item_dict['item_id']}_chart" + f"{kwargs.get('item_group', '')}",
        "dates":append_item_graph_info(item_dict['item_id'], 'date', **kwargs),
        "dates_id":f"{item_dict['item_id']}_dates" + f"{kwargs.get('item_group', '')}",
    })

    for metric in kwargs.get("graph_data", []):
        item_dict.update({
            f"{metric}_graph":append_item_graph_info(item_dict['item_id'], metric, **kwargs),
            f"{metric}_id":f"{item_dict['item_id']}_{metric}" + f"{kwargs.get('home_view', '')}",
        })
    return item_dict


def append_item_graph_info(item_id:str, metric_or_date, **kwargs):
    metric_data = DB.get_item_graph_info(item_id, metric_or_date, **kwargs)
    return metric_data


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
            "img_path":f"App/{ITEM_TYPE_CONVERT[item[1]]}/{item[0]}.png",
        } for item in theme_items
    ]

    return theme_items_formated


def format_sub_sets(pieces):
    pieces_dicts = []
    for piece in pieces:
        set_dict = {
            "piece_id":piece[0],
            "piece_name":clean_html_codes(piece[1]),
            "colour_id":piece[2],
            "quantity":piece[3],
            "img_path":f"App/pieces/{piece[2]}_{piece[0]}.png",
        }
        pieces_dicts.append(set_dict)
    return pieces_dicts


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


def format_biggest_theme_trends(themes):
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


def get_login_error_message(form):
    error = str(form.errors)
    errors = list(filter(lambda x:x != "</ul>", error.split("</li>")))

    if "Enter a valid email address" in error:
        error_msg = "Invalid Email"

    elif "Ensure this value has at most" in error:
        max_chars = error.split("Ensure this value has at most ")[1].split(" characters")[0]
        field = error.split('<ul class="errorlist"><li>')[1]
        error_msg = f"{field.capitalize()} has a maximum length of {max_chars} characters."
    else:
        error_msg = "Please fill in all required fields (*)"
    return error_msg


def validate_username(username):
    pass


def sort_items(items, sort , **order) -> list[dict]:
    sort_field = sort.split("-")[0]
    order = {"asc":False, "desc":True}[sort.split("-")[1]]
    items = sorted(items, key=lambda field:field[sort_field], reverse=order)
    return items


def sort_dropdown_options(options:list[dict[str,str]], field:str) -> list[dict[str,str]]:
    #loop through all options. If options["value"] matches to desired sort field, assign to variable
    selected_field = [option for option in options if option["value"] == field]

    #default, if code above fails 
    if selected_field == []:
        print("\n\nFAILS - <sort_dropdown_options>\n\n")
        selected_field = options[0]
    else:
        selected_field = selected_field[0]
    
    #push selected element to front of list, remove its old position
    options.insert(0, options.pop(options.index(selected_field)))
    
    return options


def get_sub_themes(user_id:int, parent_themes:list[str], themes:list[dict], indent:int, view:str, metric:str) -> list[str]:

    indent += 1
    for theme in parent_themes:
        sub_themes = DB.sub_themes(user_id, theme[0], view, metric, metric_total=True, count=True)
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


def check_page_boundaries(current_page, list_len:int, items_per_page:int) -> int:

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


def shorten_len_return_value(_list:list) -> int:
    #shorten combinations if too many words to parse through
    length_convert = {
        len(_list) < 5:1,
        len(_list) >= 5 and len(_list) < 9: 2,
        len(_list) >= 9:3
    }
    return length_convert[True]


def similar_items_iterate(single_words:list[str], item_name:str, item_type:str, item_id:str, items:list[str], combinations:int) -> tuple[int, list]:
    for sub in itertools.combinations(single_words, combinations):
        sql_like = "AND " + ''.join([f"item_name LIKE '%{word}%' AND " for word in sub])[:-4]
        new_items = DB.get_similar_items(item_name, item_type, item_id, sql_like)

        for item in new_items:
            if len(items) < MAX_SIMILAR_ITEMS and item not in items:
                items.append(item)
                if len(items) >= MAX_SIMILAR_ITEMS:
                    return combinations, list(dict.fromkeys(items))

        if len(sub) <= 3 and len(items) >= 3:
            return combinations, items

    return combinations, []


def get_similar_items(item_name:str, item_type:str, item_id:str) -> list:

    item_type = DB.get_item_type(item_id)
    remove_words = list(DB.get_most_common_words("item_name", item_type, ',', '(', ')', min_word_length=2, limit=25))
    remove_words = extend_remove_words(remove_words, COLOURS, EXTRA_WORDS)

    single_words = [
        word.translate(''.join(REMOVE_CHARS)) for word in item_name.split(" ") 
        if len(word) > 3 and word.translate(''.join(REMOVE_CHARS)) not in remove_words
    ]

    items = []

    combinations = len(single_words)
    combinations = combinations // shorten_len_return_value(single_words)
    
    #set limit for substring combinations
    if combinations > 3:
        combinations = 3

    while True:
        combinations, items = similar_items_iterate(single_words, item_name, item_type, item_id, items, combinations)

        if len(items) >= MAX_SIMILAR_ITEMS or combinations <= 1:
            break

        combinations -= 1
    return items[:MAX_SIMILAR_ITEMS]


def split_capitalize(string:str, split_value:str):
    return " ".join(list(map(str.capitalize, string.split(split_value))))


def format_metric_changes(metrics) -> list[dict]:
    changes = {
        split_capitalize(ALL_METRICS[i], "_") : change
    for i, change in enumerate(metrics)}

    return changes


def filter_out_metric_filters(metric_filters, items) -> list:

    if len(items) == 0:
        return []
    
    if type(items[0]) == dict:
        keys = {
            "avg_price":"avg_price",
            "min_price":"min_price",
            "max_price":"max_price",
            "total_quantity":"total_quantity",
        }
    else:
        keys = {
            "avg_price":4,
            "min_price":5,
            "max_price":6,
            "total_quantity":7,
        }

    for metric in metric_filters:
        for limit in ["min", "max"]:
            if limit == "min" and metric_filters[metric][limit] != -1:
                items = list(filter(lambda x:x[keys[metric]] > metric_filters[metric][limit], items))
            elif limit == "max" and metric_filters[metric][limit] != -1:
                items = list(filter(lambda x:x[keys[metric]] < metric_filters[metric][limit], items)) 
    return items 


def set_default_metric_filters(request):
    request.session["metric_filters"] = {metric :  {"min":-1, "max":-1} for metric in ALL_METRICS}
    return request


def process_theme_filters(request):
    #el request.session["filtered_themes"]
    if "filtered_themes" not in request.session:
        request.session["filtered_themes"] = []


    themes = request.session.get("themes", [])
    selected_theme = request.POST.get("theme-filter")


    for sub_theme in themes[themes.index(selected_theme)+1:]:
        if selected_theme in request.session["filtered_themes"]:
            if selected_theme.count("~") < sub_theme.count("~"):
                if sub_theme in request.session["filtered_themes"]:
                    request.session["filtered_themes"].remove(sub_theme)
            else:
                break
        else:
            if selected_theme.count("~") < sub_theme.count("~"):
                if sub_theme not in request.session["filtered_themes"]:
                    request.session["filtered_themes"].append(sub_theme)
            else:
                break

    if selected_theme not in request.session["filtered_themes"]:
        request.session["filtered_themes"].append(selected_theme)
    else:
        request.session["filtered_themes"].remove(selected_theme)
    request.session.modified = True
    return request


def process_metric_filters(request):
    if "metric_filters" not in request.session:
        request = set_default_metric_filters(request)

    for metric in ALL_METRICS:
        for limit in ["min", "max"]:

            if request.POST.get(f"{metric}_{limit}") != None and request.POST.get(f"{metric}_{limit}") != '':
                try:
                    _input = float(request.POST.get(f"{metric}_{limit}"))
                except:
                    _input = 0
                request.session["metric_filters"][metric][limit] = _input
                request.session.modified = True
    return request


def process_recently_viewed_items(request, item_id):
    if "recently-viewed" not in request.session:
        request.session["recently-viewed"] = [item_id]
    else:
        if item_id in request.session["recently-viewed"]:
            request.session["recently-viewed"].remove(item_id)

        request.session["recently-viewed"].insert(0, item_id)

        if len(request.session["recently-viewed"]) > RECENTLY_VIEWED_ITEMS_NUM:
            request.session["recently-viewed"].pop()

        request.session.modified = True
    return request


def get_theme_paths(request):
    url = request.get_full_path()
    url = url.replace("/search/", "")
    urls = url.split("/")
    urls.insert(0, "All")
    urls.remove('')

    theme_paths = [{"theme":theme, "url":'/'.join([urls[x+1] for x in range(i)])} for i, theme in enumerate(urls)]  
    return theme_paths


def is_login_blocked(request, username):
    login_blocked = False
    if username in request.session.get("login_attempts") and request.session["login_attempts"][username]["login_retry_date"] != -1:
        login_retry_date = datetime.datetime.strptime(request.session["login_attempts"][username]["login_retry_date"].strip('"'), '%Y-%m-%d %H:%M:%S')
        if dt.today() > login_retry_date: 
            login_blocked = False
        else:
            login_blocked = True
    return login_blocked



def process_filters(request, items, user_id, view):
    filtered_themes = request.session.get("filtered_themes", [])

    no_items = False
    if len(items) == 0:
        no_items = True

    if filtered_themes != [] and len(items) != 0:

        #set key if items have / have not been formatted into dict
        if type(items[0]) == dict:
            key = "item_id"
        else:
            key = 0

        items_to_filter_by_theme = DB.filter_items_by_theme(filtered_themes, view, user_id)
        items = list(filter(lambda x:x[key] in items_to_filter_by_theme, items))
    
    if "metric_filters" not in request.session:
        request.session["metric_filters"] = {metric :  {"min":-1, "max":-1} for metric in ALL_METRICS}
    metric_filters = request.session["metric_filters"]

    items = filter_out_metric_filters(metric_filters, items)
    return {
        "no_items":no_items, "request":request, "items":items, 
        "filtered_themes":filtered_themes, "metric_filters":metric_filters
    }


def clear_filters(request, view):
    if view not in request.META.get('HTTP_REFERER', ""):
        request = set_default_metric_filters(request)
        request.session["filtered_themes"] = []
    request.session.modified = True
    return request