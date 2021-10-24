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
    add_fund,
    get_nav_history,
    add_nav,
    delete_all_nav,
    delete_nav,
    fund_detail,
    update_policy,
    delete_policy
)

app_name = 'insurance'
urlpatterns = [
    path('', get_insurance, name='policy-list'),
    path('add/', add_policy, name='add-policy'),
    path('delete/', delete_policies, name='delete-all-policies'),
    path('<id>/', policy_detail, name='policy-detail'),
    path('<id>/update', update_policy, name='update-policy'),
    path('<id>/delete', delete_policy, name='delete-policy'),
    path('<id>/add_transaction', add_transaction, name='add-transaction'),
    path('<id>/upload_transactions', upload_transactions, name='upload-transactions'),
    path('<id>/add_fund', add_fund, name='add-fund'),
    path('<id>/fund/<fund_id>', fund_detail, name='fund-detail'),
    path('<id>/transactions', get_transactions, name='get-transactions'),
    path('<id>/transaction/<trans_id>/delete', delete_transaction, name='transaction-delete'),
    path('<id>/transaction/<trans_id>', transaction_detail, name='transaction-detail'),
    path('<id>/nav/<fund_id>', get_nav_history, name='nav-history'),
    path('<id>/nav/<fund_id>/add_nav', add_nav, name='add-nav'),
    path('<id>/nav/<fund_id>/delete_all_nav', delete_all_nav, name='delete-all-nav'),
    path('<id>/nav/<fund_id>/delete_nav/<nav_id>', delete_nav, name='delete-nav'),
]