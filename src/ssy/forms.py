from django import forms
from django.forms import SelectDateWidget, ChoiceField
from .models import Ssy, SsyEntry
from shared.handle_get import *
from goal.goal_helper import get_goal_id_name_mapping_for_user

class SsyEntryModelForm(forms.ModelForm):
    class Meta:
        model = SsyEntry
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
