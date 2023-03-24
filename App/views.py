from datetime import (
    datetime as dt, 
    timedelta
)

from django.shortcuts import render, redirect
from .config import *
from .utils import *

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
) 

from my_scripts.responses import * 
from my_scripts.database import *


def search_item(request, current_view):
    #get a list of all item ids that exist inside the database 
    item_ids = Item.objects.all().values_list("item_id",flat=True)
    
    #get item from the search bar, if it exists redirect to that items info page
    selected_item = request.POST.get("item_id")

    if selected_item in item_ids:
        return redirect(f"http://127.0.0.1:8000/item/{selected_item}")
    return redirect(f"http://127.0.0.1:8000{current_view}")

@timer
def index(request):
    if "user_id" not in request.session:
        request.session["user_id"] = -1
    user_id = request.session["user_id"]

    graph_options = get_graph_options()
    graph_metric = request.POST.get("graph-metric", "avg_price")
    graph_options = sort_dropdown_options(graph_options, graph_metric)

    #if the user has no recently viewed items create a new emtpy list to store items in the future
    if "recently-viewed" not in request.session or user_id == -1:
        request.session["recently-viewed"] = []

    recently_viewed_ids = request.session["recently-viewed"][:RECENTLY_VIEWED_ITEMS_NUM]
    recently_viewed = [DB.get_item_info(item_id, "avg_price")[0] for item_id in recently_viewed_ids]

    #duplicate list eg [1,2,3] -> [1,2,3,1,2,3] for infinite CSS carousel 
    '''recently_viewed.extend(recently_viewed)'''

    recently_viewed = format_item_info(recently_viewed, graph_data=[graph_metric], user_id=user_id)
    popular_items = format_item_info(DB.get_popular_items()[:10], popular_items=True, home_view="_popular_items", graph_data=[graph_metric])
    new_items = format_item_info(DB.get_new_items()[:10], home_view="_new_items", graph_data=[graph_metric])[:10]

    last_week = dt.today() - timedelta(days=7)
    last_week = last_week.strftime('%Y-%m-%d')

    for popular_item in popular_items:
        popular_item["change"] = DB.get_weekly_item_metric_change(popular_item["item_id"], last_week, graph_metric)[0] 

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
        context["trending"] = format_item_info(DB.get_biggest_trends(graph_metric), price_trend=[graph_metric], graph_data=[graph_metric], user_id=user_id)
    else:
        context["portfolio_trending_items"] = True
        context["trending"] = format_item_info(DB.biggest_portfolio_changes(user_id, graph_metric), graph_data=[graph_metric])


    return render(request, "App/home.html", context=context)


