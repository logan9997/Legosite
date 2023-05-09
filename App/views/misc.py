from django.shortcuts import redirect
from App.models import Item

from utils.general import General

GENERAL = General()

def search_item(request, current_view):
    #get a list of all item ids that exist inside the database 
    item_ids = Item.objects.all().values_list("item_id",flat=True)
    
    #get item from the search bar, if it exists redirect to that items info page
    selected_item = request.POST.get("item_id")

    if selected_item in item_ids:
        return redirect(f"http://{GENERAL.get_base_url(request)}/item/{selected_item}")
    return redirect(f"{current_view}")
