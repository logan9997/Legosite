from django.shortcuts import (
    redirect, 
    render
)

from scripts.database import DatabaseManagement

from project_utils.item_format import Formatter
from project_utils.general import General
from project_utils.filters import (
    FilterOut, 
    ClearFilter, 
    ProcessFilter
)
from config.config import (
    SEARCH_ITEMS_PER_PAGE,
    METRIC_INPUT_STEPS,
    ALL_METRICS,
    get_graph_options,
    get_sort_options
)

from App.models import (
    Theme
)

DB = DatabaseManagement()
GENERAL = General()
FORMATTER = Formatter()
FILTER_OUT = FilterOut()
CLEAR_FILTER = ClearFilter()
PROCESS_FILTER = ProcessFilter()

def search(request, theme_path='all'):

    # request = CLEAR_FILTER.clear_filters(request)

    get_params = [
        'sort-field', 'graph-metric', 'page', 'slider_start_value', 'slider_end_value', 
    ]

    request = GENERAL.process_sorts_and_pages(request, get_params)
    request = PROCESS_FILTER.save_filters(request)

    if request.POST.get('clear-form') != None:
        request = CLEAR_FILTER.clear_filters(request)
        
    if 'all' in request.path:
        return redirect(request.path.replace("all/", ""))

    graph_metric = request.session.get("graph-metric", "avg_price")
    sort_field = request.session.get("sort-field", "avg_price-desc")
    current_page = int(request.session.get("page",1))

    user_id = request.session.get("user_id", -1)
    request.session["theme_path"] = theme_path

    if theme_path == 'all':
        sub_themes = [{"sub_theme":theme[0], "img_path":f"App/sets/{theme[1]}.png"} for theme in DB.get_sub_theme_set('', 0)]
        
        theme_items = [] 
    else:
        theme_items = DB.get_theme_items(theme_path.replace("/", "~"), sort_field.split("-"))

        filter_results = FILTER_OUT.process_filters(request, theme_items)
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
        item_id__in=DB.get_all_starwars_items(),
        theme_path__contains=theme_path.replace("/", "~")
    ).values_list("theme_path", flat=True).distinct("theme_path"))[1:]


    context = {
        "show_graph":True,
        "current_page":GENERAL.check_page_boundaries(current_page, total_theme_items, SEARCH_ITEMS_PER_PAGE),
        "num_pages": GENERAL.slice_num_pages(total_theme_items, current_page, SEARCH_ITEMS_PER_PAGE),
        "theme_path":theme_path,
        "sub_themes":sub_themes,
        "theme_items":GENERAL.sort_items(theme_items,sort_field),
        "graph_options":GENERAL.sort_dropdown_options(get_graph_options(), graph_metric),
        "sort_options": GENERAL.sort_dropdown_options(get_sort_options(), sort_field),
        "biggest_theme_trends":FORMATTER.format_biggest_theme_trends(DB.biggest_theme_trends("avg_price")),
        "theme_paths":get_theme_paths(request),
        "all_metrics":ALL_METRICS,
        "metric_input_steps":METRIC_INPUT_STEPS,
        "themes":[{"theme_path":theme} for theme in themes],
        "base_url":f"{GENERAL.get_base_url(request)}/search",
    }

    if theme_items != []:
        context.update(filter_results["context"])    
    return render(request, "App/search.html", context=context)
    
    

def get_theme_paths(request):
    url = request.path
    url = url.replace("/search/", "")
    urls = url.split("/")
    urls.insert(0, "All")

    theme_paths = [
        {"theme":theme, "url":'/'.join([urls[x+1] for x in range(i)])} 
        for i, theme in enumerate(urls)
    ]  
    return theme_paths