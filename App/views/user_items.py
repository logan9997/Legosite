from django.db.models import (
    Sum,
    Count,
    Max
)
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
    USER_ITEMS_ITEMS_PER_PAGE,
    METRIC_INPUT_STEPS,
    ALL_METRICS,
    get_graph_options,
    get_sort_options
)

from App.models import (
    Portfolio,
    Watchlist,
    Price,
)

from App.forms import (
    AddItemToPortfolio,
    AddOrRemovePortfolioItem
)

from datetime import datetime as dt

DB = DatabaseManagement()
GENERAL = General()
FORMATTER = Formatter()
FILTER_OUT = FilterOut()
PROCESS_FILTER = ProcessFilter()
CLEAR_FILTER = ClearFilter()


def user_items(request, view, user_id):

    get_params = [
        'sort-field', 'page', 'graph-metric' 
    ]

    request = GENERAL.process_sorts_and_pages(request, get_params)
    request = PROCESS_FILTER.save_filters(request)

    if request.POST.get('clear-form') != None:
        request = CLEAR_FILTER.clear_filters(request)

    graph_options = get_graph_options()
    sort_options = get_sort_options()

    graph_metric = request.session.get("graph-metric", "avg_price")
    current_page = int(request.session.get("page", 1))
    sort_field = request.session.get("sort-field", "avg_price-desc")

    items = DB.get_user_items(user_id, view)
    items = FORMATTER.format_item_info(items, owned_quantity_new=8, owned_quantity_used=9, graph_data=[graph_metric], user_id=user_id)

    parent_themes = DB.parent_themes(user_id, view, graph_metric)
    themes = get_sub_themes(user_id, parent_themes, [], -1, view, graph_metric)

    filter_results = FILTER_OUT.process_filters(request, items,  [theme['theme_path'] for theme in themes])
    items = filter_results["return"]["items"]
    request = filter_results["return"]["request"]

    current_page = GENERAL.check_page_boundaries(current_page, len(items), USER_ITEMS_ITEMS_PER_PAGE)
    num_pages = GENERAL.slice_num_pages(len(items), current_page, USER_ITEMS_ITEMS_PER_PAGE)

    items = GENERAL.sort_items(items, sort_field)
    #keep selected sort field option as first <option> tag
    sort_options = GENERAL.sort_dropdown_options(sort_options, sort_field)
    graph_options = GENERAL.sort_dropdown_options(graph_options, graph_metric)

    total_unique_items = len(items)
    metric_total = {
        "metric":GENERAL.split_capitalize(graph_metric, "_"),
        "total":DB.user_items_total_price(user_id, graph_metric, view) 
    }

    years_released = []
    [years_released.append(_item["year_released"]) for _item in items if _item["year_released"] not in years_released]

    items = items[(current_page - 1) * USER_ITEMS_ITEMS_PER_PAGE : int(current_page) * USER_ITEMS_ITEMS_PER_PAGE]



    context = {
        "items":items,
        "num_pages":num_pages,
        "sort_options":sort_options,
        "graph_options":graph_options,
        "themes":themes,
        "total_unique_items":total_unique_items,
        "metric_total":metric_total,
        "view":view,
        "graph_metric":graph_metric,
        "current_page":current_page,
        "show_graph":True,
        "user_id":user_id,
        "all_metrics":ALL_METRICS,
        "metric_input_steps":METRIC_INPUT_STEPS,
        "years_released":years_released,
    }

    context.update(filter_results["context"])

    return context


