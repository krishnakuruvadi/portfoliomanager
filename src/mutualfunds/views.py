from django.shortcuts import render
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    ListView,
    DeleteView
)
import datetime
from dateutil.relativedelta import relativedelta
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from shared.utils import *
from shared.handle_get import *
from shared.handle_real_time_data import get_latest_vals, get_forex_rate, get_historical_mf_nav
from django.db import IntegrityError
from .models import Folio, MutualFundTransaction, Sip
from common.models import MutualFund, MFYearlyReturns, MFCategoryReturns
from .kuvera import Kuvera
from .pull_coin import pull_coin
from rest_framework.views import APIView
from rest_framework.response import Response
from .mf_helper import insert_trans_entry, calculate_xirr_all_users, calculate_xirr
from tasks.tasks import add_mf_transactions
from .pull_kuvera import pull_kuvera
from goal.goal_helper import get_goal_id_name_mapping_for_user
from decimal import Decimal
from common.helper import get_fund_houses

# Create your views here.

def get_folios(request):
    template = 'mutualfunds/folio_list.html'
    context = dict()
    context['users'] = get_all_users()
    show_zero_val_folio = True
    user = None
    if request.method == 'POST':
        print(request.POST)
        user = request.POST['user']
        show_zero_val_folio = 'show_zero_val' in request.POST
    context['object_list'] = list()
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
    context['user_name_mapping'] = get_all_users()
    context['show_zero_val'] = show_zero_val_folio
    total_investment = 0
    latest_value = 0
    as_on_date= None
    total_gain = 0
    folio_objs = None
    if not user or user=='':
        folio_objs = Folio.objects.all()
    else:
        folio_objs = Folio.objects.filter(user=user)
        context['user'] = user
    for folio_obj in folio_objs:
        if not folio_obj.latest_value:
            if show_zero_val_folio:
                context['object_list'].append(folio_obj)
            continue
        context['object_list'].append(folio_obj)
        if not as_on_date:
            as_on_date = folio_obj.as_on_date
        else:
            if as_on_date < folio_obj.as_on_date:
                as_on_date = folio_obj.as_on_date
        latest_value += folio_obj.latest_value
        total_investment += folio_obj.buy_value
        total_gain += folio_obj.gain
    context['as_on_date'] = as_on_date
    context['total_gain'] = round(total_gain, 2)
    context['total_investment'] = round(total_investment, 2)
    context['latest_value'] = round(latest_value, 2)
    cur_ret, all_ret = calculate_xirr(folio_objs)
    context['curr_ret'] = cur_ret
    context['all_ret'] = all_ret
    return render(request, template, context)

class FolioTransactionsListView(ListView):
    template_name = 'mutualfunds/transactions_list.html'
    ordering = ['-trans_date']
    def get_queryset(self):
        #folio = get_object_or_404(Folio, id=self.kwargs['id'])
        return MutualFundTransaction.objects.order_by('-trans_date').filter(folio__id=self.kwargs['id'])
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['folio_id'] = self.kwargs['id']
        print(data)
        return data

def sip_list(request):
    template = 'mutualfunds/sip_list.html'
    queryset = Sip.objects.all()
    data = dict()
    data['sips'] = list()
    amount = 0
    for sip in queryset:
        s = dict()
        s['folio'] = sip.folio.folio
        s['date'] = sip.sip_date
        s['amount'] = sip.amount
        s['user'] = sip.folio.user
        s['name'] = sip.folio.fund.name
        s['broker'] = ''
        brokers = set(())
        for trans in MutualFundTransaction.objects.filter(folio=sip.folio):
            if trans.broker and trans.broker != '':
                brokers.add(trans.broker)
        for b in brokers:
            if s['broker'] == '':
                s['broker'] = b
            else:
                s['broker'] = s['broker'] + ',' + b
        amount = amount + sip.amount
        data['sips'].append(s)
    data['sip_count'] = len(data['sips'])
    data['sip_amount'] = amount
    data['user_name_mapping'] = get_all_users()
    return render(request, template, data)

