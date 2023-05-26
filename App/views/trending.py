from django.http import QueryDict
from django.shortcuts import render
from project_utils.filters import ClearFilter, FilterOut, ProcessFilter
from project_utils.general import General
from project_utils.item_format import Formatter
from scripts.database import DB

from App.models import Price, Theme
from config.config import (
    ALL_METRICS, METRIC_INPUT_STEPS,
    TRENDING_ITEMS_PER_PAGE, get_graph_options,
    get_trending_options
)

GENERAL = General()
CLEAR_FILTER = ClearFilter()
FILTER_OUT = FilterOut()
FORMATTER = Formatter()
PROCESS_FILTER = ProcessFilter()


def trending(request):

    get_params = ['sort-field', 'page', 'slider_start_value', 'slider_end_value']

    request = GENERAL.process_sorts_and_pages(request, get_params)
    request = PROCESS_FILTER.save_filters(request)

    previous_url = GENERAL.get_previous_url(request)
    current_url = request.path

    if request.POST.get('clear-form') != None or current_url != previous_url: 
        request = CLEAR_FILTER.clear_filters(request)

    # query_string = '&'.join([
    #     f'{param}={request.session.get(param)}'
    #     for param in get_params if request.session.get(param) != None
    # ])

    trending_order: str = request.session.get('sort-field', 'avg_price-desc')
    trending_metric = trending_order.split('-')[0]
    current_page = request.session.get('page', 1)

    current_page = GENERAL.check_if_page_not_int(current_page)

    graph_options = GENERAL.sort_dropdown_options(
        get_graph_options(), trending_metric
    )
    trend_options = GENERAL.sort_dropdown_options(
        get_trending_options(), trending_order
    )

    dates = list(Price.objects.distinct('date').values_list('date', flat=True))
    dates = [date.strftime('%Y-%m-%d') for date in dates]

    slider_start_value = int(request.session.get(
        'slider_start_value', 0)
    )
    slider_end_value = int(request.session.get(
        'slider_end_value', len(dates)-1)
    )

    slider_start_value = GENERAL.check_slider_range(slider_start_value, dates)
    slider_end_value = GENERAL.check_slider_range(slider_end_value, dates)

    min_date = dates[slider_start_value]
    max_date = dates[slider_end_value]

    items = DB.get_biggest_trends(
        trending_metric, max_date=max_date, min_date=min_date
    )
    # remove trending items if % change (-1) is equal to None (0.00)
    items = [_item for _item in items if _item[-1] != None]

    themes = list(
        Theme.objects.filter(theme_path__startswith='Star_Wars').values_list(
        'theme_path', flat=True).distinct('theme_path')
    )

    filter_results = FILTER_OUT.process_filters(request, items, themes)
    items = filter_results['return']['items']
    request = filter_results['return']['request']

    current_page = GENERAL.check_page_boundaries(
        current_page, len(items), TRENDING_ITEMS_PER_PAGE
    )
    num_pages = GENERAL.slice_num_pages(
        len(items), current_page, TRENDING_ITEMS_PER_PAGE
    )

    items = items[
        (current_page-1) *TRENDING_ITEMS_PER_PAGE: (current_page) * TRENDING_ITEMS_PER_PAGE
    ]
    items = FORMATTER.format_item_info(
        items, metric_trends=[trending_metric], graph_data=[trending_metric]
    )

    #add metric changes to items
    for _item in items:
        metrics = [
            DB.get_item_metric_changes(
                _item['item_id'], metric, max_date=max_date, min_date=min_date
            ) for metric in ALL_METRICS
        ]
        metrics = FORMATTER.format_metric_changes(metrics)
        _item['metric_changes'] = metrics

    context = {
        'items': items,
        'show_graph': True,
        'graph_options': graph_options,
        'sort_options': trend_options,
        'num_pages': num_pages,
        'current_page': current_page,
        'dates': dates,
        'metric_data': trending_metric,
        'slider_start_value': slider_start_value,
        'slider_end_value': slider_end_value,
        'slider_start_max_value': slider_end_value - 1,
        'slider_end_max_value': len(dates) - 1,
        'slider_start_min_value': 0,
        'slider_end_min_value': slider_start_value + 1,
        'all_metrics': ALL_METRICS,
        'metric_input_steps': METRIC_INPUT_STEPS,
        'filter_themes': themes,
        'themes': request.session['themes'],
        'winners_or_losers_filter': request.session.get('winners_or_losers_filter'),
    }

    context.update(filter_results['context'])
    return render(request, 'App/trending.html', context=context)
