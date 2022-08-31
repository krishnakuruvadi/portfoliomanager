from django.shortcuts import render
from shared.handle_get import *

# Create your views here.

def reports_base_view(request):
    template = 'reports/reports_base.html'
    context = {'curr_module_id': 'id_reports_module'}
    return render(request, template, context)

def standalone_summary_view(request):
    template = 'reports/standalone_summary.html'
    context = {'curr_module_id': 'id_reports_module'}
    return render(request, template, context)

def reports_user_view(request, user_id):
    template = 'reports/reports_user.html'
    context = {'user_id': user_id, 'curr_module_id': 'id_reports_module'}
    return render(request, template, context)

def standalone_user_view(request, user_id):
    template = 'reports/standalone_user.html'
    context = {'user_id': user_id, 'curr_module_id': 'id_reports_module'}
    return render(request, template, context)