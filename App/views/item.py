import itertools

from django.db.models import F
from django.shortcuts import redirect, render
from project_utils.general import General
from project_utils.item_format import Formatter
from scripts.database import DatabaseManagement
from .user_items import entry_item_handler, add_to_user_items

from App.models import Item, Theme
from config.config import (
    ALL_METRICS, COLOURS, EXTRA_WORDS,
    MAX_SIMILAR_ITEMS, RECENTLY_VIEWED_ITEMS_NUM,
    REMOVE_CHARS, ITEM_CONDITION_CONVERT, get_graph_checkboxes,
    get_graph_options
)

FORMATTER = Formatter()
GENERAL = General()
DB = DatabaseManagement()


def item(request, item_id):

    if request.POST.get('form-type') in ['entry-edit', 'new-entry']:
        request = entry_item_handler(request)

    request = process_recently_viewed_items(request, item_id)
    request = add_to_user_items(request, item_id, 'portfolio')
    request = add_to_user_items(request, item_id, 'watchlist')

    user_id = request.session.get('user_id', -1)
    metric = request.session.get('graph-metric', 'avg_price')

    item_info = FORMATTER.format_item_info(
        DB.get_item_info(item_id, metric), graph_data=ALL_METRICS, view='item'
    )
    item_info = convert_last_and_first_date(item_info)

    # if no info for item, return to previous page
    if item_info == []:
        return redirect(request.META.get('HTTP_REFERER'))
    item_info = item_info[0]

    # stops view count being increased on refresh
    if request.session.get('item_id') != item_id:
        request.session['item_id'] = item_id
        Item.objects.filter(item_id=item_id).update(views=F('views')+1)

    context = {
        'show_year_released_availability': True,
        'show_graph': False,
        'item': item_info,
        'item_id': item_info['item_id'],
        'user_id': user_id,
        'item_themes': (Theme.objects.filter(item_id=item_id
            ).distinct('theme_path'
            ).values_list('theme_path')
        ),
        'graph_options': GENERAL.sort_dropdown_options(
            get_graph_options(), metric
        ),
        'in_watchlist': DB.is_item_in_user_items(
            user_id, 'watchlist', item_id
        ),
        'total_watchers': DB.get_total_owners_or_watchers(
            'watchlist', item_id
        ),
        'total_owners': DB.get_total_owners_or_watchers(
            'portfolio', item_id
        ),
        'graph_checkboxes': get_graph_checkboxes(),
        'sub_sets': DB.get_item_subsets(item_id),

        'metric_changes': FORMATTER.format_metric_changes(
            [
                DB.get_item_metric_changes(item_id, metric) for metric in ALL_METRICS
             ]
        ),
        'in_portfolio': [
            {'condition': ITEM_CONDITION_CONVERT[_item[0]], 'count':_item[1]}
            for _item in DB.is_item_in_user_items(user_id, 'portfolio', item_id)
        ],
        'similar_items': FORMATTER.format_item_info(
            get_similar_items(
                item_info['item_name'], item_info['item_type'], item_info['item_id']
            )
        ),
    }

    print('errr', context['in_watchlist'])

    # items to add to context based on item type
    if item_info['item_type'] == 'M':
        context['super_sets'] = FORMATTER.format_super_sets(
            DB.get_item_supersets(item_id)
        )
        context['most_recent_set_appearance'] = DB.most_recent_item_appearance(
            item_id
        )
    else:
        context['figures'] = FORMATTER.format_item_info(
            DB.get_set_items(item_id), quantity=8
        )

    return render(request, 'App/item.html', context=context)


def convert_last_and_first_date(item_info):
    if item_info != []:
        # convert first and last item into new format so on window load slider max value is not Day, Month, Year format
        if len(item_info[0]['dates']) >= 2:
            item_info[0]['dates'][-1] = item_info[0]['dates'][-1].strftime(
                '%Y-%m-%d'
            )
            item_info[0]['dates'][0] = item_info[0]['dates'][0].strftime(
                '%Y-%m-%d'
            )
        else:
            item_info[0]['dates'][0] = item_info[0]['dates'][0].strftime(
                '%Y-%m-%d'
            )
    return item_info


def process_recently_viewed_items(request, item_id):
    if 'recently-viewed' not in request.session:
        request.session['recently-viewed'] = [item_id]
    else:
        if item_id in request.session['recently-viewed']:
            request.session['recently-viewed'].remove(item_id)

        request.session['recently-viewed'].insert(0, item_id)

        if len(request.session['recently-viewed']) > RECENTLY_VIEWED_ITEMS_NUM:
            request.session['recently-viewed'].pop()

        request.session.modified = True
    return request


def shorten_len_return_value(_list: list) -> int:
    # shorten combinations if too many words to parse through
    length_convert = {
        len(_list) < 5: 1,
        len(_list) >= 5 and len(_list) < 9: 2,
        len(_list) >= 9: 3
    }
    return length_convert[True]


def similar_items_iterate(
        single_words: list[str], item_name: str, 
        item_type: str, item_id: str, items: list[str], combinations: int
    ) -> tuple[int, list]:

    for sub in itertools.combinations(single_words, combinations):
        sql_like = 'AND ' + 'AND '.join(
            [f"item_name LIKE '%{word}%' " for word in sub]
        )

        new_items = DB.get_similar_items(
            item_name, item_type, item_id, sql_like
        )

        for item in new_items:
            if len(items) < MAX_SIMILAR_ITEMS and item not in items:
                items.append(item)
                if len(items) >= MAX_SIMILAR_ITEMS:
                    return combinations, list(dict.fromkeys(items))

        if len(sub) <= 3 and len(items) >= 3:
            return combinations, items

    return combinations, []


def get_similar_items(item_name: str, item_type: str, item_id: str) -> list:

    item_type = DB.get_item_type(item_id)

    remove_words = list(DB.get_most_common_words(
        'item_name', item_type, ',', '(', ')', min_word_length=2, limit=25
    ))
    remove_words.extend(COLOURS)
    remove_words.extend(EXTRA_WORDS)
    remove_words.extend(list(map(str.capitalize, remove_words)))

    single_words = [
        word.translate(''.join(REMOVE_CHARS)) for word in item_name.split(' ')
        if len(word) > 3 and word.translate(''.join(REMOVE_CHARS)) not in remove_words
    ]

    items = []

    combinations = len(single_words)
    combinations = combinations // shorten_len_return_value(single_words)

    # set limit for substring combinations, increase combinations,
    # increase run time exponentially
    if combinations > 3:
        combinations = 3

    while True:
        combinations, items = similar_items_iterate(
            single_words, item_name, item_type, item_id, items, combinations)

        if len(items) >= MAX_SIMILAR_ITEMS or combinations <= 1:
            break

        combinations -= 1
    return items[:MAX_SIMILAR_ITEMS]
