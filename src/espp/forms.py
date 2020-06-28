from django import forms
from django.forms import SelectDateWidget, ChoiceField
from .models import Espp
import datetime
from shared.handle_get import *

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
        if self.instance.user and self.instance.user != '':
            goal_list = get_all_goals_id_to_name_mapping()
            for k,v in goal_list.items():
                self.fields['goal'].choices.append((k, v))
        if self.instance.goal:
            #self.instance.goal = get_goal_name_from_id(self.instance.goal)
            self.initial['goal'] = self.instance.goal
    '''
    def clean_goal(self):
        goal = self.cleaned_data['goal']
        if goal == '':
            return None
        goal_id = get_goal_id_from_name(self.cleaned_data['user'], goal)
        print("goal_id", goal_id)
        return goal_id
    '''