from django.urls import path

from .views import (
    tax_home,
    tax_details
)

app_name = 'tax'
urlpatterns = [
    path('', tax_home, name='tax-home'),
    path('details', tax_details, name='tax-details'),
]