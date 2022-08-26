from django.urls import path

from .views import (
    common_list_view,
    check_app_updates,
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
    preferences,
    ForexDataView,
    password_list_view,
    password_detail_view,
    password_add_view,
    password_trash,
    PasswordDeleteView,
    update_password,
    IndexListView,
    IndexDetailView,
    HistoricalIndexPointList
)
# Create your views here.

app_name = 'common'
urlpatterns = [
    path('', common_list_view, name='common-list'),
    path('check-update/', check_app_updates, name='check-app-updates'),
    path('stocks', StockListView.as_view(), name='stocks-list'),
    path('stocks/<id>/', StockDetailView.as_view(), name='stock-detail'),
    path('indices', IndexListView.as_view(), name='index-list'),
    path('index/<id>/', IndexDetailView.as_view(), name='index-detail'),
    path('index/<id>/historical-points', HistoricalIndexPointList.as_view(), name='historical-index-point-list'),
    path('stocks/refresh', refresh, name='refresh'),
    path('stocks/<id>/historical-prices', HistoricalStockPriceList.as_view(), name='historical-stock-price-list'),
    path('passwords/', password_list_view, name='passwords-list'),
    path('passwords/add', password_add_view, name='password-add'),
    path('passwords/trash', password_trash, name='password-trash'),
    path('passwords/<id>/', password_detail_view, name='password-detail'),
    path('passwords/<id>/delete', PasswordDeleteView.as_view(), name='password-delete'),
    path('passwords/<id>/update', update_password, name='password-update'),
    path('mf/refresh', mf_refresh, name='mf-refresh'),
    path('mf/<id>/historical-prices', HistoricalMFPriceList.as_view(), name='historical-mf-price-list'),
    path('mf/trash', mf_trash, name='mf-trash'),
    path('mf/bsestar', mf_bse_star, name='mf-bse-star'),
    path('mf/avail_funds/', get_mutual_funds),
    path('mf/<id>/', MfDetailView.as_view(), name='mf-detail'),
    path('mf/', MFListView.as_view(), name='mf-list'),
    path('preferences', preferences, name='preference'),
    path('api/get/scrolldata', ScrollDataView.as_view()),
    path('api/get-forex/<int:year>/<int:month>/<int:day>/<str:from_currency>/<str:to_currency>', ForexDataView.as_view())
]