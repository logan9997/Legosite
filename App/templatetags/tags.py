from django import template
from django.utils.safestring import mark_safe
from ..models import User, Item, Theme

from config.config import (
    MAX_GRAPH_POINTS_ITEM_VIEW,
    MAX_GRAPH_POINTS,
    MAX_SEARCH_SUGGESTIONS,
    ITEM_TYPE_CONVERT
)
import json

register = template.Library()

#add login status to base.html to either display (logout) / (login + join) in the nav bar
@register.simple_tag(takes_context=True)
def check_login_status(context, request):
    try:
        if request.session["user_id"] != -1:
            context["logged_in"] = True
        else:
            context["logged_in"] = False
    except KeyError:
        context["logged_in"] = False
    return ''


@register.simple_tag
def get_max_graph_points(request):
    if "/item/" in request.get_full_path():
        return MAX_GRAPH_POINTS_ITEM_VIEW
    return MAX_GRAPH_POINTS


@register.simple_tag
def max_search_suggestions():
    return MAX_SEARCH_SUGGESTIONS


@register.simple_tag
def item_details_search_suggestions():
    details = list(Item.objects.filter(
        theme__theme_path__contains="Star_Wars", 
        ).values_list("item_id", "item_name", "item_type").distinct("item_id"))
    
    return [{"item_id":detail[0].lower(), "item_name":detail[1].lower(), "item_type":ITEM_TYPE_CONVERT[detail[2]]} for detail in details]


@register.simple_tag
def item_names():
    names = list(map(str.lower, Item.objects.filter(
        theme__theme_path__contains="Star_Wars", 
    ).values_list("item_name", flat=True).distinct("item_id")))

    return ["".join([char for char in name if char not in [")", "(", ",", "-", "."]]) for name in names]


@register.filter
def iterable_index(list:list, i:int):
    if i == len(list):
        return list[i-1]
    return list[i]


@register.filter
def large_num_commas(number):
    number = str(number)
    if "." in number:
        num_int = number.split(".")[0]
        num_decimal = "." + number.split(".")[1]
    else:
        num_int = number
        num_decimal = ""

    sections = []

    remainder = len(num_int) % 3
    if remainder != 0:
        sections.append(num_int[:remainder])
        num_int = num_int[remainder:]

    for i in range(len(num_int)):
        if (i % 3) == 0:
            sections.append(num_int[i:i+3])

    number = ",".join(sections)+num_decimal
    return number

@register.simple_tag(takes_context=True)
def add_username_email_to_context(context, request):
    try: 
        user_id = request.session["user_id"]
        if user_id != -1:
            user_details = User.objects.filter(user_id=user_id)
            context["username"] = user_details.values_list("username", flat=True)[0]
            context["email"] = user_details.values_list("email", flat=True)[0]
    except KeyError:
        return ''
    return ''


@register.filter
def postivie_or_negative_sign(num:float):
    if num == None:
        return 0
    if num > 0:
        num = f"+{str(num)}"
    return num


@register.filter
def times_negative_one(number:float):
    if number < 0:
        return number *-1
    return number


@register.filter
def none_to_hyphens(date):
    if date == None:
        return " - - - -"
    return date


@register.filter
def none_to_empty_string(string):
    if string == None:
        return ''
    return string


@register.filter
def none_to_zero(num):
    if num == None or num == "":
        return 0
    return num


@register.filter
def index(iterable, item):
    return iterable.index(item) + 1


@register.filter
def capitalise_split_words(string:str):
    return ' '.join([word.capitalize() for word in string.split("_")])


@register.filter
def shorten_long_number(number:float):

    if number >= 1000:
        return str(number).split(".")[0]
    return number


@register.filter
def remove_decimals(number:float):
    return int(number)


@register.filter
def two_decimals(number:float):
    if "." in str(number):
        if len(str(number).split(".")[1]) == 1:
            return str(number).split(".")[0] + "." + str(number).split(".")[1] + "0"
    return number


@register.filter
def replace_underscore(string:str):
    return string.replace("_", " ")


@register.filter
def replace_forward_slash(string:str):
    if string == "/":
        return "index"

    return string.replace("/", "")


@register.filter
def replace_space_substitute(string:str):
    return string.replace("~", ",  ").replace("_", " ")


@register.filter
def item_themes(string:str):
    string = string.replace("_", " ")
    if "~" in string:
        string = "-- " + string.split("~")[1]
    return string


@register.filter
def split(string:str, split_value:str):
    return string.split(split_value)


@register.filter()
def append(_list:list, value):
    return _list.append(value)


@register.filter
def strip(string:str, sub_string:str):
    return string.strip(sub_string)


@register.filter
def replace(string:str, replace_args:str):

    replace_args = replace_args.split("|")
    if len(replace_args) != 2:
        return string.replace(replace_args[0])
    
    old_str, new_str = replace_args

    return string.replace(old_str, new_str)


@register.filter
def get_item(_dict:dict, key:str):
    return dict(_dict).get(key)


@register.filter
def count(string:str, sub_string:str) -> int:
    return string.count(sub_string)


@register.filter
def get_indent_colour(theme_path:str):
    indent = theme_path.count("~") + 1
    return f"rgb(255, {45 * indent}, {10 * indent * indent})"


@register.filter
def count_theme_indent(theme_path:str):
    indent = theme_path.count("~")
    parent_theme = theme_path.split("~")[0]
    desired_indent = 2

    if indent <= desired_indent and parent_theme in theme_path:
        return "-"*(indent*2) + " " + theme_path.split("~")[-1].replace("_", " ").replace("~", " ")
    return ''


@register.filter
def absolute_value(num):
    return abs(num)


@register.filter
def capitalise(string:str):
    return string.capitalize()


@register.filter(is_safe=True)
def js(obj):
    return mark_safe(json.dumps(obj))