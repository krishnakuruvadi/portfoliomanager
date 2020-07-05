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
    upload_transactions,
    update_folio,
    mf_refresh,
    #ChartData
)

app_name = 'mutualfund'

urlpatterns = [
    path('', FolioListView.as_view(), name='folio-list'),
    path('add/', add_transaction, name='transaction-add'),
    path('refresh/', mf_refresh, name='refresh'),
    path('transactions', TransactionsListView.as_view(), name='transactions-list'),
    path('upload/', upload_transactions, name='transaction-upload'),
    path('transaction/<id>/delete', TransactionDeleteView.as_view(), name='transaction-delete'),
    path('<id>/', FolioDetailView.as_view(), name='folio-detail'),
    path('<id>/update', update_folio, name='folio-update'),
    path('<id>/delete', FolioDeleteView.as_view(), name='folio-delete'),
    path('<id>/transactions/', FolioTransactionsListView.as_view(), name='folio-transactions-list'),
    path('transaction/<id>', TransactionDetailView.as_view(), name='transaction-detail'),

    #path('transaction/<id>/edit', edit_transaction, name='transaction-edit'),
    #path('api/chart/data/<id>', ChartData.as_view()),

]