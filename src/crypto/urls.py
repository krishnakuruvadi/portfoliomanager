from django.urls import path

from .views import (
    get_crypto,
    add_transaction,
    get_transactions,
    delete_all_crypto,
    delete_crypto,
    crypto_detail,
    all_transactions,
    upload_transactions,
    transaction_detail,
    insights,
    update_transaction,
    update_crypto,
    delete_transaction
)

app_name = 'crypto'

urlpatterns = [
    path('', get_crypto, name='crypto-list'),
    path('add/', add_transaction, name='crypto-add'),
    path('<id>/transactions', get_transactions, name='get-transactions'),
    path('<id>/update', update_crypto, name='update-crypto'),
    path('<id>/transaction/<trans_id>/update/', update_transaction, name='update-transaction'),
    path('<id>/transaction/<trans_id>/delete/', delete_transaction, name='delete-transaction'),
    path('upload/', upload_transactions, name='transaction-upload'),
    path('delete/', delete_all_crypto, name='delete-all-crypto'),
    path('<id>/delete/', delete_crypto, name='delete-crypto'),
    path('transactions/', all_transactions, name='all-transactions'),
    path('insights/', insights, name='insights'),
    path('<id>/transaction/<trans_id>', transaction_detail, name='transaction-detail'),
    path('<id>/', crypto_detail, name='crypto-detail'),
]