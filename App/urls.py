from django.urls import path

from App.views import (index, item, join, login, misc, profile, search,
                       trending, user_items)

urlpatterns = [
    path('', index.index, name='index'),
    path('search_item/<path:current_view>',
         misc.search_item, name='search_item'),
    path('update_filters_in_session/<str:view>',
         misc.update_filters_in_session, name='update_filters_in_session'),
    path('item/<str:item_id>/', item.item, name='item'),
    path('join/', join.join, name='join'),
    path('login/', login.login, name='login'),
    path('logout', misc.logout, name='logout'),
    path('profile/', profile.profile, name='profile'),
    path('search/', search.search, name='search'),
    path('search/<path:theme_path>/', search.search, name='search'),
    path('trending/', trending.trending, name='trending'),
    path('portfolio/', user_items.portfolio, name='portfolio'),
    path('watchlist/', user_items.watchlist, name='watchlist'),
    path('view_POST/<str:view>/', user_items.view_POST, name='view_POST'),
    path('entry_item_handler/<str:view>/',
         user_items.entry_item_handler, name='entry_item_handler'),
    path('add_to_user_items/<str:view>/',
         user_items.add_to_user_items, name='add_to_user_items')
]
