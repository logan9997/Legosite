from scripts.database import DatabaseManagement

from config.config import ALL_METRICS

from .general import General

DB = DatabaseManagement()
GENERAL = General()


class FilterOut():

    def process_filters(self, request, items: list, themes: list):

        request.session['themes'] = themes

        filters = [
            self.filter_out_theme_filters,
            self.filter_out_item_type_filters,
            self.filter_out_metric_filters,
            self.filter_out_winners_losers_filters
        ]

        for filter in filters:
            if len(items) != 0:
                request, items = filter(request, items)

        context = {
            'filtered_themes': request.session.get('filtered_themes'),
            'metric_filters': {
                f'{param}_{limit}': request.session['metric_filters'].get(f'{param}_{limit}')
                for param in ALL_METRICS for limit in ['min', 'max']
            },
            'item_type_filter': request.session.get('item_type_filter'),
        }

        return_values = {
            'request': request,
            'items': items
        }

        return {'context': context, 'return': return_values}

    def filter_out_theme_filters(self, request, items):

        filtered_themes = request.session.get('filtered_themes', [])
        if filtered_themes != []:
            if type(items[0]) == dict:
                item_id_key = 'item_id'
            else:
                item_id_key = 0

            items_to_filter_by_theme = DB.filter_items_by_theme(
                filtered_themes
                )
            items = list(
                filter(lambda x: x[item_id_key] in items_to_filter_by_theme, items)
            )
        return request, items

    def filter_out_item_type_filters(self, request, items: list):
        item_type_filter = request.session.get('item_type_filter')

        if type(items[0]) == dict:
            item_type_key = 'item_type'
        else:
            item_type_key = 3

        if item_type_filter not in ['All', None]:
            items = list(
                filter(lambda x: x[item_type_key] == item_type_filter, items))

        return request, items

    def filter_out_winners_losers_filters(self, request, items):

        winners_or_losers = request.session.get(
            'winners_or_losers_filter', 'All'
        )
        metric = request.session.get(
            'trending_order', 'avg_price-desc'
        ).split('-')[0]
        metric = GENERAL.split_capitalize(metric, '_')

        if type(items[0]) == dict:
            pass

        if winners_or_losers == 'Winners':
            items = list(filter(lambda x: x[-1] > 0, items))
        elif winners_or_losers == 'Losers':
            items = list(filter(lambda x: x[-1] < 0, items))
        return request, items

    def filter_out_metric_filters(self, request, items) -> list:
        metric_filters = request.session.get(
            'metric_filters', ProcessFilter().default_metric_filters()
        )

        if type(items[0]) == dict:
            keys = {
                'avg_price': 'avg_price',
                'min_price': 'min_price',
                'max_price': 'max_price',
                'total_quantity': 'total_quantity',
            }
        else:
            keys = {
                'avg_price': 4,
                'min_price': 5,
                'max_price': 6,
                'total_quantity': 7,
            }

        for metric in metric_filters:
            keys_lookup = metric.rsplit('_', 1)[0]

            if 'min' in metric and metric_filters[metric] != -1:
                items = list(
                    filter(lambda x: x[keys[keys_lookup]] > metric_filters[metric], items))
            elif 'max' in metric and metric_filters[metric] != -1:
                items = list(
                    filter(lambda x: x[keys[keys_lookup]] < metric_filters[metric], items))

        return request, items


class ProcessFilter():

    def process_theme_filters(self, request):
        if 'filtered_themes' not in request.session:
            request.session['filtered_themes'] = []

        themes = request.session.get('themes', [])
        selected_theme = request.GET.get('theme-filter')

        for sub_theme in themes[themes.index(selected_theme)+1:]:
            if selected_theme in request.session['filtered_themes']:
                if selected_theme.count('~') < sub_theme.count('~'):
                    if sub_theme in request.session['filtered_themes']:
                        request.session['filtered_themes'].remove(sub_theme)
                else:
                    break
            else:
                if selected_theme.count('~') < sub_theme.count('~'):
                    if sub_theme not in request.session['filtered_themes']:
                        request.session['filtered_themes'].append(sub_theme)
                else:
                    break

        if selected_theme not in request.session['filtered_themes']:
            request.session['filtered_themes'].append(selected_theme)
        else:
            request.session['filtered_themes'].remove(selected_theme)
        request.session.modified = True
        return request

    def process_metric_filters(self, request):
        if 'metric_filters' not in request.session:
            request.session['metric_filters'] = self.default_metric_filters()

        for metric in ALL_METRICS:
            for limit in ['min', 'max']:
                if (
                    request.GET.get(f'{metric}_{limit}') != None and 
                    request.GET.get(f'{metric}_{limit}') != ''
                ):
                    try:
                        _input = float(request.GET.get(f'{metric}_{limit}'))
                    except:
                        _input = 0
                    request.session['metric_filters'][f'{metric}_{limit}'] = _input
                    request.session.modified = True
        return request

    def save_filters(self, request):
        if request.GET.get('form-type') == 'metric_filters':
            request = ProcessFilter().process_metric_filters(request)

        elif request.GET.get('form-type') == 'theme-filter':
            request = ProcessFilter().process_theme_filters(request)

        elif request.GET.get('form-type') == 'item_type_filter':
            request.session['item_type_filter'] = request.GET.get(
                'item_type_filter')

        elif request.GET.get('form-type') == 'winners_or_losers_filter':
            request.session['winners_or_losers_filter'] = request.GET.get(
                'winners_or_losers_filter')

        return request

    def default_metric_filters(self):
        return {
            f'{metric}_{limit}': -1 for metric in ALL_METRICS for limit in ['min', 'max']
        }


class ClearFilter():

    def clear_filters(self, request):
        request.session['metric_filters'] = ProcessFilter(
        ).default_metric_filters()
        request.session['filtered_themes'] = []
        request.session.modified = True
        return request
