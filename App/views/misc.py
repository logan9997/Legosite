from django.shortcuts import redirect
from django.db.models import Count
from datetime import datetime as dt
from project_utils.filters import ProcessFilter
from project_utils.general import General
from scripts.database import DB

from App.models import Item, Watchlist, Portfolio
from App.forms import ItemSelect

GENERAL = General()
PROCESS_FILTER = ProcessFilter()


def search_item(request, current_view):
    # get a list of all item ids that exist inside the database
    item_ids = Item.objects.all().values_list('item_id', flat=True)

    # get item from the search bar, if it exists redirect to that items info page
    selected_item = ''
    if request.method == 'POST':
        form = ItemSelect(request.POST)
        if form.is_valid():
            selected_item = form.cleaned_data['item_id_or_name']

    if selected_item in item_ids:
        return redirect(f'http://{GENERAL.get_base_url(request)}/item/{selected_item}')
    return redirect(f'{current_view}')


def update_filters_in_session(request, view):

    if request.POST.get('clear-form') == 'clear-metric-filters':
        request = PROCESS_FILTER.set_default_metric_filters(request)

    elif request.POST.get('clear-form') == 'clear-theme-filters':
        request.session['filtered_themes'] = []

    if view == 'search':
        return redirect(request.META.get('HTTP_REFERER'))

    return redirect(view)


def logout(request):
    del request.session['user_id']
    return redirect('login')


def entry_item_handler(request, redirect_view):
    entry_id = request.POST.get('entry_id')
    user_id = request.session.get('user_id', -1)

    if request.POST.get('remove-entry') != None:
        Portfolio.objects.filter(portfolio_id=entry_id).delete()

    elif 'CLEAR' in request.POST.get('clear-input', ''):
        nulled_field = request.POST.get('clear-input').split('_CLEAR')[0]

        # for price inputs
        new_data = {nulled_field: None}
        if '_for' in nulled_field:
            new_data = {nulled_field: 0}

        Portfolio.objects.filter(portfolio_id=entry_id).update(**new_data)

    elif request.POST.get('form-type') == 'entry-edit':
        fields = {
            'date_added': str(request.POST.get('date_added')),
            'bought_for': float(request.POST.get('bought_for')),
            'date_sold': str(request.POST.get('date_sold')),
            'sold_for': float(request.POST.get('sold_for')),
            'notes': str(request.POST.get('notes')),
        }

        # set fields in database to null rather than empty string
        for k, v in fields.items():
            if v == '':
                fields[k] = None

        Portfolio.objects.filter(portfolio_id=entry_id).update(**fields)

    elif request.POST.get('form-type') == 'new-entry':
        values = {
            k: v for k, v in request.POST.items() 
            if k not in ['csrfmiddlewaretoken', 'form-type'] and v != ''
        }
        values.update({'user_id': user_id})
        Portfolio(**values).save()
    redirect_view = redirect_view.split('/')
    return redirect(redirect_view[0], *redirect_view[1:])


def add_to_watchlist(request, item_id):
    user_id = request.session.get('user_id', -1)
    watchlist_items = Watchlist.objects.filter(user_id=user_id, item_id=item_id)

    if len(watchlist_items) == 0:
        DB.add_to_user_items(
            user_id, item_id, 'watchlist',
            dt.today().strftime('%Y-%m-%d')
        )
    else:
        Watchlist.objects.filter(user_id=user_id, item_id=item_id).delete()

    return redirect('item', item_id)
