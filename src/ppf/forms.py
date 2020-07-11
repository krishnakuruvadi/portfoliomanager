from django import forms
from django.forms import SelectDateWidget, ChoiceField
from .models import Ppf, PpfEntry
from shared.handle_get import *

class PpfModelForm(forms.ModelForm):
    class Meta:
        model = Ppf
        fields =[
            'number',
            'start_date',
            'user',
            'goal',
        ]
        # Always put date in %Y-%m-%d for chrome to show things properly 
        widgets = {
            'start_date': forms.DateInput(format=('%Y-%m-%d'), attrs={'placeholder':'Select a date', 'type':'date'}),
        }
    user = ChoiceField(required=True)
    goal = ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].choices = [('','')]
        self.fields['goal'].choices = [('','')]
        users = get_all_users()
        for k,v in users.items():
            self.fields['user'].choices.append((k, v))
        print("in form user is ", self.instance.user)
        goal_list = get_all_goals_id_to_name_mapping()
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
