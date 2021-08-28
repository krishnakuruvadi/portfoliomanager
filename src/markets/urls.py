from django.urls import path

from .views import (
    pe_view,
    markets_home,
    news_view,
    returns_view
)

app_name = 'markets'

urlpatterns = [
    path('', markets_home, name='markets-home'),
    path('pe/', pe_view, name='pe-view'),
    path('news/', news_view, name='news-view'),
    path('returns/', returns_view, name='returns-view')
]