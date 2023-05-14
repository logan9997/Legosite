import math
import time
import itertools

from datetime import datetime as dt

from ..config import *









#AA







#AA






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








