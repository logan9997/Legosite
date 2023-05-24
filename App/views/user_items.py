from datetime import datetime as dt

from django.db.models import Count, Max, Sum
from django.shortcuts import redirect, render
from project_utils.filters import ClearFilter, FilterOut, ProcessFilter
from project_utils.general import General
from project_utils.item_format import Formatter
from scripts.database import DB

from App.models import Portfolio, Price, Watchlist
from config.config import (
    ALL_METRICS, METRIC_INPUT_STEPS,
    USER_ITEMS_ITEMS_PER_PAGE, get_graph_options,
    get_sort_options
)

GENERAL = General()
FORMATTER = Formatter()
FILTER_OUT = FilterOut()
PROCESS_FILTER = ProcessFilter()
CLEAR_FILTER = ClearFilter()


def user_items(request, view, user_id):

    get_params = ['sort-field', 'page', 'graph-metric']

    request = GENERAL.process_sorts_and_pages(request, get_params)
    request = PROCESS_FILTER.save_filters(request)

    previous_url = GENERAL.get_previous_url(request)
    current_url = request.path

    if request.POST.get('clear-form') != None or current_url != previous_url:
        print('clearing filters, user items')
        request = CLEAR_FILTER.clear_filters(request)

    graph_options = get_graph_options()
    sort_options = get_sort_options()

    if request.POST.get('form-type') == 'remove-watchlist-item':
        item_id = request.POST.get('item_id')
        Watchlist.objects.filter(user_id=user_id, item_id=item_id).delete()

    graph_metric = request.session.get('graph-metric', 'avg_price')
    current_page = request.session.get('page', 1)
    sort_field = request.session.get('sort-field', 'avg_price-desc')

    current_page = GENERAL.check_if_page_not_int(current_page)

    items = DB.get_user_items(user_id, view)
    items = FORMATTER.format_item_info(
        items, owned_quantity_new=8, owned_quantity_used=9, 
        graph_data=[graph_metric], user_id=user_id
    )

    parent_themes = DB.parent_themes(user_id, view, graph_metric)
    themes = get_sub_themes(
        user_id, parent_themes, [], -1, view, graph_metric
    )

    filter_themes = [theme['theme_path'] for theme in themes]
    filter_results = FILTER_OUT.process_filters(
        request, items, filter_themes
    )
    items = filter_results['return']['items']
    request = filter_results['return']['request']

    current_page = GENERAL.check_page_boundaries(
        current_page, len(items), USER_ITEMS_ITEMS_PER_PAGE
    )
    num_pages = GENERAL.slice_num_pages(
        len(items), current_page, USER_ITEMS_ITEMS_PER_PAGE
    )

    # keep selected sort field option as first <option> tag
    sort_options = GENERAL.sort_dropdown_options(sort_options, sort_field)
    graph_options = GENERAL.sort_dropdown_options(graph_options, graph_metric)
    items = GENERAL.sort_items(items, sort_field)

    total_unique_items = len(items)
    metric_total = {
        'metric': GENERAL.split_capitalize(graph_metric, '_'),
        'total': DB.user_items_total_price(user_id, graph_metric, view)
    }

    years_released = []

    #create a list of all unique years released from items
    [
        years_released.append(_item['year_released'])
        for _item in items if _item['year_released'] not in years_released
    ]

    items = items[
        (current_page - 1) * USER_ITEMS_ITEMS_PER_PAGE: int(current_page) * USER_ITEMS_ITEMS_PER_PAGE
    ]

    print(request.session['themes'])

    context = {
        'items': items,
        'num_pages': num_pages,
        'sort_options': sort_options,
        'graph_options': graph_options,
        'filter_themes': filter_themes,
        'themes': themes,
        'total_unique_items': total_unique_items,
        'metric_total': metric_total,
        'view': view,
        'graph_metric': graph_metric,
        'current_page': current_page,
        'show_graph': True,
        'user_id': user_id,
        'all_metrics': ALL_METRICS,
        'metric_input_steps': METRIC_INPUT_STEPS,
        'years_released': years_released,
    }

    context.update(filter_results['context'])

    return context


def portfolio(request):

    if 'user_id' not in request.session or request.session['user_id'] == -1:
        return redirect('index')
    user_id = request.session.get('user_id', -1)

    context = user_items(request, 'portfolio', user_id)

    context['total_items'] = Portfolio.objects.filter(user_id=user_id).count()

    context['total_bought_price'] = Portfolio.objects.filter(user_id=user_id
        ).aggregate(total_bought_for=Sum('bought_for', default=0)
    )['total_bought_for']

    context['total_sold_price'] = Portfolio.objects.filter(user_id=user_id
        ).aggregate(total_sold_for=Sum('sold_for', default=0)
    )['total_sold_for']

    context['total_profit'] = round(Portfolio.objects.filter(user_id=user_id).aggregate(
        profit=Sum('bought_for', default=0) - Sum('sold_for', default=0))['profit'] ,2
    )

    return render(request, 'App/portfolio.html', context=context)


