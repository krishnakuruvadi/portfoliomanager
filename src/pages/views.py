
from django.http import HttpResponse
from django.shortcuts import render
from shared.handle_get import *
from shared.handle_chart_data import get_user_contributions, get_goal_contributions, get_investment_data
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.
def home_view(request, *args, **kwargs): # *args, **kwargs
    print(args, kwargs)
    print(request.user)
    users = get_all_users_names_as_list()
    context = dict()
    context['all'] = dict()
    context['users'] = dict()
    all_debt = 0
    all_equity = 0
    all_distrib_labels = None
    all_target = 0
    all_achieved = 0
    all_distrib_vals = list()

    i = 1
    for user in users:
        context['users'][str(i)] = {'name':user}
        id = get_user_id_from_name(user)
        contrib = get_user_contributions(id)
        debt = contrib['debt']
        all_debt += debt
        equity = contrib['equity']
        all_equity += equity
        achieved = contrib['total']
        all_achieved += achieved
        target = contrib['target']
        if target < 1:
            target = 1
        all_target += target
        remaining = target - achieved
        if remaining < 0:
            remaining = 0
        remaining_per = int(remaining*100/target)
        achieve_per = int(achieved*100/target)
        context['users'][str(i)]['data'] = {
            "id": id,
            "debt": debt,
            "equity": equity,
            "distrib_labels": contrib['distrib_labels'],
            "distrib_vals": contrib['distrib_vals'],
            "distrib_colors": contrib['distrib_colors'],
            "achieved": achieved,
            "remaining": remaining,
            "remaining_per": remaining_per,
            "achieve_per": achieve_per,
        }
        if len(all_distrib_vals) == 0 :
            all_distrib_vals = [0]*len(contrib['distrib_vals'])
        for index, val in enumerate(contrib['distrib_vals']):
            all_distrib_vals[index] += val
        all_distrib_labels = contrib['distrib_labels']
        all_distrib_colors = contrib['distrib_colors']
        i = i + 1
    all_remaining = all_target - all_achieved
    all_remaining_per = int(all_remaining*100/all_target)
    all_achieve_per = int(all_achieved*100/all_target)
    context['all'] = {
            "debt": all_debt,
            "equity": all_equity,
            "distrib_labels": all_distrib_labels,
            "distrib_vals": all_distrib_vals,
            "distrib_colors": all_distrib_colors,
            "achieved": all_achieved,
            "remaining": all_remaining,
            "remaining_per": all_remaining_per,
            "achieve_per": all_achieve_per,
        }
    #for user in users:
    #start_date = get_start_day_across_portfolio()
    #context['investment_data'] = get_investment_data(start_date)
    print("context", context)
    #return HttpResponse("<h1>Hello World</h1>") # string of HTML code
    return render(request, "home.html", context)

'''
class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
'''

class InvestmentData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        start_date = get_start_day_across_portfolio()
        data = get_investment_data(start_date)
        return Response(data)