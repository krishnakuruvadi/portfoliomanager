from django import forms
from django.forms import SelectDateWidget
from .models import Epf, EpfEntry


class EpfModelForm(forms.ModelForm):
    class Meta:
        model = Epf
        fields =[
            'number',
            'company',
            'start_date',
            'end_date',
            'user',
            'goal',
        ]