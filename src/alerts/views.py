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
    context['alerts'] = list()
    for a in queryset:
        e = dict()
        e['seen'] = a.seen
        e['action_url'] = a.action_url
        e['time'] = get_in_preferred_tz(a.time)
        e['content'] = a.content
        e['summary'] = a.summary
        e['severity'] = a.severity
        e['id'] = a.id
        context['alerts'].append(e)

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

class AlertsDeleteView(DeleteView):
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(models.Alert, id=id_)

    def get_success_url(self):
        return reverse('alerts:alerts-list')
    
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

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