def item(request, item_id):

    request, options = save_POST_params(request)

    metric = options.get("graph-metric", "avg_price")

    #[0] since list with one element (being the item)
    item_info = format_item_info(
        DB.get_item_info(item_id, metric),
        graph_data=["avg_price", "min_price", "max_price", "total_quantity"]
    )
    
    if item_info == []:
        return redirect(request.META.get('HTTP_REFERER'))
    item_info = item_info[0]

    if "user_id" in request.session:
        user_id = request.session["user_id"]
    else:
        user_id = -1

    #stops view count being increased on refresh
    if "item_id" not in request.session or request.session.get("item_id") != item_id:
        request.session["item_id"] = item_id
        DB.increment_item_views(item_id)

    '''
    CHANGE IF USER IS LOGGED IN!!
    '''
    #if no recently viewed items, add item on current page to recently viewed items
    if "recently-viewed" not in request.session:
        request.session["recently-viewed"] = [item_id]
    else:
        #if item is already in recently viewed then revome it (will be added to i=0)
        if item_id in request.session["recently-viewed"]:
            request.session["recently-viewed"].remove(item_id)

        #add the item on the page to i=0
        request.session["recently-viewed"].insert(0, item_id)

        #if more than x recently-viewed items remove last / oldest item
        if len(request.session["recently-viewed"]) > RECENTLY_VIEWED_ITEMS_NUM:
            request.session["recently-viewed"].pop()

        #list is mutable, to save the changes to session
        request.session.modified = True

    graph_options = sort_dropdown_options(get_graph_options(), metric)

    in_portfolio = DB.is_item_in_user_items(user_id, "portfolio", item_id)
    #convert tuple to dict 
    in_portfolio = [{"condition":{"N":"New", "U":"Used"}[_item[0]], "count":_item[1] } for _item in in_portfolio]

    in_watchlist = DB.is_item_in_user_items(user_id, "watchlist", item_id)
    if len(in_watchlist) == 1:
        in_watchlist = "Yes"
    else:
        in_watchlist = "No"

    item_themes = Theme.objects.filter(item_id=item_id).values_list("theme_path")
    similar_items = format_item_info(get_similar_items(item_info["item_name"], item_info["item_type"], item_info["item_id"]))

    total_watchers = DB.get_total_owners_or_watchers("watchlist", item_id) 
    total_owners = DB.get_total_owners_or_watchers("portfolio", item_id)

    sub_sets = DB.get_item_subsets(item_id)
    super_sets = DB.get_item_supersets(item_id)

    metric_changes = [
        {"metric":" ".join(list(map(str.capitalize, metric_change.split("_")))) , 
        "change":DB.get_item_metric_changes(item_id, metric_change)} 
        for metric_change in ["avg_price", "min_price", "max_price", "total_quantity"]
    ]

    context = {
        "show_year_released_availability":True,
        "show_graph":False,
        "item":item_info,
        "item_id":item_info["item_id"],
        "user_id":user_id,
        "item_themes":item_themes,
        "similar_items":similar_items,
        "graph_options":graph_options,
        "in_portfolio":in_portfolio,
        "in_watchlist":in_watchlist,
        "total_watchers":total_watchers,
        "total_owners":total_owners,
        "graph_checkboxes":get_graph_checkboxes(),
        "sub_sets":format_sub_sets(sub_sets),
        "super_sets":format_super_sets(super_sets),
        "metric_changes":metric_changes,
        "most_recent_set_appearance":DB.most_recent_set_appearance(item_id)
    }

    return render(request, "App/item.html", context=context)


def trending(request):

    request, options = save_POST_params(request)

    graph_metric = options.get("graph-metric", "avg_price")
    trend_type = options.get("sort-field", "avg_price-desc")
    current_page = options.get("page", 1)

    graph_options = sort_dropdown_options(get_graph_options(), graph_metric)
    trend_options = sort_dropdown_options(get_trending_options(), trend_type)

    items = format_item_info(DB.get_biggest_trends(graph_metric), price_trend=[graph_metric], graph_data=[graph_metric])

    current_page = check_page_boundaries(current_page, len(items), SEARCH_ITEMS_PER_PAGE)
    page_numbers = slice_num_pages(len(items), current_page, SEARCH_ITEMS_PER_PAGE)

    items = sort_items(items, trend_type)
    items = items[(current_page-1) * SEARCH_ITEMS_PER_PAGE : (current_page) * SEARCH_ITEMS_PER_PAGE]

    context = {
        "items":items,
        "show_graph":True,
        "graph_options":graph_options,
        "sort_options":trend_options,
        "page_numbers":page_numbers
        }
    

    return render(request, "App/trending.html", context=context)

