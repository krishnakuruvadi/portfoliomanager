from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView
)
from . import models
from shared.handle_get import *
from django.http import HttpResponseRedirect

# Create your views here.

class AlertsListView(ListView):
    template_name = 'alerts/alerts_list.html'
    queryset = models.Alert.objects.all()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        return data

class AlertsDetailView(DetailView):
    template_name = 'alerts/alert_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(models.Alert, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        return data

def toggle_seen(request, id):
    alert = get_object_or_404(models.Alert, id=id)
    if alert.seen:
        alert.seen = False
    else:
        alert.seen = True
    alert.save()
    return HttpResponseRedirect('../../')