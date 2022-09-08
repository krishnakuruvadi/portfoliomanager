from django.urls import path, re_path

from .views import (
    FixedDepositListView,
    FixedDepositDetailView,
    delete_fd,
    add_fixed_deposit,
    update_fixed_deposit,
    ChartData,
    CurrentFds
)

app_name = 'fixed-deposits'

urlpatterns = [
    path('', FixedDepositListView.as_view(), name='fixed-deposit-list'),
    path('create/', add_fixed_deposit, name='fixed-deposit-add'),
    path('<id>/', FixedDepositDetailView.as_view(), name='fixed-deposit-detail'),
    path('<id>/delete/', delete_fd, name='fixed-deposit-delete'),
    path('<id>/update/', update_fixed_deposit, name='fixed-deposit-update'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('api/get/current/<user_id>', CurrentFds.as_view()),
    path('api/get/current/', CurrentFds.as_view())
]