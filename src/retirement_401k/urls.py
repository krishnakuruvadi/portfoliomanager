from django.urls import path

from .views import (
    add_account,
    AccountDeleteView,
    account_detail,
    get_accounts,
    update_account,
    get_transactions,
    add_transaction,
    edit_transaction,
    TransactionDeleteView,
    links,
    add_nav,
    delete_nav
)

app_name = 'retirement_401k'
urlpatterns = [
    path('', get_accounts, name='account-list'),
    path('create/', add_account, name='account-create'),
    path('links/', links, name='links'),
    path('<id>/', account_detail, name='account-detail'),
    path('<id>/update/', update_account, name='account-update'),
    path('<id>/delete/', AccountDeleteView.as_view(), name='account-delete'),
    path('<id>/transactions/', get_transactions, name='transaction-list'),
    path('<id>/add-transaction/', add_transaction, name='transaction-add'),
    path('<id>/add-nav/', add_nav, name='nav-add'),
    path('<id>/delete-nav/<nav_id>', delete_nav, name='nav-delete'),
    path('<id>/edit-transaction/', edit_transaction, name='transaction-edit'),
    path('<id>/delete-transaction/', TransactionDeleteView.as_view(), name='transaction-delete')
]