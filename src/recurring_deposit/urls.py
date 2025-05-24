from django.urls import path

from .views import (
    RecurringDepositListView,
    RecurringDepositDetailView,
    delete_rd,
    add_recurring_deposit,
    update_recurring_deposit,
    ChartData,
    CurrentRds
)

app_name = 'recurring-deposits'

urlpatterns = [
    path('', RecurringDepositListView.as_view(), name='recurring-deposit-list'),
    path('create/', add_recurring_deposit, name='recurring-deposit-add'),
    path('<id>/', RecurringDepositDetailView.as_view(), name='recurring-deposit-detail'),
    path('<id>/delete/', delete_rd, name='recurring-deposit-delete'),
    path('<id>/update/', update_recurring_deposit, name='recurring-deposit-update'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('api/get/current/<user_id>', CurrentRds.as_view()),
    path('api/get/current/', CurrentRds.as_view())
]