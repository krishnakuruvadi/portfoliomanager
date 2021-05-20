from django import forms
from django.forms import SelectDateWidget, ChoiceField
from .models import Espp
import datetime
from shared.handle_get import *
from goal.goal_helper import get_goal_id_name_mapping_for_user


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
            'user',
            'goal'
        ]
        # Always put date in %Y-%m-%d for chrome to show things properly 
        widgets = {
            'purchase_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'placeholder':'Select a date', 'type':'date'}),
        }
    user = ChoiceField(required=True)
    goal = ChoiceField(required=False, validators=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].choices = [('','')]
        self.fields['goal'].choices = [('','')]
        users = get_all_users()
        for k,v in users.items():
            self.fields['user'].choices.append((k, v))
        print("in form user is ", self.instance.user)
        if self.instance.user:
            goal_list = get_goal_id_name_mapping_for_user(self.instance.user)
            for k,v in goal_list.items():
                self.fields['goal'].choices.append((k, v))
            if self.instance.goal:
                #self.instance.goal = get_goal_name_from_id(self.instance.goal)
                self.initial['goal'] = self.instance.goal
    
    def clean_goal(self):
        goal = self.cleaned_data['goal']
        if goal == '':
            return None
        return goal