@timer
def search(request, theme_path='all'):

    if 'all' in request.path:
        return redirect(request.path.replace("all/", ""))

    if request.META.get('HTTP_REFERER') != None:
        if "search" not in request.META.get('HTTP_REFERER'):
            request = clear_session_url_params(request, "graph-metric", "sort-field", "page", sub_dict="url_params")

    request, options = save_POST_params(request)

    graph_metric = options.get("graph-metric", "avg_price")
    sort_field = options.get("sort-field", "avg_price-desc")
    current_page = int(options.get("page", 1))

    if "user_id" in request.session:
        user_id = request.session["user_id"]
    else:
        user_id = -1

    
    if theme_path == 'all':
        sub_themes = [{"sub_theme":theme[0], "img_path":f"App/images/{theme[1]}.png"} for theme in DB.get_sub_theme_set('', 0)]
        print(sub_themes, theme_path)
        
        theme_items = [] 
    else:
        theme_items = DB.get_theme_items(theme_path.replace("/", "~"), sort_field.split("-"))[(current_page-1) * SEARCH_ITEMS_PER_PAGE : (current_page) * SEARCH_ITEMS_PER_PAGE] #return all sets for theme
        theme_items = format_item_info(theme_items, view="search",graph_data=[graph_metric] ,user_id=user_id)

        if len(theme_items) == 0:
            redirect_path = "".join([f"{sub_theme}/" for sub_theme in theme_path.split("/")][:-1])
            #return redirect(f"http://127.0.0.1:8000/search/{redirect_path}")
       
        sub_theme_indent = request.path.replace("/search/", "").count("/")
        sub_themes = [{"sub_theme":theme[0].split("~")[sub_theme_indent], "img_path":f"App/images/{theme[1]}.png"} for theme in DB.get_sub_theme_set(theme_path.replace("/", "~"), sub_theme_indent)]

    total_theme_items = Theme.objects.filter(theme_path=theme_path.replace("/", "~"), item__item_type="M").count()

    current_page = check_page_boundaries(current_page, total_theme_items, SEARCH_ITEMS_PER_PAGE)
    page_numbers = slice_num_pages(total_theme_items, current_page, SEARCH_ITEMS_PER_PAGE)

    theme_sort_option = request.POST.get("sort-order", "theme_name-asc")
    theme_sort_options = get_search_sort_options()
    if theme_sort_option != None:
        theme_sort_options = sort_dropdown_options(theme_sort_options, theme_sort_option)

    graph_options = sort_dropdown_options(get_graph_options(), graph_metric)
    sort_options = sort_dropdown_options(get_sort_options(), sort_field)

    theme_items = sort_items(theme_items,sort_field)

    if request.method == "POST": 
        if request.POST.get("form-type") == "theme-url":
            order = theme_sort_option.split("-")[1]
            field = theme_sort_option.split("-")[0]
            sub_themes = sort_themes(field, order, sub_themes)

    context = {
        "show_graph":True,
        "current_page":current_page,
        "num_pages":page_numbers,
        "theme_path":theme_path,
        "sub_themes":sub_themes,
        "theme_items":theme_items,
        "theme_sort_options":theme_sort_options,
        "graph_options":graph_options,
        "sort_options":sort_options,
        "biggest_theme_trends":biggest_theme_trends()
    }
    
    return render(request, "App/search.html", context=context)


