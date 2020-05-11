from django import forms
from django.forms import SelectDateWidget
from .models import Ppf, PpfEntry


class PpfModelForm(forms.ModelForm):
    class Meta:
        model = Ppf
        fields =[
            'number',
            'start_date',
            'user',
            'goal',
        ]

class PpfEntryModelForm(forms.ModelForm):
    class Meta:
        model = PpfEntry
        fields =[
            'number',
            'trans_date',
            'notes',
            'reference',
            'entry_type',
            'amount',
            'interest_component',
        ]
        #exclude = ('number',)
        widgets = {
            'trans_date': SelectDateWidget(),
            'number': forms.TextInput(attrs={'disabled': True}),
        }
