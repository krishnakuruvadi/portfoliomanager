from django import forms
from django.forms import SelectDateWidget
from .models import Espp
import datetime

class EsppModelForm(forms.ModelForm):
    class Meta:
        model = Espp
        fields =[
            'purchase_date',
            'exchange',
            'symbol',
            'subscription_fmv',
            'purchase_fmv',
            'purchase_price',
            'purchase_conversion_rate',
            'shares_purchased',
            'sell_date',
            'sell_price',
            'sell_conversion_rate',
            'user',
            'goal'
        ]
        # Always put date in %Y-%m-%d for chrome to show things properly 
        widgets = {
            'purchase_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'placeholder':'Select a date', 'type':'date'}),
            'sell_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'placeholder':'Select a date', 'type':'date'}),
        }
