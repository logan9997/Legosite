from django.db.models import F
from django.shortcuts import (
    render
)

from datetime import datetime as dt
from datetime import timedelta 

from scripts.database import DatabaseManagment

from project_utils.item_format import Formatter
from project_utils.general import General 
from config.config import (
    RECENTLY_VIEWED_ITEMS_NUM,
    get_graph_options,
)

from App.models import User

GENERAL = General()
FORMATTER = Formatter()
DB = DatabaseManagment()

def index(request):

    if "user_id" not in request.session:
        request.session["user_id"] = -1
    user_id = request.session["user_id"]

    graph_options = get_graph_options()
    graph_metric = request.POST.get("graph-metric", "avg_price")
    graph_options = GENERAL.sort_dropdown_options(graph_options, graph_metric)

    #if the user has no recently viewed items create a new emtpy list to store items in the future
    if "recently-viewed" not in request.session or user_id == -1:
        request.session["recently-viewed"] = []

    recently_viewed_ids = request.session["recently-viewed"][:RECENTLY_VIEWED_ITEMS_NUM]
    recently_viewed = [DB.get_item_info(item_id, "avg_price")[0] for item_id in recently_viewed_ids]

    recently_viewed = FORMATTER.format_item_info(recently_viewed, graph_data=[graph_metric], user_id=user_id)
    popular_items = FORMATTER.format_item_info(DB.get_popular_items()[:10], weekly_views=8, item_group="_popular_items", graph_data=[graph_metric])
    new_items = FORMATTER.format_item_info(DB.get_new_items()[:10], item_group="_new_items", graph_data=[graph_metric])[:10]

    last_week = dt.today() - timedelta(days=7)
    last_week = last_week.strftime('%Y-%m-%d')

    for popular_item in popular_items:
        popular_item["change"] = round(DB.get_weekly_item_metric_change(popular_item["item_id"], last_week, graph_metric), 2)

    username = User.objects.filter(user_id=user_id).values_list("username", flat=True)

    context = {
        "username":username,
        "graph_options":graph_options,
        "last_week":last_week,
        "popular_items":popular_items,
        "new_items":new_items,
        "recently_viewed":recently_viewed,
        "show_graph":False,
        "metric":graph_metric,
    }

    if user_id == -1 or len(DB.get_user_items(user_id, "portfolio")) == 0:
        context["portfolio_trending_items"] = False
        context["trending"] = FORMATTER.format_item_info(DB.get_biggest_trends(graph_metric, limit=10), metric_trends=[graph_metric], graph_data=[graph_metric], user_id=user_id)
    else:
        context["portfolio_trending_items"] = True
        context["trending"] = FORMATTER.format_item_info(DB.biggest_portfolio_changes(user_id, graph_metric), graph_data=[graph_metric])


    return render(request, "App/home.html", context=context)