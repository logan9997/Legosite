from django.urls import path

from App.views import (
     index, item, join, login, misc, 
     search, settings, trending, user_items
)

urlpatterns = [
    path(
        '', index.index, name='index'
     ),
    path(
        'search_item/<path:current_view>',misc.search_item, name='search_item'
     ),
    path(
        'update_filters_in_session/<str:view>',
         misc.update_filters_in_session, name='update_filters_in_session'
     ),
    path(
        'item/<str:item_id>/', item.item, name='item'
     ),
    path(
        'join/', join.join, name='join'
     ),
    path(
        'login/', login.login, name='login'
     ),
    path(
        'logout', misc.logout, name='logout'
     ),
    path(
        'settings/', settings.settings, name='settings'
     ),
    path(
        'search/', search.search, name='search'
     ),
    path(
        'search/<path:theme_path>/', search.search, name='search'
     ),
    path(
        'trending/', trending.trending, name='trending'
     ),
    path(
        'portfolio/', user_items.portfolio, name='portfolio'
     ),
    path(
        'portfolio/item/<str:item_id>',
          user_items.portfolio_item, name='portfolio_item'
     ),
    path(
        'watchlist/', user_items.watchlist, name='watchlist'
     ),
]