def fund_insights(request):
    template = 'mutualfunds/investment_insights.html'
    queryset = Folio.objects.all()
    data = dict()
    category = dict()
    blend = dict()
    total = 0
    for folio in queryset:
        if folio.fund.category:
            category[folio.fund.category] = add_two(category.get(folio.fund.category, 0), folio.latest_value)
        else:
            category['Unknown'] = add_two(category.get('Unknown', 0), folio.latest_value)
        if folio.fund.investment_style:
            blend[folio.fund.investment_style] = add_two(blend.get(folio.fund.investment_style, 0) , folio.latest_value)
        else:
            blend['Unknown'] = add_two(blend.get('Unknown', 0), folio.latest_value)
        total = add_two(total, folio.latest_value)

    data['blend_labels'] = list()
    data['blend_vals'] = list()
    data['blend_colors'] = list()
    data['blend_percents'] = list()
    for k,v in blend.items():
        if v:
            data['blend_labels'].append(k)
            data['blend_vals'].append(float(v))
            import random
            r = lambda: random.randint(0,255)
            data['blend_colors'].append('#{:02x}{:02x}{:02x}'.format(r(), r(), r()))
            h = float(v)*100/float(total)
            h = int(round(h))
            data['blend_percents'].append(h)
    
    data['category_labels'] = list()
    data['category_vals'] = list()
    data['category_colors'] = list()
    data['category_percents'] = list()
    for k,v in category.items():
        if v:
            data['category_labels'].append(k)
            data['category_vals'].append(float(v))
            import random
            r = lambda: random.randint(0,255)
            data['category_colors'].append('#{:02x}{:02x}{:02x}'.format(r(), r(), r()))
            h = float(v)*100/float(total)
            h = int(round(h))
            data['category_percents'].append(h)
    print('returning:', data)
    return render(request, template, data)


def fund_returns(request):
    template = 'mutualfunds/folio_returns.html'
    queryset = Folio.objects.all()
    data = dict()
    data['object_list'] = dict()
    for folio in queryset:
        if folio.fund.code not in data['object_list']:
            data['object_list'][folio.fund.code] = dict()
            data['object_list'][folio.fund.code]['name'] = folio.fund.name
            data['object_list'][folio.fund.code]['code'] = folio.fund.code
            data['object_list'][folio.fund.code]['id'] = folio.fund.id
            data['object_list'][folio.fund.code]['units'] = folio.units
            data['object_list'][folio.fund.code]['buy_value'] = folio.buy_value
            data['object_list'][folio.fund.code]['latest_value'] = folio.latest_value
            data['object_list'][folio.fund.code]['gain'] = folio.gain
            data['object_list'][folio.fund.code]['1d'] = folio.fund.return_1d
            data['object_list'][folio.fund.code]['1w'] = folio.fund.return_1w
            data['object_list'][folio.fund.code]['1m'] = folio.fund.return_1m
            data['object_list'][folio.fund.code]['3m'] = folio.fund.return_3m
            data['object_list'][folio.fund.code]['ytd'] = folio.fund.return_ytd
            data['object_list'][folio.fund.code]['1y'] = folio.fund.return_1y
            data['object_list'][folio.fund.code]['3y'] = folio.fund.return_3y
            data['object_list'][folio.fund.code]['5y'] = folio.fund.return_5y
            data['object_list'][folio.fund.code]['10y'] = folio.fund.return_10y
            data['object_list'][folio.fund.code]['15y'] = folio.fund.return_15y
            data['object_list'][folio.fund.code]['inception'] = folio.fund.return_incep

            try:
                yrly_returns = MFYearlyReturns.objects.filter(fund=folio.fund)

            except MFYearlyReturns.DoesNotExist:
                print('Yearly returns not found for code', folio.fund.code)
                for ret in ['1d','1w','1m','3m','1y','3y','5y','10y','15y','inception']:
                    data['object_list'][folio.fund.code][ret] = ''
        else:
            data['object_list'][folio.fund.code]['buy_value'] = add_two(data['object_list'][folio.fund.code]['buy_value'], folio.buy_value)
            data['object_list'][folio.fund.code]['latest_value'] = add_two(data['object_list'][folio.fund.code]['latest_value'], folio.latest_value)
            data['object_list'][folio.fund.code]['gain'] = add_two(data['object_list'][folio.fund.code]['gain'], folio.gain)
            data['object_list'][folio.fund.code]['units'] = add_two(data['object_list'][folio.fund.code]['units'], folio.units)

    ret = dict()
    ret['object_list'] = list()
    for _,v in data['object_list'].items():
        if v['units']:
            ret['object_list'].append(v)
    return render(request, template, ret)

