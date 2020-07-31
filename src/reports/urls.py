from django.urls import path

from .views import (
    reports_base_view,
    reports_user_view,
    standalone_summary_view,
    standalone_user_view
)

app_name='reports'

urlpatterns = [
    path('', reports_base_view, name='reports'),
    path('user/<user_id>', reports_user_view, name='reports-user'),
    path('standalone-summary/', standalone_summary_view, name = 'standalone-summary'),
    path('standalone-user/<user_id>', standalone_user_view, name = 'standalone-user')
]