def login(request):
    context = {}

    if "user_id" in request.session:
        if request.session["user_id"] != -1:
            return redirect("index")
    else:
        return redirect("index")

    #if not login attempts have been made set to 0
    if "login_attempts" not in request.session:
        request.session["login_attempts"] = 0

    #check if login block has exipred
    if "login_retry_date" not in request.session:
        login_blocked = False
    else:
        #format login_retry_date into datetime format to compare with todays date
        login_retry_date = datetime.datetime.strptime(request.session["login_retry_date"].strip('"'), '%Y-%m-%d %H:%M:%S')
        if dt.today() > login_retry_date: 
            login_blocked = False
        else:
            login_blocked = True

    #analyse login form
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid() and not login_blocked:
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            #check if username and password match, create new user_id session, del login_attempts session
            if len(User.objects.filter(username=username, password=password)) == 1:
                #filter database to find user with corrisponding username and password
                user = User.objects.filter(username=username, password=password)

                #get the user_id field from user_id
                user_id = user.values_list("user_id", flat=True)[0]

                #set the user_id in session to the user that just logged in, reset login attempts
                request.session["user_id"] = user_id
                request.session["login_attempts"] = 0

                #redirect to home page id login successful
                return redirect("http://127.0.0.1:8000/")
            else:
                #display login error message, increment login_attempts 
                context.update({"login_message":"Username and Password do not match"})
                request.session["login_attempts"] += 1


    #if max login attempts exceeded, then block user for 24hrs and display message on page
    if request.session["login_attempts"] >= 4:
        if not login_blocked:
            #if the useer does not have a login time restriction, create a new one
            tommorow = dt.strptime(str(dt.now() + timedelta(1)).split(".")[0], "%Y-%m-%d %H:%M:%S")
            
            #add the new date to session in json format otherwise serializer error
            request.session["login_retry_date"] = json.dumps(tommorow, default=str)

        #if logim block date already set then display login error message, showing when the user can try to login again
        login_retry_date = request.session["login_retry_date"]
        context.update({"login_message":["YOU HAVE ATTEMPTED LOGIN TOO MANY TIMES:", f"try again on {login_retry_date}"]})

    #add the username to context which can only happen if the user is logged in
    

    return render(request, "App/login.html", context=context)


def logout(request):
    #when logging out delete user_id. 

    '''
    rework sessions for specific user, need to associate recently viewed with a user_id
    otherwise recently viewed items still show after logging out
    '''
    del request.session["user_id"]
    return redirect("login")


def join(request):

    context = {}

    if "user_id" in request.session:
        if request.session["user_id"] != -1:
            return redirect("index")
    else:
        return redirect("index")

    if request.method == 'POST':
        form = SignupFrom(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            password_confirmation = form.cleaned_data["password_confirmation"]
            
            #check if passwords match other wise need to display message showing it
            if password == password_confirmation:

                #check if the username / email already exists inside the database, cannot be duplicates
                if len(User.objects.filter(Q(username=username) | Q(email=email))) == 0:
                    #if the username or email does not already exist, add the new users details to database
                    new_user = User(
                        username=username,email=email,password=password,
                        email_preference="All", region="None", date_joined=datetime.date.today().strftime('%Y-%m-%d')
                    )
                    new_user.save()

                    #get the new users id to add to session
                    user = User.objects.filter(username=username, password=password)
                    user_id = user.values_list("user_id", flat=True)[0]
                    request.session["user_id"] = user_id
                    request.session.modified = True
                    return redirect("http://127.0.0.1:8000/")

                #set error messages depending on what the user did wrong in filling out the form
                context["signup_message"] = "Username / Email already exists"
            context["signup_message"] = "Passwords do not Match"

    #add the username to context which can only happen if the user is logged in
    return render(request, "App/join.html", context=context)


def user_items(request, view, user_id):

    if view not in request.META.get('HTTP_REFERER', ""):
        request = clear_session_url_params(request, "graph-metric", "sort-field", "page", sub_dict="url_params")

    graph_options = get_graph_options()
    sort_options = get_sort_options()

    if "url_params" in request.session:
        options = request.session["url_params"]
    else:
        options = {}

    graph_metric = options.get("graph-metric", "avg_price")
    current_page = int(options.get("page", 1))
    sort_field = options.get("sort-field", "avg_price-desc")

    items = DB.get_user_items(user_id, view)
    items = format_item_info(items, view=view, graph_data=[graph_metric], user_id=user_id)

    current_page = check_page_boundaries(current_page, len(items), USER_ITEMS_ITEMS_PER_PAGE)
    num_pages = slice_num_pages(len(items), current_page, USER_ITEMS_ITEMS_PER_PAGE)

    items = sort_items(items, sort_field)
    #keep selected sort field option as first <option> tag
    sort_options = sort_dropdown_options(sort_options, sort_field)

    graph_options = sort_dropdown_options(graph_options, graph_metric)

    total_unique_items = len(items)
    metric_total = {
        "metric":' '.join(list(map(str.capitalize, graph_metric.split("_")))),
        "total":DB.user_items_total_price(user_id, graph_metric, view) 
        }

    items = items[(current_page - 1) * USER_ITEMS_ITEMS_PER_PAGE : int(current_page) * USER_ITEMS_ITEMS_PER_PAGE]

    parent_themes = DB.parent_themes(user_id, view, graph_metric)
    themes = get_sub_themes(user_id, parent_themes, [], -1, view, graph_metric)

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
    }

    return context


