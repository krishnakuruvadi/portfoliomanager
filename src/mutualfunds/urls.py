from django.urls import path

from .views import (
    FolioListView,
    FolioDetailView,
    FolioDeleteView,
    FolioTransactionsListView,
    TransactionsListView,
    TransactionDeleteView,
    TransactionDetailView,
    add_transaction,
    add_folio,
    upload_transactions,
    update_folio,
    mf_refresh,
    CurrentMfs,
    update_transaction,
    fund_returns,
    fund_insights,
    delete_folios
    #ChartData
)

app_name = 'mutualfund'

urlpatterns = [
    path('', FolioListView.as_view(), name='folio-list'),
    path('add/', add_folio, name='folio-add'),
    path('refresh/', mf_refresh, name='refresh'),
    path('transactions', TransactionsListView.as_view(), name='transactions-list'),
    path('upload/', upload_transactions, name='transaction-upload'),
    path('delete/', delete_folios, name='folio-delete'),
    path('transaction/<id>/delete', TransactionDeleteView.as_view(), name='transaction-delete'),
    path('returns', fund_returns, name='fund-returns'),
    path('insights', fund_insights, name='fund-insights'),
    path('<id>/', FolioDetailView.as_view(), name='folio-detail'),
    path('<id>/update', update_folio, name='folio-update'),
    path('<id>/delete', FolioDeleteView.as_view(), name='folio-delete'),
    path('<id>/transactions/', FolioTransactionsListView.as_view(), name='folio-transactions-list'),
    path('<id>/transactions/add', add_transaction, name='folio-add-transaction'),
    path('transaction/<id>', TransactionDetailView.as_view(), name='transaction-detail'),

    path('transaction/<id>/update', update_transaction, name='transaction-update'),
    #path('api/chart/data/<id>', ChartData.as_view()),
    path('api/get/current/<user_id>', CurrentMfs.as_view()),
    path('api/get/current/', CurrentMfs.as_view())
]