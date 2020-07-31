from django.shortcuts import render
import datetime
from dateutil.relativedelta import relativedelta
from shared.handle_get import *

# Create your views here.

def reports_base_view(request):
    template = 'reports/reports_base.html'
    context = dict()
    return render(request, template, context)

def standalone_summary_view(request):
    template = 'reports/standalone_summary.html'
    context = dict()
    return render(request, template, context)

def reports_user_view(request, user_id):
    template = 'reports/reports_user.html'
    context = {'user_id': user_id}
    return render(request, template, context)

def standalone_user_view(request, user_id):
    template = 'reports/standalone_user.html'
    context = {'user_id': user_id}
    return render(request, template, context)