from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.template import Context
from shared.handle_delete import delete_user
from shared.handle_chart_data import get_user_contributions
from .models import User
from shared.utils import get_date_or_none_from_string, get_in_preferred_tz
from epf.epf_interface import EpfInterface
from espp.espp_interface import EsppInterface
from fixed_deposit.fd_interface import FdInterface
from ppf.ppf_interface import PpfInterface
from ssy.ssy_interface import SsyInterface
from shares.share_interface import ShareInterface
from mutualfunds.mf_interface import MfInterface
from retirement_401k.r401k_interface import R401KInterface
from rsu.rsu_interface import RsuInterface
from insurance.insurance_interface import InsuranceInterface
from gold.gold_interface import GoldInterface
from bankaccounts.bank_account_interface import BankAccountInterface
from crypto.crypto_interface import CryptoInterface
import datetime
from shared.utils import get_min
from dateutil import tz
from pytz import timezone
from common.helper import get_preferences
from shared.handle_get import *
from dateutil.relativedelta import relativedelta
from pages.models import InvestmentData
import json


# Create your views here.
class UserListView(ListView):
    template_name = 'users/user_list.html'
    queryset = User.objects.all()
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['curr_module_id'] = 'id_user_module'
        data['current_networth'] = 0
        for user in data['user_list']:
            data['current_networth'] += float(user.total_networth)
            if user.as_on:
                data['as_on'] = user.as_on
        preferred_currency = get_preferences('currency')
        data['preferred_currency'] = preferred_currency if preferred_currency else 'INR'
        data['as_on'] = get_in_preferred_tz(data['as_on'])
        print(data)
        return data

def contrib_deduct_str(c, d):
    return str(int(c)) + ' / ' + str(int(d))


def get_start_day_for_user(id_):
    start_day = datetime.date.today()
    for intf in [EpfInterface, EsppInterface, FdInterface, MfInterface, PpfInterface, SsyInterface, ShareInterface, R401KInterface, RsuInterface, InsuranceInterface, GoldInterface, BankAccountInterface, CryptoInterface]:
        start_day = get_min(intf.get_start_day_for_user(id_), start_day)
    return start_day

