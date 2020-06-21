from django.urls import path

from .views import (
    common_list_view,
    refresh,
    HistoricalStockPriceList
)
# Create your views here.

app_name = 'common'
urlpatterns = [
    path('', common_list_view, name='common-list'),
    path('refresh', refresh, name='refresh'),
    path('stock/<id>/historical-prices', HistoricalStockPriceList.as_view(), name='historical-stock-price-list')
]