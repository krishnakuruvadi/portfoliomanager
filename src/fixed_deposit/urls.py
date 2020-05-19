from django.urls import path

from .views import (
    FixedDepositListView,
    FixedDepositDetailView,
    FixedDepositDeleteView,
    add_fixed_deposit
)

app_name = 'fixed-deposits'

urlpatterns = [
    path('', FixedDepositListView.as_view(), name='fixed-deposit-list'),
    path('create/', add_fixed_deposit, name='fixed-deposit-add'),
    path('<id>/', FixedDepositDetailView.as_view(), name='fixed-deposit-detail'),
    path('<id>/delete/', FixedDepositDeleteView.as_view(), name='fixed-deposit-delete'),
]