def view_POST(request, view):

    if "?item=" in request.META.get('HTTP_REFERER'):
        request.session["graph_metric"] = request.POST.get("graph-metric", "avg_price")
        request.session["graph_options"] = GENERAL.sort_dropdown_options(get_graph_options(), request.POST.get("graph-metric", "avg_price"))
        return redirect(request.META.get('HTTP_REFERER'))
    
    if "user_id" not in request.session or request.session["user_id"] == -1:
        return redirect("index")
    user_id = request.session["user_id"]

    items = DB.get_user_items(user_id, view=view)

    portfolio_items = FORMATTER.format_item_info(items, owned_quantity_new=8, owned_quantity_used=9)

    if request.POST.get("form-type") == "remove-or-add-portfolio-item":
        form = AddOrRemovePortfolioItem(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data["item_id"]
            remove_or_add = form.cleaned_data["remove_or_add"]
            condition = form.cleaned_data["condition"][0]
            quantity = int(form.cleaned_data["quantity"])

            if remove_or_add == "-":
                quantity *= -1

            if (item_id, condition) in [(_item["item_id"], _item["condition"]) for _item in portfolio_items]:
                DB.update_portfolio_item_quantity(user_id, item_id, condition, quantity)
            else:
                DB.add_to_user_items(item_id, user_id, view, condition=condition, quantity=quantity)

    if request.POST.get("form-type") == "remove-watchlist-item":
        item_id = request.POST.get("item_id")
        Watchlist.objects.filter(user_id=user_id, item_id=item_id).delete()

    item_id = request.GET.get("item")
    if item_id != None:
        return redirect(f"http://{GENERAL.get_base_url(request)}/{view}/?item={item_id}")
    return redirect(view)


def portfolio(request, item_id=None):

    if "user_id" not in request.session or request.session["user_id"] == -1:
        return redirect("index")
    user_id = request.session["user_id"]

    item_id = request.GET.get("item")
    
    context = user_items(request, "portfolio", user_id)

    context["total_items"] = Portfolio.objects.filter(user_id=user_id).count() 
    context["total_bought_price"] = Portfolio.objects.filter(user_id=user_id).aggregate(total_bought_for=Sum("bought_for", default=0))["total_bought_for"]
    context["total_sold_price"] = Portfolio.objects.filter(user_id=user_id).aggregate(total_sold_for=Sum("sold_for", default=0))["total_sold_for"]
    context["total_profit"] = round(Portfolio.objects.filter(user_id=user_id).aggregate(profit=Sum("bought_for", default=0) - Sum("sold_for", default=0))["profit"], 2)


    item_id = request.GET.get("item")
    if item_id != None:

        if len(Portfolio.objects.filter(user_id=user_id, item_id=item_id)) == 0:
            return redirect("portfolio")

        if "graph_metric" in request.session:
            context["graph_metric"] = request.session["graph_metric"]
            del request.session["graph_metric"]

        if "graph_options" in request.session:
            context["graph_options"] = request.session["graph_options"]
            del request.session["graph_options"]
      
        items = Portfolio.objects.filter(item_id=item_id, user_id=user_id).values_list("condition", "bought_for", "sold_for", "date_added", "date_sold", "notes", "portfolio_id")
        items = FORMATTER.format_portfolio_items(items)
        context["item_entries"] = items
        context["metric_changes"] = [{"metric":metric,"change":DB.get_item_metric_changes(item_id, metric)} for metric in ALL_METRICS]
        context["item"] = FORMATTER.format_item_info(DB.get_item_info(item_id, context["graph_metric"]), graph_data=[context["graph_metric"]], metric_trends=ALL_METRICS)[0]
        
        context["total_profit"] = round(Portfolio.objects.filter(user_id=user_id, item_id=item_id).aggregate(profit=Sum("sold_for", default=0) - Sum("bought_for", default=0))["profit"], 2)
        context["total_owners"] = len(Portfolio.objects.filter(item_id=item_id).aggregate(Count("user_id")))
        context["total_watchers"] = Watchlist.objects.filter(item_id=item_id).count()
        
        context["total_market_value"] = Price.objects.filter(
            item_id=item_id, date=Price.objects.filter(item_id=item_id).aggregate(Max("date"))["date__max"]
        ).values_list("avg_price", flat=True)[0] * Portfolio.objects.filter(item_id=item_id, user_id=user_id, date_sold=None).count()

        if len(Portfolio.objects.filter(item_id=item_id, user_id=user_id)) > 0:
            context["total_bought_price"] = Portfolio.objects.filter(item_id=item_id, user_id=user_id).aggregate(total_bought_for=Sum("bought_for", default=0))["total_bought_for"]
            context["total_sold_price"] = Portfolio.objects.filter(item_id=item_id, user_id=user_id).aggregate(total_sold_for=Sum("sold_for", default=0))["total_sold_for"] 

    return render(request, "App/portfolio.html", context=context)



def watchlist(request):

    if "user_id" not in request.session or request.session["user_id"] == -1:
        return redirect("index")
    user_id = request.session["user_id"]

    context = user_items(request, "watchlist", user_id)

    return render(request, "App/watchlist.html", context=context)


def add_to_user_items(request, item_id):

    view:str = request.POST.get("view-type")

    if "user_id" not in request.session or request.session["user_id"] == -1:
        return redirect("index")
    user_id = request.session["user_id"]

    user_item_ids = eval(view.capitalize()).objects.filter(user_id=user_id).values_list("item_id", flat=True).annotate(t=Count("item_id"))

    if view == "portfolio":
        form = AddItemToPortfolio(request.POST)
        if form.is_valid():
            condition = form.cleaned_data["condition"]
            quantity = form.cleaned_data["quantity"]
            bought_for = form.cleaned_data["bought_for"]
            date_added = form.cleaned_data["date_added"]

            for _ in range(quantity):
                DB.add_to_user_items(user_id, item_id, view,date_added, condition=condition, bought_for=bought_for)
    else:
        if item_id not in user_item_ids:
            DB.add_to_user_items(user_id, item_id, view, dt.today().strftime('%Y-%m-%d'))
        else:
            Watchlist.objects.filter(user_id=user_id, item_id=item_id).delete()
            
    return redirect(f"http://{GENERAL.get_base_url(request)}/item/{item_id}")



def entry_item_handler(request, view):
    item_id = request.POST.get("item_id")
    entry_id = request.POST.get("entry_id")

    if request.POST.get("remove-entry") != None:
        Portfolio.objects.filter(portfolio_id=entry_id).delete()
        if view == "portfolio":
            return redirect(f"http://{GENERAL.get_base_url(request)}/{view}/?item={item_id}")
        return redirect(f"http://{GENERAL.get_base_url(request)}/{view}/{item_id}/")
    

    elif "CLEAR" in request.POST.get("clear-input", ""):
        nulled_field = request.POST.get("clear-input").split("_CLEAR")[0]

        new_data = {nulled_field:None}
        if "_for" in nulled_field:
            new_data = {nulled_field:0}

        Portfolio.objects.filter(portfolio_id=entry_id).update(**new_data)
        if view == "portfolio":
            return redirect(f"http://{GENERAL.get_base_url(request)}/{view}/?item={item_id}")
        return redirect(f"http://{GENERAL.get_base_url(request)}/{view}/{item_id}/")
    

    elif request.POST.get("form-type") == "entry-edit":
        fields = {
            "date_added" : str(request.POST.get("date_added")),
            "bought_for" : float(request.POST.get("bought_for")),
            "date_sold" : str(request.POST.get("date_sold")),
            "sold_for" : float(request.POST.get("sold_for")),
            "notes" : str(request.POST.get("notes")),
        }

        #set fields in database to null rather than empty string
        for k, v in fields.items():
            if v == "":
                fields[k] = None

        Portfolio.objects.filter(portfolio_id=entry_id).update(**fields)
        return redirect(f"http://{GENERAL.get_base_url(request)}/{view}/?item={item_id}")
    
    elif request.POST.get("form-type") == "new-entry":
        values = {k:v for k,v in request.POST.items() if k not in ["csrfmiddlewaretoken", "form-type"] and v != ''}
        Portfolio(**values).save()
        if view == "portfolio":
            return redirect(f"http://{GENERAL.get_base_url(request)}/{view}/?item={item_id}")
        return redirect(f"http://{GENERAL.get_base_url(request)}/{view}/{item_id}/")


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