from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from .models import Task, TaskState
from django.views.generic import (
    ListView,
    DetailView
)
from .tasks import *

# Create your views here.
class TaskListView(ListView):
    template_name = 'tasks/task_list.html'
    queryset = Task.objects.all()
    
    def get_context_data(self, **kwargs):

        available_tasks = {
            'get_mf_navs': {
                'description':'Get Mutual Fund latest NAV'
            },
            'update_mf': {
                'description':'Update Mutual Fund investment with latest value'
            },
            'update_espp': {
                'description':'Update ESPP investment with latest value'
            },
            'update_mf_schemes': {
                'description':'Check and update latest mutual schemes from fund houses from AMFII'
            },
            'update_bse_star_schemes': {
                'description':'Check and update latest mutual schemes from fund houses from BSE STaR' 
            },
            'update_investment_data':{
                'description':'Update investment data for home view chart'
            },
            'update_mf_mapping': {
                'description': 'Update any missing mapping info between AMFII, BSE STaR and KUVERA'
            },
            'update_goal_contrib':{
                'description': 'Update different investment data for each goal'
            },
            'analyse_mf':{
                'description':'Analyse different Mutual Funds where users have active investment'
            }
        }
        for task in available_tasks.keys():
            found = False
            for task_obj in Task.objects.all():
                if task_obj.task_name == task:
                    found = True
            if not found:
                Task.objects.create(
                    task_name = task,
                    description = available_tasks[task]['description']
                )
        data = super().get_context_data(**kwargs)
        data['task_state_mapping'] = get_task_state_to_name_mapping()
        print(data)
        return data

def get_task_state_to_name_mapping():
    task_sate_mapping = dict()
    for state, name in Task.TASK_STATE_CHOICES:
        task_sate_mapping[state] = name
    return task_sate_mapping

def run_task(request, id):
    task = get_object_or_404(Task, id=id)
    possibles = globals().copy()
    possibles.update(locals())
    method = possibles.get(task.task_name)
    if not method:
        raise NotImplementedError("Method %s not implemented" % task.task_name)
    
    if task.current_state == TaskState.Unknown.value:
        task.current_state = TaskState.Scheduled.value
        task.save()
    method()
    return HttpResponseRedirect('../../')

class TaskDetailView(DetailView):
    template_name = 'tasks/task_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Task, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        return data