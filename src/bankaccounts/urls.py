from django.urls import path

from .views import (
    get_accounts,
    add_account,
    get_transactions,
    account_detail,
    delete_accounts,
    delete_account,
    add_transaction,
    transaction_detail,
    delete_transactions,
    delete_transaction,
    update_account,
    upload_transactions,
    update_transaction,
    insights
)

app_name = 'bankaccounts'

urlpatterns = [
    path('', get_accounts, name='account-list'),
    path('insights/', insights, name='insights'),
    path('add/', add_account, name='account-add'),
    path('<id>/transactions', get_transactions, name='get-transactions'),
    path('delete/', delete_accounts, name='delete-all-accounts'),
    path('<id>/delete/', delete_account, name='delete-account'),
    path('<id>/update/', update_account, name='update-account'),
    path('<id>/add_transaction/', add_transaction, name='add-transaction'),
    path('<id>/upload_transactions/', upload_transactions, name='upload-transaction'),
    path('<id>/', account_detail, name='account-detail'),
    path('<id>/transaction/<trans_id>', transaction_detail, name='transaction-detail'),
    path('<id>/delete_transactions', delete_transactions, name='delete-transactions'),
    path('<id>/transaction/<trans_id>/delete', delete_transaction, name='delete-transaction'),
    path('<id>/transaction/<trans_id>/update', update_transaction, name='update-transaction')
]