def add_two(first, second):
    if first and second:
        return int(first+second)
    if first:
        return int(first)
    if second:
        return int(second)
    return None

def add_folio(request):
    template = 'mutualfunds/add_folio.html'
    if request.method == 'POST':
        print('inside add_folio')
        folio = request.POST['folio']
        fund = request.POST['fund']
        user = request.POST['user']
        print('user is of type:',type(user))
        notes = request.POST['notes']
        goal_id = None
        goal = request.POST['goal']
        if goal != '':
            goal_id = Decimal(goal)
        
        mf_obj = MutualFund.objects.get(code=fund)
        found = False
        try:
            fos = Folio.objects.filter(folio=folio)
            for fo in fos:
                if fo.fund.code == fund:
                    found = True
        except Exception as ex:
            pass
        
        if not found:
            Folio.objects.create(folio=folio,
                                 fund=mf_obj,
                                 user=user,
                                 goal=goal_id,
                                 notes=notes)
    users = get_all_users()
    fund_houses = dict()
    resp = get_fund_houses()
    for fh in sorted(resp):
        fund_houses[fh] = fh
    context = {'users':users, 'operation': 'Add Folio', 'fund_houses':fund_houses}
    return render(request, template, context)

def add_transaction(request, id):
    template = 'mutualfunds/add_transaction.html'
    folio = Folio.objects.get(id=id)
    user = get_user_name_from_id(folio.user)
    if request.method == 'POST':
        trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
        trans_type = request.POST['trans_type']
        price = get_float_or_none_from_string(request.POST['price'])
        units = get_float_or_none_from_string(request.POST['units'])
        conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
        trans_price = get_float_or_none_from_string(request.POST['trans_price'])
        broker = request.POST['broker']
        notes = request.POST['notes']
        insert_trans_entry(folio.folio, folio.fund.code, folio.user, trans_type, units, price, trans_date, notes, broker, conversion_rate, trans_price)
    users = get_all_users()
    context = {'users':users, 'operation': 'Add Transaction', 'folio':folio.folio, 'user':user, 'fund_name':folio.fund.name, 'folio_id':id}
    return render(request, template, context)

def update_transaction(request, id):
    template = 'mutualfunds/update_transaction.html'
    transaction = MutualFundTransaction.objects.get(id=id)
    if request.method == 'POST':
        #folio = request.POST['folio']
        #fund = request.POST['fund']
        #user = request.POST['user']
        #print('user is of type:',type(user))
        transaction.trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
        transaction.trans_type = request.POST['trans_type']
        transaction.price = get_float_or_none_from_string(request.POST['price'])
        transaction.units = get_float_or_none_from_string(request.POST['units'])
        transaction.conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
        transaction.trans_price = get_float_or_none_from_string(request.POST['trans_price'])
        transaction.broker = request.POST['broker']
        transaction.notes = request.POST['notes']
        if 'switch_trans' in request.POST:
            print('switch_trans', request.POST['switch_trans'])
            transaction.switch_trans = True
        else:
            transaction.switch_trans = False
        transaction.save()
    context = {'operation': 'Update Transaction'}
    context['trans_date'] = transaction.trans_date.strftime("%Y-%m-%d")
    context['trans_type'] = transaction.trans_type
    context['price'] = transaction.price
    context['units'] = transaction.units
    context['conversion_rate'] = transaction.conversion_rate
    context['trans_price'] = transaction.trans_price
    context['broker'] = transaction.broker
    context['notes'] = transaction.notes
    context['switch_trans'] = transaction.switch_trans  
    print('context', context) 
    return render(request, template, context)

