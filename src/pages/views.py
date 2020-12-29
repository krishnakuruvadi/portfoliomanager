
from django.http import HttpResponse
from django.shortcuts import render
from shared.handle_get import *
from shared.handle_chart_data import get_user_contributions, get_goal_contributions, get_investment_data
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import InvestmentData
import json

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
    all_distrib_labels = list()
    all_distrib_colors = list()
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
    if all_target > 0:
        all_remaining = all_target - all_achieved
        all_remaining_per = int(all_remaining*100/all_target)
        all_achieve_per = int(all_achieved*100/all_target)
    else:
        all_remaining = all_target = all_achieved = 0
        all_remaining_per = all_achieve_per = 0

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

class GetInvestmentData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        investment_data = None
        try:
            investment_data = InvestmentData.objects.get(user='all')
            return Response({
                    'ppf':json.loads(investment_data.ppf_data.replace("\'", "\"")),
                    'epf':json.loads(investment_data.epf_data.replace("\'", "\"")),
                    'ssy':json.loads(investment_data.ssy_data.replace("\'", "\"")),
                    'fd': json.loads(investment_data.fd_data.replace("\'", "\"")),
                    'espp': json.loads(investment_data.espp_data.replace("\'", "\"")),
                    'rsu':json.loads(investment_data.rsu_data.replace("\'", "\"")),
                    'shares':json.loads(investment_data.shares_data.replace("\'", "\"")),
                    'mf':json.loads(investment_data.mf_data.replace("\'", "\"")),
                    'total':json.loads(investment_data.total_data.replace("\'", "\"")),
                    'start_date': investment_data.start_day_across_portfolio,
                    'as_on_date_time': investment_data.as_on_date
            })

        except InvestmentData.DoesNotExist:
            start_date = get_start_day_across_portfolio()
            investment_data = get_investment_data(start_date)
            investment_data['start_date'] = start_date
            investment_data['as_on_date_time'] = datetime.datetime.now()

        return Response(investment_data)