def portfolio_item(request, item_id: str):

    user_id = request.session.get('user_id', -1)

    get_params = ['graph-metric']
    GENERAL.save_get_params(request, get_params)

    current_url = request.path
    previous_url = GENERAL.get_previous_url(request)

    if current_url != previous_url:
        GENERAL.clear_get_params(request, get_params)

    graph_metric = request.session.get('graph-metric', 'avg_price')

    item_info = FORMATTER.format_item_info(
        DB.get_item_info(item_id, graph_metric), 
        graph_data=[graph_metric], metric_trends=ALL_METRICS
    )[0]

    context = {
        'item_id': item_id,
        'item_info': item_info,
        'item': item_info,
        'view': 'portfolio',
        'graph_options': GENERAL.sort_dropdown_options(get_graph_options(), graph_metric),
        'graph_metric': graph_metric
    }

    if len(Portfolio.objects.filter(user_id=user_id, item_id=item_id)) == 0:
        return redirect('portfolio')

    if 'graph_metric' in request.session:
        context['graph_metric'] = request.session['graph_metric']
        del request.session['graph_metric']

    if 'graph_options' in request.session:
        context['graph_options'] = request.session['graph_options']
        del request.session['graph_options']

    item_entries = Portfolio.objects.filter(item_id=item_id, user_id=user_id).values_list(
        'condition', 'bought_for', 'sold_for', 
        'date_added', 'date_sold', 'notes', 'portfolio_id'
    )
    context['item_entries'] = FORMATTER.format_portfolio_items(item_entries)

    context['metric_changes'] = [
        {'metric': metric, 'change': DB.get_item_metric_changes(item_id, metric)}
        for metric in ALL_METRICS
    ]
    context['item'] = FORMATTER.format_item_info(
        DB.get_item_info(item_id, graph_metric), 
        graph_data=[graph_metric], metric_trends=ALL_METRICS
    )[0]

    context['total_profit'] = round(
        Portfolio.objects.filter(user_id=user_id, item_id=item_id).aggregate(
        profit=Sum('sold_for', default=0) - Sum('bought_for', default=0))['profit']
    ,2)

    context['total_owners'] = len(Portfolio.objects.filter(
        item_id=item_id).aggregate(Count('user_id'))
    )
    context['total_watchers'] = Watchlist.objects.filter(item_id=item_id).count()

    item_current_price = Price.objects.filter(
        item_id=item_id, date=Price.objects.filter(
        item_id=item_id).aggregate(Max('date'))['date__max']
    ).values_list('avg_price', flat=True)[0]

    item_count = (
        Portfolio.objects.filter(
        item_id=item_id, user_id=user_id, date_sold=None
        ).count()
    )

    context['total_market_value'] = round(item_current_price * item_count, 3)

    if len(Portfolio.objects.filter(item_id=item_id, user_id=user_id)) > 0:
        context['total_bought_price'] = Portfolio.objects.filter(item_id=item_id, user_id=user_id).aggregate(
            total_bought_for=Sum('bought_for', default=0)
        )['total_bought_for']

        context['total_sold_price'] = Portfolio.objects.filter(item_id=item_id, user_id=user_id).aggregate(
            total_sold_for=Sum('sold_for', default=0)
        )['total_sold_for']

    return render(request, 'App/portfolio_item.html', context=context)


def watchlist(request):

    if 'user_id' not in request.session or request.session['user_id'] == -1:
        return redirect('index')
    user_id = request.session.get('user_id')

    context = user_items(request, 'watchlist', user_id)

    return render(request, 'App/watchlist.html', context=context)


def get_sub_themes(
        user_id: int, parent_themes: list[str], themes: list[dict], 
        indent: int, view: str, metric: str
    ) -> list[str]:

    indent += 1
    for theme in parent_themes:
        sub_themes = DB.sub_themes(
            user_id, theme[0], view, metric, metric_total=True, count=True
        )
        
        sub_themes = [
            theme_path for theme_path in sub_themes 
            if theme_path.count('~') == indent
        ]
        themes.append({
            'theme_path': theme[0],
            'count': theme[1],
            'metric_total': theme[2],
            'sub_themes': sub_themes,
        })

        get_sub_themes(user_id, sub_themes, themes, indent, view, metric)

    return themes
