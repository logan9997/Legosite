from django.shortcuts import (
    redirect, 
    render
)

from scripts.database import DatabaseManagment

from project_utils.item_format import Formatter
from project_utils.general import General 
from project_utils.filters import (
    FilterOut, 
    ClearFilter, 
    ProcessFilter
)
from config.config import (
    METRIC_INPUT_STEPS,
    ALL_METRICS,
    TRENDING_ITEMS_PER_PAGE,
    get_graph_options,
    get_trending_options,
)

from App.models import (
    Theme,
    Price
)


GENERAL = General()
FORMATTER = Formatter()
DB = DatabaseManagment()
FILTER_OUT = FilterOut()
CLEAR_FILTER = ClearFilter()
PROCESS_FILTER = ProcessFilter()


def trending(request):
    user_id = request.session.get("user_id", -1)

    trending_order:str = request.session.get("trending_order", "avg_price-desc") 
    trending_metric = trending_order.split("-")[0]
    current_page = int(request.session.get("current_page", 1))

    request = CLEAR_FILTER.clear_filters(request)

    graph_options = GENERAL.sort_dropdown_options(get_graph_options(), trending_metric)
    trend_options = GENERAL.sort_dropdown_options(get_trending_options(), trending_order)

    dates = list(Price.objects.distinct("date").values_list("date", flat=True))
    dates = [date.strftime('%Y-%m-%d') for date in dates]

    slider_start_value = int(request.session.get("slider_start_value", 0))
    slider_end_value = int(request.session.get("slider_end_value", len(dates)-1))

    min_date = dates[slider_start_value]
    max_date = dates[slider_end_value]

    items = DB.get_biggest_trends(trending_metric, max_date=max_date, min_date=min_date)

    #remove trending items if % change (-1) is equal to None (0.00)
    items = [_item for _item in items if _item[-1] != None]

    themes = list(Theme.objects.filter(theme_path__startswith="Star_Wars").values_list("theme_path", flat=True).distinct("theme_path"))
    themes_formatted = [{"theme_path":theme} for theme in themes]

    filter_results = FILTER_OUT.process_filters(request, items, user_id, "item")
    items = filter_results["return"]["items"]
    request = filter_results["return"]["request"]

    current_page = GENERAL.check_page_boundaries(current_page, len(items), TRENDING_ITEMS_PER_PAGE)

    num_pages = GENERAL.slice_num_pages(len(items), current_page, TRENDING_ITEMS_PER_PAGE)

    items = items[(current_page-1) * TRENDING_ITEMS_PER_PAGE : (current_page) * TRENDING_ITEMS_PER_PAGE]

    items = FORMATTER.format_item_info(items, metric_trends=[trending_metric], graph_data=[trending_metric])
    
    for _item in items:
        metrics = [DB.get_item_metric_changes(_item["item_id"], metric, max_date=max_date, min_date=min_date) for metric in ALL_METRICS]
        metrics = FORMATTER.format_metric_changes(metrics)
        _item["metric_changes"] = metrics

    request.session["themes"] = themes

    context = {
        "items":items,
        "show_graph":True,
        "graph_options":graph_options,
        "sort_options":trend_options,
        "num_pages":num_pages,
        "current_page":current_page,
        "dates":dates,
        "metric_data":trending_metric,
        "slider_start_value":slider_start_value,
        "slider_end_value":slider_end_value,
        "slider_start_max_value":slider_end_value - 1,
        "slider_end_max_value":len(dates) -1,
        "slider_start_min_value":0,
        "slider_end_min_value":slider_start_value + 1,
        "all_metrics":ALL_METRICS,
        "metric_input_steps":METRIC_INPUT_STEPS,
        "themes":themes_formatted,
        "winners_losers_filter":request.session.get("winners_losers_filter")
    }

    context.update(filter_results["context"])

    return render(request, "App/trending.html", context=context)


def trending_POST(request):

    if request.POST.get("form-type") == "graph-metric-form":    
        graph_metric = request.POST.get("graph-metric")
        request.session["graph_metric"] = graph_metric

    elif request.POST.get("form-type") == "sort-form":
        trending_order = request.POST.get("sort-field")
        request.session["trending_order"] = trending_order

    elif request.POST.get("form-type") == "page-buttons-form":
        current_page = request.POST.get("page")
        request.session["current_page"] = current_page


    elif request.POST.get("form-type") == "sliders-form":
        dates = list(Price.objects.distinct("date").values_list("date", flat=True))

        slider_start_value = request.POST.get("slider_start", 0)
        slider_end_value = request.POST.get("slider_end", len(dates)-1)

        request.session["slider_start_value"] = slider_start_value
        request.session["slider_end_value"] = slider_end_value

    return redirect("trending")