
from django.http import HttpResponse
from django.shortcuts import render
from shared.handle_get import *
from shared.handle_chart_data import get_user_contributions, get_goal_contributions, get_investment_data
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import InvestmentData
import json
from dateutil import tz
from pytz import timezone
from common.helper import get_preferences
from users.user_interface import UserInterface, user_count

# Create your views here.
def home_view(request, *args, **kwargs): # *args, **kwargs
    
    if user_count() == 0:
        return render(request, 'welcome.html')
    else:
        pass
    
    print(args, kwargs)
    print(request.user)
    users = get_all_users_names_as_list()
    context = dict()
    context['all'] = dict()
    context['users'] = dict()
    all_debt = 0
    all_equity = 0
    all_gold = 0
    all_crypto = 0
    all_cash = 0
    all_distrib_labels = list()
    all_distrib_colors = list()
    all_target = 0
    all_achieved = 0
    all_distrib_vals = list()
    all_distrib = dict()

    i = 1
    for user in users:
        context['users'][str(i)] = {'name':user}
        id = get_user_id_from_name(user)
        contrib = get_user_contributions(id)
        debt = contrib.get('debt', 0)
        all_debt += debt
        equity = contrib.get('equity', 0)
        all_equity += equity
        gold = contrib.get('Gold', 0)
        all_gold += gold
        crypto = contrib.get('Crypto', 0)
        all_crypto += crypto
        cash = contrib.get('Cash', 0)
        all_cash += cash
        achieved = contrib.get('total', 0)
        all_achieved += achieved
        target = contrib.get('target', 0)
        if target < 1:
            target = 1
        all_target += target
        remaining = target - achieved
        if remaining < 0:
            remaining = 0
        remaining_per = round(remaining*100/target, 2)
        achieve_per = round(achieved*100/target, 2)
        
        context['users'][str(i)]['data'] = {
            "id": id,
            "debt": debt,
            "equity": equity,
            "gold": gold,
            "cash": cash,
            "crypto": crypto,
            "distrib_labels": contrib['distrib_labels'],
            "distrib_vals": contrib['distrib_vals'],
            "distrib_colors": contrib['distrib_colors'],
            "achieved": achieved,
            "remaining": remaining,
            "remaining_per": remaining_per,
            "achieve_per": achieve_per,
            "debt_per": round(debt*100/(debt+equity+gold+cash+crypto+1), 2),
            "equity_per": round(equity*100/(debt+equity+gold+cash+crypto+1), 2),
            "gold_per": round(gold*100/(debt+equity+gold+cash+crypto+1), 2),
            "crypto_per": round(crypto*100/(debt+equity+gold+cash+crypto+1), 2),
            "cash_per": round(cash*100/(debt+equity+gold+cash+crypto+1), 2)
        }

        for d in range(len(contrib['distrib_labels'])):
            if contrib['distrib_labels'][d] not in all_distrib:
                all_distrib[contrib['distrib_labels'][d]] = dict()
                all_distrib[contrib['distrib_labels'][d]]['color'] = contrib['distrib_colors'][d]
                all_distrib[contrib['distrib_labels'][d]]['amount'] = contrib['distrib_vals'][d]
            else:
                all_distrib[contrib['distrib_labels'][d]]['amount'] += contrib['distrib_vals'][d]

        i = i + 1
    if all_target > 0:
        all_remaining = all_target - all_achieved
        all_remaining_per = round(all_remaining*100/all_target, 2)
        all_achieve_per = round(all_achieved*100/all_target, 2)
    else:
        all_remaining = all_target = all_achieved = 0
        all_remaining_per = all_achieve_per = 0

    for k,v in all_distrib.items():
        all_distrib_labels.append(k)
        all_distrib_colors.append(v['color'])
        all_distrib_vals.append(v['amount'])
    context['all'] = {
            "debt": all_debt,
            "equity": all_equity,
            "gold": all_gold,
            "cash": all_cash,
            "crypto": all_crypto,
            "distrib_labels": all_distrib_labels,
            "distrib_vals": all_distrib_vals,
            "distrib_colors": all_distrib_colors,
            "achieved": all_achieved,
            "remaining": all_remaining,
            "remaining_per": all_remaining_per,
            "achieve_per": all_achieve_per,
            "debt_per": round(all_debt*100/(all_debt+all_equity+all_gold+all_cash+all_crypto+1), 2),
            "equity_per": round(all_equity*100/(all_debt+all_equity+all_gold+all_cash+all_crypto+1), 2),
            "gold_per": round(all_gold*100/(all_debt+all_equity+all_gold+all_cash+all_crypto+1), 2),
            "crypto_per": round(all_crypto*100/(all_debt+all_equity+all_gold+all_cash+all_crypto+1), 2),
            "cash_per": round(all_cash*100/(all_debt+all_equity+all_gold+all_cash+all_crypto+1), 2),
        }
    context['investment_data'] = dict()
    try:
        investment_data = InvestmentData.objects.get(user='all')
        context['investment_data']['ppf'] = json.loads(investment_data.ppf_data.replace("\'", "\""))
        context['investment_data']['epf'] = json.loads(investment_data.epf_data.replace("\'", "\""))
        context['investment_data']['ssy'] = json.loads(investment_data.ssy_data.replace("\'", "\""))
        context['investment_data']['fd'] =  json.loads(investment_data.fd_data.replace("\'", "\""))
        context['investment_data']['espp'] = json.loads(investment_data.espp_data.replace("\'", "\""))
        context['investment_data']['rsu'] = json.loads(investment_data.rsu_data.replace("\'", "\""))
        context['investment_data']['shares'] = json.loads(investment_data.shares_data.replace("\'", "\""))
        context['investment_data']['mf'] = json.loads(investment_data.mf_data.replace("\'", "\""))
        context['investment_data']['r401k'] = json.loads(investment_data.r401k_data.replace("\'", "\""))
        context['investment_data']['insurance'] = json.loads(investment_data.insurance_data.replace("\'", "\""))
        context['investment_data']['gold'] = json.loads(investment_data.gold_data.replace("\'", "\""))
        context['investment_data']['cash'] = json.loads(investment_data.cash_data.replace("\'", "\""))
        context['investment_data']['loan'] = json.loads(investment_data.loan_data.replace("\'", "\""))
        context['investment_data']['crypto'] = json.loads(investment_data.crypto_data.replace("\'", "\""))
        context['investment_data']['total'] = json.loads(investment_data.total_data.replace("\'", "\""))
        context['investment_data']['start_date'] =  investment_data.start_day_across_portfolio.strftime("%Y-%b-%d")
        utc = investment_data.as_on_date
        from_zone = tz.tzutc()
        utc = utc.replace(tzinfo=from_zone)
        preferred_tz = get_preferences('timezone')
        if not preferred_tz:
            preferred_tz = 'Asia/Kolkata'
        context['investment_data']['as_on_date_time'] = utc.astimezone(timezone(preferred_tz)).strftime("%Y-%b-%d %H:%M:%S")

    except InvestmentData.DoesNotExist:
        pass
    context['curr_module_id'] = 'id_dashboard_module'
    print("context", context)
    return render(request, "home.html", context)


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
                'r401k':json.loads(investment_data.r401k_data.replace("\'", "\"")),
                'insurance':json.loads(investment_data.insurance_data.replace("\'", "\"")),
                'gold':json.loads(investment_data.gold_data.replace("\'", "\"")),
                'cash':json.loads(investment_data.cash_data.replace("\'", "\"")),
                'crypto':json.loads(investment_data.crypto_data.replace("\'", "\"")),
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

class Export(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        ret = dict()
        try:
            ret = UserInterface.export()
        except Exception as ex:
            print(f'exception when getting export data {ex}')
        return Response(ret)