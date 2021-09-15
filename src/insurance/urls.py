from django.urls import path

from .views import (
    get_insurance,
    add_policy,
    delete_policies,
    policy_detail,
    add_transaction,
    get_transactions,
    transaction_detail,
    delete_transaction,
    upload_transactions,
    add_fund
)

app_name = 'insurance'
urlpatterns = [
    path('', get_insurance, name='insurance-list'),
    path('add/', add_policy, name='add-policy'),
    path('delete/', delete_policies, name='delete-all-policies'),
    path('<id>/', policy_detail, name='policy-detail'),
    path('<id>/add_transaction', add_transaction, name='add-transaction'),
    path('<id>/upload_transactions', upload_transactions, name='upload-transactions'),
    path('<id>/add_fund', add_fund, name='add-fund'),
    path('<id>/transactions', get_transactions, name='get-transactions'),
    path('<id>/transaction/<trans_id>/delete', delete_transaction, name='transaction-delete'),
    path('<id>/transaction/<trans_id>', transaction_detail, name='transaction-detail')
]