from django.db.models import Q
from django.shortcuts import (
    redirect, 
    render
)

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.database import DatabaseManagment

from utils.item_format import Formatter
from utils.general import General 
from utils.filters import (
    FilterOut, 
    ClearFilter, 
    ProcessFilter
)
from config import (
    SEARCH_ITEMS_PER_PAGE,
    METRIC_INPUT_STEPS,
    ALL_METRICS,
    get_graph_options,
    get_sort_options
)

from App.models import (
    Theme
)


GENERAL = General()
FORMATTER = Formatter()
DB = DatabaseManagment()
FILTER_OUT = FilterOut()
CLEAR_FILTER = ClearFilter()
PROCESS_FILTER = ProcessFilter()


def search(request, theme_path='all'):

    request = CLEAR_FILTER.clear_filters(request, "search")

    if 'all' in request.path:
        return redirect(request.path.replace("all/", ""))

    graph_metric = request.session.get("graph_metric", "avg_price")
    sort_field = request.session.get("sort_field", "avg_price-desc")
    current_page = int(request.session.get("current_page",1)) 

    user_id = request.session.get("user_id", -1)
    request.session["theme_path"] = theme_path

    if theme_path == 'all':
        sub_themes = [{"sub_theme":theme[0], "img_path":f"App/sets/{theme[1]}.png"} for theme in DB.get_sub_theme_set('', 0)]
        
        theme_items = [] 
    else:
        theme_items = DB.get_theme_items(theme_path.replace("/", "~"), sort_field.split("-"))

        filter_results = PROCESS_FILTER.process_filters(request, theme_items, user_id, "item")
        request = filter_results["return"]["request"]
        theme_items = filter_results["return"]["items"]

        current_page = GENERAL.check_page_boundaries(current_page, len(theme_items), SEARCH_ITEMS_PER_PAGE)
        theme_items = theme_items[(current_page-1) * SEARCH_ITEMS_PER_PAGE : (current_page) * SEARCH_ITEMS_PER_PAGE]        
        theme_items = FORMATTER.format_item_info(theme_items,graph_data=[graph_metric] ,user_id=user_id)

        if len(theme_items) == 0:
            pass
            #redirect_path = "".join([f"{sub_theme}/" for sub_theme in theme_path.split("/")][:-1])
            #return redirect(f"http://{base_url(request)}/search/{redirect_path}")
    
        sub_theme_indent = request.path.replace("/search/", "").count("/")
        sub_themes = [{"sub_theme":theme[0].split("~")[sub_theme_indent], "img_path":f"App/sets/{theme[1]}.png"} for theme in DB.get_sub_theme_set(theme_path.replace("/", "~"), sub_theme_indent)]



    total_theme_items = Theme.objects.filter(theme_path=theme_path.replace("/", "~"), item__item_type="M").count()

    #remove first theme (parent theme)
    themes = list(Theme.objects.filter(
        item_id__in=DB.get_starwars_ids(),
        theme_path__contains=theme_path.replace("/", "~")
    ).values_list("theme_path", flat=True).distinct("theme_path"))[1:]

    themes_formatted = [{"theme_path":theme} for theme in themes]

    current_page = GENERAL.check_page_boundaries(current_page, total_theme_items, SEARCH_ITEMS_PER_PAGE)
    page_numbers = GENERAL.slice_num_pages(total_theme_items, current_page, SEARCH_ITEMS_PER_PAGE)

    graph_options = GENERAL.sort_dropdown_options(get_graph_options(), graph_metric)
    sort_options = GENERAL.sort_dropdown_options(get_sort_options(), sort_field)

    theme_items = GENERAL.sort_items(theme_items,sort_field)

    theme_paths = get_theme_paths(request)

    biggest_theme_trends = DB.biggest_theme_trends("avg_price")

    context = {
        "show_graph":True,
        "current_page":current_page,
        "num_pages":page_numbers,
        "theme_path":theme_path,
        "sub_themes":sub_themes,
        "theme_items":theme_items,
        "graph_options":graph_options,
        "sort_options":sort_options,
        "biggest_theme_trends":FORMATTER.format_biggest_theme_trends(biggest_theme_trends),
        "theme_paths":theme_paths,
        "all_metrics":ALL_METRICS,
        "metric_input_steps":METRIC_INPUT_STEPS,
        "themes":themes_formatted,
        "base_url":f"{GENERAL.get_base_url(request)}/search",
    }

    if theme_items != []:
        context.update(filter_results["context"])    
    return render(request, "App/search.html", context=context)
    
    
def search_POST(request):


    theme_path = request.session.get("theme_path", "")

    graph_metric = request.session.get("graph-metric", "avg_price")
    sort_field = request.session.get("sort-field", "avg_price-desc")
    current_page = int(request.session.get("page", 1))

    request.session["graph_metric"] = graph_metric
    request.session["sort_field"] = sort_field
    request.session["current_page"] = current_page
    return redirect(f"http://{GENERAL.get_base_url(request)}/search/{theme_path}")


def get_theme_paths(request):
    url = request.get_full_path()
    url = url.replace("/search/", "")
    urls = url.split("/")
    urls.insert(0, "All")
    urls.remove('')

    theme_paths = [{"theme":theme, "url":'/'.join([urls[x+1] for x in range(i)])} for i, theme in enumerate(urls)]  
    return theme_paths