from django import forms
from django.forms import SelectDateWidget, ChoiceField
from .models import Ssy, SsyEntry
from shared.handle_get import get_all_users_names_as_list, get_all_goals_for_user_as_list, get_goal_id_from_name, get_goal_name_from_id

class SsyModelForm(forms.ModelForm):
    class Meta:
        model = Ssy
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
        for x in get_all_users_names_as_list():
            self.fields['user'].choices.append((x, x))
        print("in form user is ", self.instance.user)
        if self.instance.user and self.instance.user != '':
            goal_list = get_all_goals_for_user_as_list(self.instance.user)
            for x in goal_list:
                self.fields['goal'].choices.append((x, x))
        if self.instance.goal:
            self.instance.goal = get_goal_name_from_id(self.instance.goal)
            self.initial['goal'] = self.instance.goal

    def clean_goal(self):
        goal = self.cleaned_data['goal']
        if goal == '':
            return None
        goal_id = get_goal_id_from_name(self.cleaned_data['user'], goal)
        print("goal_id", goal_id)
        return goal_id 

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
