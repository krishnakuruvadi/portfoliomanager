from django.urls import path

from .views import (
    common_list_view,
    refresh,
    StockListView,
    StockDetailView,
    MFListView,
    mf_refresh,
    mf_trash,
    mf_bse_star,
    HistoricalStockPriceList,
    HistoricalMFPriceList,
    MfDetailView,
    get_mutual_funds,
    ScrollDataView,
    preferences
)
# Create your views here.

app_name = 'common'
urlpatterns = [
    path('', common_list_view, name='common-list'),
    path('stocks', StockListView.as_view(), name='stocks-list'),
    path('stocks/<id>/', StockDetailView.as_view(), name='stock-detail'),
    path('stocks/refresh', refresh, name='refresh'),
    path('stocks/<id>/historical-prices', HistoricalStockPriceList.as_view(), name='historical-stock-price-list'),

    path('mf/refresh', mf_refresh, name='mf-refresh'),
    path('mf/<id>/historical-prices', HistoricalMFPriceList.as_view(), name='historical-mf-price-list'),
    path('mf/trash', mf_trash, name='mf-trash'),
    path('mf/bsestar', mf_bse_star, name='mf-bse-star'),
    path('mf/avail_funds/', get_mutual_funds),
    path('mf/<id>/', MfDetailView.as_view(), name='mf-detail'),
    path('mf/', MFListView.as_view(), name='mf-list'),
    path('preferences', preferences, name='preference'),
    path('api/get/scrolldata', ScrollDataView.as_view())
]