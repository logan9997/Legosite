from datetime import (
    datetime as dt, 
    timedelta
)

from django.shortcuts import render, redirect
from ..config import *
from ..utils._utils import *

from .forms import (
    AddItemToPortfolio, 
    PortfolioItemsSort, 
    LoginForm,
    SignupFrom,
    AddOrRemovePortfolioItem,
    ChangePassword,
    EmailPreferences,
    PersonalInfo,
    SearchSort,
)

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
    Max,
    F,
) 

from scripts.responses import * 
from scripts.database import *









def filters_POST(request, view):
    if request.POST.get("form-type") == "theme-filter":
        request = process_theme_filters(request)

    elif request.POST.get("form-type") == "metric-filter":
        request = process_metric_filters(request)

    elif request.POST.get("form-type") == "item-type-select":
        request.session["item_type_filter"] = request.POST.get("item-type-select")

    elif request.POST.get("form-type") == "winners-or-losers-filter":
        request.session["winners_losers_filter"] = request.POST.get("winners-or-losers-filter", "All")


    if request.POST.get("clear-form") == "clear-metric-filters":
        request = set_default_metric_filters(request)
    
    elif request.POST.get("clear-form") == "clear-theme-filters":
        request.session["filtered_themes"] = []

    if view == "search":
        return redirect(request.META.get('HTTP_REFERER'))

    return redirect(view)














def logout(request):
    '''
    rework sessions for specific user, need to associate recently viewed with a user_id
    otherwise recently viewed items still show after logging out
    '''
    del request.session["user_id"]
    return redirect("login")





def user_items(request, view, user_id):

    request = clear_filters(request, view)

    graph_options = get_graph_options()
    sort_options = get_sort_options()

    options = request.session.get("url_params", {})

    graph_metric = options.get("graph-metric", "avg_price")
    current_page = int(options.get("page", 1))
    sort_field = options.get("sort-field", "avg_price-desc")

    items = DB.get_user_items(user_id, view)
    items = format_item_info(items, owned_quantity_new=8, owned_quantity_used=9, graph_data=[graph_metric], user_id=user_id)

    parent_themes = DB.parent_themes(user_id, view, graph_metric)
    themes = get_sub_themes(user_id, parent_themes, [], -1, view, graph_metric)

    filter_results = process_filters(request, items, user_id, view)
    items = filter_results["return"]["items"]
    request = filter_results["return"]["request"]

    current_page = check_page_boundaries(current_page, len(items), USER_ITEMS_ITEMS_PER_PAGE)
    num_pages = slice_num_pages(len(items), current_page, USER_ITEMS_ITEMS_PER_PAGE)

    items = sort_items(items, sort_field)
    #keep selected sort field option as first <option> tag
    sort_options = sort_dropdown_options(sort_options, sort_field)
    graph_options = sort_dropdown_options(graph_options, graph_metric)

    total_unique_items = len(items)
    metric_total = {
        "metric":split_capitalize(graph_metric, "_"),
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
        request.session["graph_options"] = sort_dropdown_options(get_graph_options(), request.POST.get("graph-metric", "avg_price"))
        return redirect(request.META.get('HTTP_REFERER'))
    
    if "user_id" not in request.session or request.session["user_id"] == -1:
        return redirect("index")
    user_id = request.session["user_id"]

    items = DB.get_user_items(user_id, view=view)

    portfolio_items = format_item_info(items, owned_quantity_new=8, owned_quantity_used=9)

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

    request = save_POST_params(request)[0]
    item_id = request.GET.get("item")
    if item_id != None:
        return redirect(f"http://{base_url(request)}/{view}/?item={item_id}")


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
        items = format_portfolio_items(items)
        context["item_entries"] = items
        context["metric_changes"] = [{"metric":metric,"change":DB.get_item_metric_changes(item_id, metric)} for metric in ALL_METRICS]
        context["item"] = format_item_info(DB.get_item_info(item_id, context["graph_metric"]), graph_data=[context["graph_metric"]], metric_trends=ALL_METRICS)[0]
        
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
            DB.add_to_user_items(user_id, item_id, view, datetime.datetime.today().strftime('%Y-%m-%d'))
        else:
            Watchlist.objects.filter(user_id=user_id, item_id=item_id).delete()
            
    return redirect(f"http://{base_url(request)}/item/{item_id}")



def entry_item_handler(request, view):
    item_id = request.POST.get("item_id")
    entry_id = request.POST.get("entry_id")

    if request.POST.get("remove-entry") != None:
        Portfolio.objects.filter(portfolio_id=entry_id).delete()
        if view == "portfolio":
            return redirect(f"http://{base_url(request)}/{view}/?item={item_id}")
        return redirect(f"http://{base_url(request)}/{view}/{item_id}/")
    

    elif "CLEAR" in request.POST.get("clear-input", ""):
        nulled_field = request.POST.get("clear-input").split("_CLEAR")[0]

        new_data = {nulled_field:None}
        if "_for" in nulled_field:
            new_data = {nulled_field:0}

        Portfolio.objects.filter(portfolio_id=entry_id).update(**new_data)
        if view == "portfolio":
            return redirect(f"http://{base_url(request)}/{view}/?item={item_id}")
        return redirect(f"http://{base_url(request)}/{view}/{item_id}/")
    

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
        return redirect(f"http://{base_url(request)}/{view}/?item={item_id}")
    
    elif request.POST.get("form-type") == "new-entry":
        values = {k:v for k,v in request.POST.items() if k not in ["csrfmiddlewaretoken", "form-type"] and v != ''}
        Portfolio(**values).save()
        if view == "portfolio":
            return redirect(f"http://{base_url(request)}/{view}/?item={item_id}")
        return redirect(f"http://{base_url(request)}/{view}/{item_id}/")


