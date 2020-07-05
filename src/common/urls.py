from django.urls import path

from .views import (
    common_list_view,
    refresh,
    StockListView,
    MFListView,
    mf_refresh,
    mf_trash,
    mf_bse_star,
    HistoricalStockPriceList,
    HistoricalMFPriceList,
    MfDetailView
)
# Create your views here.

app_name = 'common'
urlpatterns = [
    path('', common_list_view, name='common-list'),
    path('stock', StockListView.as_view(), name='stock-list'),
    
    path('refresh', refresh, name='refresh'),
    path('stock/refresh', refresh, name='refresh'),
    path('mf/refresh', mf_refresh, name='mf-refresh'),
    path('stock/<id>/historical-prices', HistoricalStockPriceList.as_view(), name='historical-stock-price-list'),
    path('mf/<id>/historical-prices', HistoricalMFPriceList.as_view(), name='historical-mf-price-list'),
    path('mf/<id>/', MfDetailView.as_view(), name='mf-detail'),
    path('mf/trash', mf_trash, name='mf-trash'),
    path('mf/bsestar', mf_bse_star, name='mf-bse-star'),
    path('mf/', MFListView.as_view(), name='mf-list')
]