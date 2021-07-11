from django.urls import path

from .views import (
    get_shares_list,
    ShareDetailView,
    ShareDeleteView,
    ShareTransactionsListView,
    TransactionsListView,
    TransactionDeleteView,
    TransactionDetailView,
    add_transaction,
    update_transaction,
    upload_transactions,
    update_share,
    refresh,
    CurrentShares,
    delete_shares,
    shares_insights
    #ChartData
)

app_name = 'shares'

urlpatterns = [
    path('', get_shares_list, name='shares-list'),
    path('add/', add_transaction, name='transaction-add'),
    path('refresh/', refresh, name='refresh'),
    path('transactions', TransactionsListView.as_view(), name='transactions-list'),
    path('upload/', upload_transactions, name='transaction-upload'),
    path('delete/', delete_shares, name='shares-delete'),
    path('insights', shares_insights, name='shares-insights'),
    path('transaction/<id>/delete', TransactionDeleteView.as_view(), name='transaction-delete'),
    path('<id>/', ShareDetailView.as_view(), name='share-detail'),
    path('<id>/update', update_share, name='share-update'),
    path('<id>/delete', ShareDeleteView.as_view(), name='share-delete'),
    path('<id>/transactions/', ShareTransactionsListView.as_view(), name='share-transactions-list'),
    path('transaction/<id>/update', update_transaction, name='transaction-detail'),
    path('transaction/<id>', TransactionDetailView.as_view(), name='transaction-detail'),
    path('api/get/current/<user_id>', CurrentShares.as_view()),
    path('api/get/current/', CurrentShares.as_view())
    #path('transaction/<id>/edit', edit_transaction, name='transaction-edit'),
    #path('api/chart/data/<id>', ChartData.as_view()),

]