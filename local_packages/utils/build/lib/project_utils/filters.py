from scripts.database import DatabaseManagment
from config.config import ALL_METRICS
from .general import General  


DB = DatabaseManagment()
GENERAL = General()


class FilterOut():

    def process_filters(self, request, items, user_id, view):
    
        filters = [
            self.filter_out_theme_filters(request, items, user_id, view),
            self.filter_out_item_type_filters(request, items),
            self.filter_out_metric_filters(request, items),
            self.filter_out_winners_losers_filters(request, items)
        ]

        print(filters)

        for filter in filters:
            if len(items) != 0 :
                request, items = filter 

        context = {
            "filtered_themes":request.session.get("filtered_themes"), 
            "metric_filters":request.session.get("metric_filters"),
            "item_type_filter":request.session.get("item_type_filter")
        }

        return_values = {
            "request":request, 
            "items":items
        }

        return {"context":context, "return":return_values}
    
    def filter_out_theme_filters(self, request, items, user_id, view):

        filtered_themes = request.session.get("filtered_themes", [])
        if filtered_themes != []:
            if type(items[0]) == dict:
                item_id_key = "item_id"
            else:
                item_id_key = 0

            items_to_filter_by_theme = DB.filter_items_by_theme(filtered_themes, view, user_id)
            items = list(filter(lambda x:x[item_id_key] in items_to_filter_by_theme, items))
        return request, items


    def filter_out_item_type_filters(self, request, items):

        item_type_filter = request.session.get("item_type_filter")

        if type(items[0]) == dict:
            item_type_key = "item_type"
        else:
            item_type_key = 3

        if item_type_filter not in ["All", None]:
            items = list(filter(lambda x:x[item_type_key] == item_type_filter, items))

        return request, items


    def filter_out_winners_losers_filters(self, request, items):

        winners_or_losers = request.session.get("winners_losers_filter", "All")
        metric = request.session.get("trending_order", "avg_price-desc").split("-")[0]
        metric = GENERAL.split_capitalize(metric, "_")

        if winners_or_losers == "Winners":
            items = list(filter(lambda x:x[-1] > 0 , items))
        elif winners_or_losers == "Losers":
            items = list(filter(lambda x:x[-1] < 0 , items))
        return request, items
    
    
    def filter_out_metric_filters(self, request, items) -> list:
        
        if "metric_filters" not in request.session:
            request.session["metric_filters"] = {metric :  {"min":-1, "max":-1} for metric in ALL_METRICS}
        metric_filters = request.session["metric_filters"]
        
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
        
        return request, items 

    
class ProcessFilter():

    def process_theme_filters(self, request):
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


    def process_metric_filters(self, request):
        if "metric_filters" not in request.session:
            request = self.set_default_metric_filters(request)

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
    
    def set_default_metric_filters(self, request):
        request.session["metric_filters"] = {metric :  {"min":-1, "max":-1} for metric in ALL_METRICS}
        return request


class ClearFilter():

    def clear_filters(self, request):
        print(request.META.get('HTTP_REFERER', ""),"\n",f"{GENERAL.get_base_url(request)}{request.get_full_path()}")
        if f"{GENERAL.get_base_url(request)}{request.get_full_path()}" != request.META.get('HTTP_REFERER', "").replace("http://", ""):
            request = ProcessFilter().set_default_metric_filters(request)
            request.session["filtered_themes"] = []
        request.session.modified = True
        return request

