from App.views import (
    index,
    item,
    join,
    login,
    profile,
    search,
    trending,
    misc,
)
from django.urls import path

urlpatterns = [
    path('',index.index , name='index'),
    path('search_item/<path:current_view>', misc.search_item, name='search_item'),
    path('item/<str:item_id>/',item.item , name='item'),
    path('join/',join.join , name='join'),
    path('login/',login.login , name='login'),
    path('profile/',profile.profile , name='profile'),
    path('search/',search.search , name='search'),
    path('trending/',trending.trending , name='trending'),
]