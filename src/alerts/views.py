from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView
)
from . import models
from shared.handle_get import *
from django.http import HttpResponseRedirect
from django.urls import reverse
from shared.utils import get_in_preferred_tz


# Create your views here.

def get_alerts(request):
    template = 'alerts/alert_list.html'
    queryset = models.Alert.objects.all()
    context = dict()
    context['actions'] = list()
    context['notifications'] = list()
    context['marketing'] = list()
    context['application'] = list()
    notifs = 0
    acts = 0
    mrktngs = 0
    applns = 0


    for a in queryset:
        e = dict()
        e['seen'] = a.seen
        e['action_url'] = a.action_url
        e['time'] = get_in_preferred_tz(a.time)
        e['content'] = a.content
        e['summary'] = a.summary
        e['severity'] = a.severity
        e['id'] = a.id
        if a.alert_type == 'Action':
            context['actions'].append(e)
            if not a.seen:
                acts += 1
        elif a.alert_type == 'Marketing':
            context['marketing'].append(e)
            if not a.seen:
                mrktngs += 1
        elif a.alert_type == 'Application':
            context['application'].append(e)
            if not a.seen:
                applns += 1
        else:
            context['notifications'].append(e)
            if not a.seen:
                notifs += 1

    context['num_notification'] = notifs
    context['num_action'] = acts
    context['num_marketing'] = mrktngs
    context['num_application'] = applns

    #print(context)

    return render(request, template, context)

class AlertsDetailView(DetailView):
    template_name = 'alerts/alert_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(models.Alert, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        return data

def delete_alert(request, id):
    try:
        a = models.Alert.objects.get(id=id)
        a.delete()
    except Exception as ex:
        print(f'exception {ex} when deleting alert id {id}')
    return HttpResponseRedirect(reverse('alerts:alerts-list'))
    
def toggle_seen(request, id):
    alert = get_object_or_404(models.Alert, id=id)
    if alert.seen:
        alert.seen = False
    else:
        alert.seen = True
    alert.save()
    return HttpResponseRedirect('../../')

def delete_all(request):
    models.Alert.objects.all().delete()
    return HttpResponseRedirect(reverse('alerts:alerts-list'))

def read_all(request):
    for alert in models.Alert.objects.all():
        alert.seen = True
        alert.save()
    return HttpResponseRedirect(reverse('alerts:alerts-list'))
