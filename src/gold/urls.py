from django.urls import path

from .views import (
    get_trans,
    add_trans,
    trans_detail,
    sell_transactions,
    add_sell_trans,
    delete_sell,
    sell_trans_detail,
    update_trans,
    trans_delete,
    delete_all_trans
)

app_name = 'gold'

urlpatterns = [
    path('', get_trans, name='trans-list'),
    path('add/', add_trans, name='add-trans'),
    path('delete/', delete_all_trans, name='delete-all-trans'),
    path('<id>/', trans_detail, name='gold-detail'),
    path('<id>/delete', trans_delete, name='gold-delete'),
    path('<id>/update', update_trans, name='update-trans'),
    path('<id>/sell_transactions', sell_transactions, name='sell-transactions'),
    path('<id>/sell/', add_sell_trans, name='add-sell-transaction'),
    path('<id>/sell/<sell_id>', sell_trans_detail, name='sell-transaction-detail'),
    path('<id>/delete_sell',delete_sell,name='delete-sell')
]