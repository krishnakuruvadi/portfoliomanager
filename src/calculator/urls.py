from django.urls import path

from .views import (
    calculator
)

app_name = 'calculator'

urlpatterns = [
    path('', calculator, name='calculator'),    
]