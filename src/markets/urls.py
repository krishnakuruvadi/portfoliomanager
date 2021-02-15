from django.urls import path

from .views import (
    pe_view,
    markets_home
)

app_name = 'markets'

urlpatterns = [
    path('', markets_home, name='markets-home'),
    path('pe/', pe_view, name='pe-view'),
]