class FolioDetailView(DetailView):
    template_name = 'mutualfunds/folio_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Folio, id=id_)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        id = data['object'].id
        folio_obj = self.get_object()
        data['isin'] = folio_obj.fund.isin
        data['isin2'] = folio_obj.fund.isin2
        data['mf_ref_id'] = folio_obj.fund.id
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        data['category'] = folio_obj.fund.category
        data['investment_style'] = folio_obj.fund.investment_style
        data['1D'] = folio_obj.fund.return_1d
        data['1W'] = folio_obj.fund.return_1w
        data['1M'] = folio_obj.fund.return_1m
        data['3M'] = folio_obj.fund.return_3m
        data['6M'] = folio_obj.fund.return_6m
        data['1Y'] = folio_obj.fund.return_1y
        data['3Y'] = folio_obj.fund.return_3y
        data['5Y'] = folio_obj.fund.return_5y
        data['10Y'] = folio_obj.fund.return_10y
        data['15Y'] = folio_obj.fund.return_15y
        data['Inception'] = folio_obj.fund.return_incep
        data['YTD'] = folio_obj.fund.return_ytd
        try:
            cat_returns = MFCategoryReturns.objects.get(category=folio_obj.fund.category)
            data['cat_1D_avg'] = cat_returns.return_1d_avg
            data['cat_1D_bot'] = cat_returns.return_1d_bot
            data['cat_1D_top'] = cat_returns.return_1d_top
            data['cat_1W_avg'] = cat_returns.return_1w_avg
            data['cat_1W_bot'] = cat_returns.return_1w_bot
            data['cat_1W_top'] = cat_returns.return_1w_top
            data['cat_1M_avg'] = cat_returns.return_1m_avg
            data['cat_1M_bot'] = cat_returns.return_1m_bot
            data['cat_1M_top'] = cat_returns.return_1m_top
            data['cat_3M_avg'] = cat_returns.return_3m_avg
            data['cat_3M_bot'] = cat_returns.return_3m_bot
            data['cat_3M_top'] = cat_returns.return_3m_top
            data['cat_6M_avg'] = cat_returns.return_6m_avg
            data['cat_6M_bot'] = cat_returns.return_6m_bot
            data['cat_6M_top'] = cat_returns.return_6m_top
            data['cat_1Y_avg'] = cat_returns.return_1y_avg
            data['cat_1Y_bot'] = cat_returns.return_1y_bot
            data['cat_1Y_top'] = cat_returns.return_1y_top
            data['cat_3Y_avg'] = cat_returns.return_3y_avg
            data['cat_3Y_bot'] = cat_returns.return_3y_bot
            data['cat_3Y_top'] = cat_returns.return_3y_top
            data['cat_5Y_avg'] = cat_returns.return_5y_avg
            data['cat_5Y_bot'] = cat_returns.return_5y_bot
            data['cat_5Y_top'] = cat_returns.return_5y_top
            data['cat_10Y_avg'] = cat_returns.return_10y_avg
            data['cat_10Y_bot'] = cat_returns.return_10y_bot
            data['cat_10Y_top'] = cat_returns.return_10y_top
            data['cat_YTD_avg'] = cat_returns.return_ytd_avg
            data['cat_YTD_bot'] = cat_returns.return_ytd_bot
            data['cat_YTD_top'] = cat_returns.return_ytd_top
            data['cat_Inception_avg'] = cat_returns.return_inception_avg
            data['cat_Inception_bot'] = cat_returns.return_inception_bot
            data['cat_Inception_top'] = cat_returns.return_inception_top
        except MFCategoryReturns.DoesNotExist:
            print(f'not able to find returns for category {folio_obj.fund.category}')
        data['curr_module_id'] = 'id_mf_module'
        return data

class FolioDeleteView(DeleteView):
    template_name = 'mutualfunds/folio_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Folio, id=id_)

    def get_success_url(self):
        return reverse('mutualfund:folio-list')
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['folio_id'] = self.kwargs['id']
        print(data)
        return data

class TransactionsListView(ListView):
    template_name = 'mutualfunds/transactions_list.html'
    #paginate_by = 15
    model = MutualFundTransaction
    ordering = ['-trans_date']

class TransactionDeleteView(DeleteView):
    template_name = 'mutualfunds/transaction_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(MutualFundTransaction, id=id_)

    def get_success_url(self):
        return reverse('mutualfund:transactions-list')

class TransactionDetailView(DetailView):
    template_name = 'mutualfunds/transaction_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(MutualFundTransaction, id=id_)