def portfolio(request, item_id=None):

    if "user_id" not in request.session or request.session["user_id"] == -1:
        return redirect("index")
    user_id = request.session["user_id"]

    item_id = request.GET.get("item")
    
    context = user_items(request, "portfolio", user_id)

    context["total_items"] = Portfolio.objects.filter(user_id=user_id).count()
    context["total_bought_price"] = Portfolio.objects.filter(user_id=user_id).aggregate(total_bought_for=Sum("bought_for"))["total_bought_for"]
    context["total_sold_price"] = Portfolio.objects.filter(user_id=user_id).aggregate(total_sold_for=Sum("sold_for"))["total_sold_for"] 
    context["total_profit"] = round(Portfolio.objects.filter(user_id=user_id).aggregate(profit=Sum("bought_for") - Sum("sold_for"))["profit"], 2)


    item_id = request.GET.get("item")
    if item_id != None:

        if "graph_metric" in request.session:
            context["graph_metric"] = request.session["graph_metric"]
            context["graph_options"] = request.session["graph_options"]
            del request.session["graph_metric"] ; del request.session["graph_options"]
      
        items = Portfolio.objects.filter(item_id=item_id, user_id=user_id).values_list("condition", "bought_for", "sold_for", "date_added", "date_sold", "notes", "portfolio_id")
        items = format_portfolio_items(items)
        context["item_entries"] = items
        context["metric_changes"] = [{"metric":metric,"change":DB.get_item_metric_changes(item_id, metric)} for metric in ALL_METRICS]
        context["item"] = format_item_info(DB.get_item_info(item_id, context["graph_metric"]), graph_data=[context["graph_metric"]], price_trend=ALL_METRICS)[0]
        
        context["total_profit"] = round(Portfolio.objects.filter(user_id=user_id, item_id=item_id).aggregate(profit=Sum("bought_for") - Sum("sold_for"))["profit"], 2)
        context["total_owners"] = len(Portfolio.objects.filter(item_id=item_id).aggregate(Count("user_id")))
        context["total_watchers"] = Watchlist.objects.filter(item_id=item_id).count()
        
        context["total_market_value"] = Price.objects.filter(
            item_id=item_id, date=Price.objects.filter(item_id=item_id).aggregate(Max("date"))["date__max"]
        ).values_list("avg_price", flat=True)[0] * Portfolio.objects.filter(item_id=item_id, user_id=user_id, date_sold=None).count()

        if len(Portfolio.objects.filter(item_id=item_id, user_id=user_id)) > 0:
            context["total_bought_price"] = Portfolio.objects.filter(item_id=item_id, user_id=user_id).aggregate(total_bought_for=Sum("bought_for"))["total_bought_for"]
            context["total_sold_price"] = Portfolio.objects.filter(item_id=item_id, user_id=user_id).aggregate(total_sold_for=Sum("sold_for"))["total_sold_for"] 

    return render(request, "App/portfolio.html", context=context)


def view_POST(request, view):

    if "?item=" in request.META.get('HTTP_REFERER'):
        request.session["graph_metric"] = request.POST.get("graph-metric", "avg_price")
        request.session["graph_options"] = sort_dropdown_options(get_graph_options(), request.POST.get("graph-metric", "avg_price"))
        return redirect(request.META.get('HTTP_REFERER'))

    if "user_id" not in request.session or request.session["user_id"] == -1:
        return redirect("index")
    user_id = request.session["user_id"]

    items = DB.get_user_items(user_id, view=view)

    portfolio_items = format_item_info(items, view=view)

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
        return redirect(f"http://127.0.0.1:8000/{view}/?item={item_id}")

    return redirect(view)


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
            
    return redirect(f"http://127.0.0.1:8000/item/{item_id}")