class UserDetailView(DetailView):
    template_name = 'users/user_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(User, id=id_)

    def get_context_data(self, **kwargs):
        id_ = self.kwargs.get("id")
        data = super().get_context_data(**kwargs)

        start_day = get_start_day_for_user(id_)

        #new_start_day = datetime.date(start_day.year, start_day.month, 1)
        
        curr_yr = datetime.date.today().year
        investment_types = list()
        yrly = dict()
        for yr in range(start_day.year, curr_yr+1):
            total_c = 0
            total_d = 0
            yrly[yr] = dict()
            c, d = PpfInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'PPF' in investment_types:
                investment_types.append('PPF')
            yrly[yr]['PPF'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = R401KInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not '401K' in investment_types:
                investment_types.append('401K')
            yrly[yr]['401K'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = RsuInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'RSU' in investment_types:
                investment_types.append('RSU')
            yrly[yr]['RSU'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = InsuranceInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'Insurance' in investment_types:
                investment_types.append('Insurance')
            yrly[yr]['Insurance'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = GoldInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'Gold' in investment_types:
                investment_types.append('Gold')
            yrly[yr]['Gold'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = BankAccountInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'Cash' in investment_types:
                investment_types.append('Cash')
            yrly[yr]['Cash'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = EpfInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'EPF' in investment_types:
                investment_types.append('EPF')
            yrly[yr]['EPF'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = SsyInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'SSY' in investment_types:
                investment_types.append('SSY')
            yrly[yr]['SSY'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = MfInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'MF' in investment_types:
                investment_types.append('MF')
            yrly[yr]['MF'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = EsppInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'ESPP' in investment_types:
                investment_types.append('ESPP')
            yrly[yr]['ESPP'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = FdInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'FD' in investment_types:
                investment_types.append('FD')
            yrly[yr]['FD'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = ShareInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'Shares' in investment_types:
                investment_types.append('Shares')
            yrly[yr]['Shares'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = CryptoInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'Crypto' in investment_types:
                investment_types.append('Crypto')
            yrly[yr]['Crypto'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            yrly[yr]['Total'] = contrib_deduct_str(total_c, total_d)

        for item in ['PPF', '401K', 'RSU', 'EPF', 'ESPP', 'SSY', 'MF', 'FD', 'Shares', 'Insurance', 'Crypto']:
            if item not in investment_types:
                for yr in range(start_day.year, curr_yr+1):
                    del yrly[yr][item]
        investment_types.append('Total')

        data['yrly_investment'] = yrly
        data['investment_types'] = investment_types
        data['curr_module_id'] = 'id_user_module'
        utc = self.get_object().as_on
        from_zone = tz.tzutc()
        utc = utc.replace(tzinfo=from_zone)
        preferred_tz = get_preferences('timezone')
        if not preferred_tz:
            preferred_tz = 'Asia/Kolkata'
        data['last_updated'] = utc.astimezone(timezone(preferred_tz)).strftime("%Y-%m-%d %H:%M:%S")
        print(f'user detail view data {data}')
        return data


class UserDeleteView(DeleteView):
    template_name = 'users/user_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(User, id=id_)

    def get_success_url(self):
        return reverse('users:user-list')
    
    def delete(self, request, *args, **kwargs):
        print(request)
        delete_user(kwargs['id'])
        return super(DeleteView, self).delete(request, *args, **kwargs)

def add_user(request):
    template = 'users/add_user.html'
    if request.method == 'POST':
        name = request.POST['name']
        short_name = request.POST['short_name']
        dob = get_date_or_none_from_string(request.POST['dob'])
        email = request.POST['email']
        notes = request.POST['notes']
        User.objects.create(name=name, dob=dob, notes=notes, email=email, short_name=short_name)
    context = {'curr_module_id': 'id_user_module'}
    return render(request, template, context=context)

def update_user(request, id):
    template = 'users/add_user.html'
    try:
        user_obj = User.objects.get(id=id)
        if request.method == 'POST':
            user_obj.name = request.POST['name']
            user_obj.short_name = request.POST['short_name']
            user_obj.email = request.POST['email']
            user_obj.dob = request.POST['dob']
            user_obj.notes = request.POST['notes']
            user_obj.save()
        else:
            short_name = user_obj.short_name
            if not short_name:
                short_name = ''
            context = {'curr_module_id': 'id_user_module', 'name': user_obj.name, 'short_name': short_name, 'email':user_obj.email, 'dob':user_obj.dob.strftime("%Y-%m-%d"), 'notes':user_obj.notes}
            return render(request, template, context=context)
        return HttpResponseRedirect("../")
    except User.DoesNotExist:
        pass

class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        data = dict()
        try:
            user_obj = User.objects.get(id=id)
            contrib = get_user_contributions(id)
            debt = contrib['debt']
            equity = contrib['equity']
            achieved = contrib['total']
            target = contrib['target']
            if target < 1:
                target = 1
            remaining = target - achieved
            if remaining < 0:
                remaining = 0
            remaining_per = round(remaining*100/target, 2)
            achieve_per = round(achieved*100/target, 2)
            data = {
                "id": id,
                "debt": debt,
                "equity": equity,
                "gold":contrib['Gold'],
                'cash':contrib['Cash'],
                'crypto':contrib['Crypto'],
                "distrib_labels": contrib['distrib_labels'],
                "distrib_vals": contrib['distrib_vals'],
                "distrib_colors": contrib['distrib_colors'],
                "achieved": achieved,
                "remaining": remaining,
                "remaining_per": remaining_per,
                "achieve_per": achieve_per,
            }
        except Exception as e:
            print(e)
        finally:
            print(data)
            return Response(data)

class Users(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None):
        data = dict()
        data['user_list'] = list()
        user_objs = User.objects.all()
        for user_obj in user_objs:
            obj = dict()
            obj['id'] = user_obj.id
            obj['name'] = user_obj.name
            data['user_list'].append(obj)
        return Response(data)

class UserMonthlyContribDeduct(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None, year=None):
        data = dict()
        try:
            print(f'id {id} year {year}')
            id_int = int(id)
            yr = int(year)
            user_obj = User.objects.get(id=id_int)
            data['vals'] = dict()
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for month in range(0,12):
                data['vals'][months[month]] = list()
            data['headers'] = list()
            totalc = [0]*12
            totald = [0]*12
            for intf in [EpfInterface, EsppInterface, FdInterface, MfInterface, PpfInterface, SsyInterface, ShareInterface, R401KInterface, RsuInterface, InsuranceInterface, GoldInterface, BankAccountInterface, CryptoInterface]:
                data['headers'].append(intf.get_chart_name())
                c,d = intf.get_user_monthly_contrib(id_int, yr)
                for month in range(0,12):
                    data['vals'][months[month]].append(contrib_deduct_str(c[month],d[month]))
                    totalc[month] += c[month]
                    totald[month] += d[month]
            for month in range(0,12):
                data['vals'][months[month]].append(contrib_deduct_str(totalc[month],totald[month]))
            data['headers'].append('Total')
        except Exception as e:
            print(e)
        finally:
            print(data)
            return Response(data)

def insights_view(request):
    template = 'users/insights.html'
    try:
        context =dict()
        users = get_all_users_names_as_list()
        context = dict()
        context['all'] = dict()
        context['users'] = dict()

        i = 1
        today = datetime.date.today()
        start_day_for_family = today
        for user in users:
            context['users'][str(i)] = {'name':user}
            id = get_user_id_from_name(user)
            contribs = list()
            contrib = 0
            #contrib = get_user_contributions(id)
            start_day = get_start_day_for_user(id)
            #start_day = datetime.date(day=1,month=1,year=2009)
            end_year = today.year+1
            start_day_for_family = get_min(start_day_for_family, start_day)
            for yr in range(start_day.year, end_year):
                contrib_totals = [0]*12
                for intf in [EpfInterface, EsppInterface, FdInterface, MfInterface, PpfInterface, SsyInterface, ShareInterface, R401KInterface, RsuInterface, InsuranceInterface, GoldInterface, BankAccountInterface, CryptoInterface]:
                    c,d = intf.get_user_monthly_contrib(id, yr)
                    for month in range(0,12):
                        contrib_totals[month] += c[month] + d[month]
                for month in range(0,12):
                    dt = datetime.date(day=1, month=month+1, year=yr)+relativedelta(months=1)+relativedelta(days=-1)
                    if dt <= today:
                        contribs.append({'x':dt.strftime('%Y-%m-%d'), 'y':round(contrib_totals[month]+contrib,2)})
                        contrib += contrib_totals[month]
            context['users'][str(i)]['contribs'] = contribs
            context['users'][str(i)]['totals'] = list()
            i = i + 1
        context['users'][str(i)] = {'name':'All'}
        max_vals = 0
        for j in range(1,i):
            max_vals = max_vals if max_vals > len(context['users'][str(j)]['contribs']) else len(context['users'][str(j)]['contribs'])
        context['users'][str(i)]['contribs'] = list()
        print(f"start: {context['users'][str(i)]['contribs']}")
        for k in range(max_vals-1,-1,-1):
            tt = 0
            tt_d = None
            for j in range(1,i):
                ul = len(context['users'][str(i)]['contribs'])
                jl = len(context['users'][str(j)]['contribs'])
                if  ul< jl:
                    #context['users'][str(i)]['contribs'][k]['y'] += context['users'][str(j)]['contribs'][k]['y']
                    #context['users'][str(i)]['contribs'][k]['x'] = context['users'][str(j)]['contribs'][k]['x']
                    tt += context['users'][str(j)]['contribs'][jl-ul-1]['y']
                    tt_d = context['users'][str(j)]['contribs'][jl-ul-1]['x']
            context['users'][str(i)]['contribs'].insert(0,{'x':tt_d, 'y':round(tt,2)})
        try:
            investment_data = InvestmentData.objects.get(user='all')
            context['users'][str(i)]['totals'] = json.loads(investment_data.total_data.replace("\'", "\""))
        except InvestmentData.DoesNotExist:
            context['users'][str(i)]['totals'] = list()
        print(context)
        return render(request, template, context=context)
    except User.DoesNotExist:
        return HttpResponseRedirect("../")
