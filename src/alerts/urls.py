from django.urls import path

from .views import (
    AlertsListView,
    AlertsDetailView,
    toggle_seen
)

app_name = 'alerts'

urlpatterns = [
    path('', AlertsListView.as_view(), name='alerts-list'),
    path('<id>/', AlertsDetailView.as_view(), name='alert-detail'),
    path('<id>/toggle_seen/', toggle_seen, name='toggle-alert-seen')
]