def entry_item_handler(request, view):
    item_id = request.POST.get("item_id")
    entry_id = request.POST.get("entry_id")

    if request.POST.get("remove-entry") != None:
        Portfolio.objects.filter(portfolio_id=entry_id).delete()
        if view == "portfolio":
            return redirect(f"http://127.0.0.1:8000/{view}/?item={item_id}")
        return redirect(f"http://127.0.0.1:8000/{view}/{item_id}/")
    

    elif "CLEAR" in request.POST.get("clear-input", ""):
        nulled_field = request.POST.get("clear-input").split("_CLEAR")[0]

        new_data = {nulled_field:None}
        if "_for" in nulled_field:
            new_data = {nulled_field:0}

        Portfolio.objects.filter(portfolio_id=entry_id).update(**new_data)
        if view == "portfolio":
            return redirect(f"http://127.0.0.1:8000/{view}/?item={item_id}")
        return redirect(f"http://127.0.0.1:8000/{view}/{item_id}/")
    

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
        return redirect(f"http://127.0.0.1:8000/{view}/?item={item_id}")
    
    elif request.POST.get("form-type") == "new-entry":
        values = {k:v for k,v in request.POST.items() if k not in ["csrfmiddlewaretoken", "form-type"] and v != ''}
        Portfolio(**values).save()
        if view == "portfolio":
            return redirect(f"http://127.0.0.1:8000/{view}/?item={item_id}")
        return redirect(f"http://127.0.0.1:8000/{view}/{item_id}/")

def profile(request):

    if "user_id" not in request.session or request.session["user_id"] == -1:
        return redirect("index")
    user_id = request.session["user_id"]

    context = {
        "username":User.objects.filter(user_id=user_id).values_list("username", flat=True)[0],
        "name":"NO NAME FIELD IN DATABASE",
        "email":User.objects.filter(user_id=user_id).values_list("email", flat=True)[0],
    }

    #SETTINGS    
    if request.method == "POST":
        #-Change password
        if request.POST.get("form-type") == "change-password-form":
            form = ChangePassword(request.POST)
            if form.is_valid():
                old_password = form.cleaned_data["old_password"]
                new_password = form.cleaned_data["new_password"]
                confirm_password = form.cleaned_data["confirm_password"]
        
                #list of rules that must all return True for the password to be updated, with corrisponding error messages
                #to be displayed to the user.
                rules:list[dict] = [ 
                    {len(User.objects.filter(user_id=user_id, password=old_password)) > 0:"'Old password' is incorrect"},
                    {new_password == confirm_password:"'New password' and 'Confirm password' do not match"},
                ]

                #add all dict keys to list, use all() method on list[bool] to see if all password change conditions are met
                if all([all(rule) for rule in rules]):
                    User.objects.filter(password=old_password, user_id=user_id).update(password=new_password)
                else:
                    #pass an error message to context, based on what condition was not satisfied
                    context["change_password_error_message"] = get_change_password_error_message(rules)

        #-Email preferences
        elif request.POST.get("form-type") == "email-preference-form":
            form = EmailPreferences(request.POST)
            if form.is_valid():
                email = form.cleaned_data["email"]
                preference = form.cleaned_data["preference"][0]
                User.objects.filter(user_id=user_id, email=email).update(email_preference=preference)

        #-Change personal info
        elif request.POST.get("form-type") == "personal-details-form":
            form = PersonalInfo(request.POST)
            if form.is_valid():
                username = form.cleaned_data["username"]

                #update username is database
                User.objects.filter(user_id=user_id).update(username=username)

    #USER INFO

    #MEMBERSHIP 

    return render(request, "App/profile.html", context=context)