def upload_transactions(request):
    template = 'mutualfunds/upload_transactions.html'
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    if request.method == 'POST':
        if 'pull-user' in request.POST:
            pull_user = request.POST['pull-user']
            pull_broker = request.POST.get('pullBrokerControlSelect')
            pull_emailid = request.POST.get('pull-email-id')
            pull_passwd = request.POST.get('pull-passwd')
            pull_user_name = request.POST.get('pull_kuvera_acc_name')
            print('user:',pull_user)
            print('broker:',pull_broker)
            print('emailid:',pull_emailid)
            #print('passwd:',pull_passwd)
            if pull_broker == 'KUVERA':
                pull_kuvera(pull_user, pull_emailid, pull_passwd, pull_user_name)
            elif pull_broker == 'COIN ZERODHA':
                pull_coin(pull_user, pull_emailid, pull_passwd, pull_user_name)
        else:
            uploaded_file = request.FILES['document']
            user = request.POST['user']
            broker = request.POST.get('brokerControlSelect')
            passwd = request.POST.get('cas-pass')
            fs = FileSystemStorage()
            file_locn = fs.save(uploaded_file.name, uploaded_file)
            print(settings.MEDIA_ROOT)
            full_file_path = settings.MEDIA_ROOT + '/' + file_locn
            print(f'Read transactions from file: {uploaded_file} {broker} {passwd} {file_locn} {full_file_path}')
            add_mf_transactions(broker, user, full_file_path, passwd)
    users = get_all_users()
    context = {'users':users}
    return render(request, template, context)

def update_folio(request, id):
    template = 'mutualfunds/update_folio.html'
    folio = Folio.objects.get(id=id)
    if request.method == 'POST':
        folio.user = int(request.POST['user'])
        print('user is:',folio.user)
        goal = request.POST['goal']
        if goal != '':
            folio.goal = int(goal)
        else:
            folio.goal = None
        folio.notes = request.POST['notes']
        folio.save()
        
    else:
        users = get_all_users()

        context = {'users':users,
                   'folio':folio.folio,
                   'fund_name':folio.fund.name,
                   'user':folio.user,
                   'goal':folio.goal,
                   'notes':folio.notes,
                   'goals':get_goal_id_name_mapping_for_user(folio.user)}
        print(context)
        return render(request, template, context)
    return HttpResponseRedirect("../")

def mf_refresh(request):
    print("inside mf_refresh")
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()
    folio_objs = Folio.objects.all()
    for folio_obj in folio_objs:
        if folio_obj.as_on_date != datetime.date.today():
            vals = get_historical_mf_nav(folio_obj.fund.code, start, end, True)
            if vals:
                for val in vals:
                    for k,v in val.items():
                        if k and v:
                            if not folio_obj.as_on_date or k > folio_obj.as_on_date:
                                folio_obj.as_on_date = k
                                folio_obj.latest_price = v
                                if folio_obj.country == 'India':
                                    folio_obj.conversion_rate = 1
                                folio_obj.latest_value = float(folio_obj.latest_price) * float(folio_obj.conversion_rate) * float(folio_obj.units)
                                folio_obj.save()
        folio_obj.latest_value = float(folio_obj.latest_price) * float(folio_obj.conversion_rate) * float(folio_obj.units)
        if folio_obj.latest_value:
            folio_obj.gain=float(folio_obj.latest_value)-float(folio_obj.buy_value)
            #print("folio_obj.gain",folio_obj.gain)
            #print("folio_obj.latest_value",folio_obj.latest_value)
            #print("folio_obj.buy_value",folio_obj.buy_value)
            #print("folio_obj.latest_price",folio_obj.latest_price)
            #print("folio_obj.units",folio_obj.units)
            folio_obj.save()
    print('done with request')
    return HttpResponseRedirect(reverse('mutualfund:folio-list'))

class CurrentMfs(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, user_id=None):
        print("inside CurrentMfs")
        folios = dict()
        folios['folio'] = list()
        if user_id:
            folio_objs = Folio.objects.filter(units__gt=0).filter(user=user_id)
        else:
            folio_objs = Folio.objects.filter(units__gt=0)
        for folio in folio_objs:
            data = dict()
            data['folio'] = folio.folio
            data['fund'] = folio.fund.name
            data['units'] = folio.units
            data['buy_price'] = folio.buy_price
            data['buy_value'] = folio.buy_value
            data['user_id'] = folio.user
            data['user'] = get_user_name_from_id(folio.user)
            data['notes'] = folio.notes
            data['latest_price'] = folio.latest_price
            data['latest_value'] = folio.latest_value
            data['as_on_date'] = folio.as_on_date
            data['gain'] = folio.gain
            folios['folio'].append(data)
        return Response(folios)

def delete_folios(request):
    Folio.objects.all().delete()
    return HttpResponseRedirect('../')