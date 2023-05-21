import math
import time
import itertools

from datetime import datetime as dt

from ..config import *









#AA







#AA
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





def save_POST_params(request) -> tuple[dict, dict]:
    if "url_params" in request.session:
        for k, v in request.POST.items():
            request.session["url_params"][k] = v
        options = request.session["url_params"]
    else:
        request.session["url_params"] = {}
        options = {}

    request.session.modified = True
    return request, options





















#AA








