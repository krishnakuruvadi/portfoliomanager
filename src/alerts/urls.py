from django.urls import path

from .views import (
    AlertsDetailView,
    AlertsDeleteView,
    toggle_seen,
    delete_all,
    read_all,
    get_alerts
)

app_name = 'alerts'

urlpatterns = [
    path('', get_alerts, name='alerts-list'),
    path('delete', delete_all, name='delete-all'),
    path('read', read_all, name='read-all'),
    path('<id>/', AlertsDetailView.as_view(), name='alert-detail'),
    path('<id>/delete', AlertsDeleteView.as_view(), name='alert-delete'),
    path('<id>/toggle_seen/', toggle_seen, name='toggle-alert-seen')
]