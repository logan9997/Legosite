from django.shortcuts import redirect
from App.models import Item

from project_utils.general import General 
from project_utils.filters import ProcessFilter


GENERAL = General()
PROCESS_FILTER = ProcessFilter()

def search_item(request, current_view):
    #get a list of all item ids that exist inside the database 
    item_ids = Item.objects.all().values_list("item_id",flat=True)
    
    #get item from the search bar, if it exists redirect to that items info page
    selected_item = request.POST.get("item_id")

    if selected_item in item_ids:
        return redirect(f"http://{GENERAL.get_base_url(request)}/item/{selected_item}")
    return redirect(f"{current_view}")


def update_filters_in_session(request, view):
    if request.POST.get("form-type") == "theme-filter":
        request = PROCESS_FILTER.process_theme_filters(request)

    elif request.POST.get("form-type") == "metric-filter":
        request = PROCESS_FILTER.process_metric_filters(request)

    elif request.POST.get("form-type") == "item-type-select":
        request.session["item_type_filter"] = request.POST.get("item-type-select")

    elif request.POST.get("form-type") == "winners-or-losers-filter":
        request.session["winners_losers_filter"] = request.POST.get("winners-or-losers-filter", "All")

    if request.POST.get("clear-form") == "clear-metric-filters":
        request = PROCESS_FILTER.set_default_metric_filters(request)
    
    elif request.POST.get("clear-form") == "clear-theme-filters":
        request.session["filtered_themes"] = []

    if view == "search":
        return redirect(request.META.get('HTTP_REFERER'))

    return redirect(view)


def logout(request):
    del request.session["user_id"]
    return redirect("login")