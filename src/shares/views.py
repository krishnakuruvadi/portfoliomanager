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
from .models import Share, Transactions
from common.models import Dividendv2, Bonusv2, Splitv2, Stock
from .shares_helper import *
from shared.utils import *
from shared.handle_get import *
from shared.handle_real_time_data import get_latest_vals, get_forex_rate
from .zerodha import Zerodha
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from tasks.tasks import pull_share_trans_from_broker, pull_share_trans_from_rh
from django.conf import settings
from django.db.models import Q
import time
# Create your views here.

class TransactionsListView(ListView):
    template_name = 'shares/transactions_list.html'
    queryset = Transactions.objects.all()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['share_name'] = ''
        data['share_id'] = ''
        return data

def get_shares_list(request):
    template = 'shares/shares_list.html'
    context = dict()
    context['users'] = get_all_users()
    context['exchanges'] = ['NSE/BSE', 'NASDAQ', 'NYSE']
    show_zero_val_shares = True
    user = None
    exchange = None
    if request.method == 'POST':
        print(request.POST)
        user = request.POST['user']
        exchange = request.POST['exchange']
        show_zero_val_shares = 'show_zero_val' in request.POST
    context['object_list'] = list()
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
    context['user_name_mapping'] = get_all_users()
    context['show_zero_val'] = show_zero_val_shares
    total_investment = 0
    latest_value = 0
    as_on_date= None
    total_gain = 0
    realised_gain = 0
    share_objs = None
    if not user or user=='':
        if not exchange or exchange=='': 
            share_objs = Share.objects.all()
        else:
            if exchange == 'NSE/BSE':
                share_objs = Share.objects.filter(Q(exchange='NSE') | Q(exchange='BSE') | Q(exchange='NSE/BSE'))
            else:
                share_objs = Share.objects.filter(exchange=exchange)
            context['exchange'] = exchange
    else:
        if not exchange or exchange=='': 
            share_objs = Share.objects.filter(user=user)
        else:
            if exchange == 'NSE/BSE':
                share_objs = Share.objects.filter(Q(exchange='NSE') | Q(exchange='BSE') | Q(exchange='NSE/BSE'))
            else:
                share_objs = Share.objects.filter(user=user, exchange=exchange)
            context['exchange'] = exchange
        context['user'] = user
    for share_obj in share_objs:
        if share_obj.realised_gain:
            realised_gain = realised_gain + float(share_obj.realised_gain)
        if not share_obj.latest_value:
            if show_zero_val_shares:
                context['object_list'].append(share_obj)
            continue
        context['object_list'].append(share_obj)
        if not as_on_date:
            as_on_date = share_obj.as_on_date
        else:
            if as_on_date < share_obj.as_on_date:
                as_on_date = share_obj.as_on_date
        latest_value += share_obj.latest_value
        total_investment += share_obj.buy_value
        total_gain += share_obj.gain
    context['as_on_date'] = as_on_date
    context['total_gain'] = round(total_gain, 2)
    context['total_investment'] = round(total_investment, 2)
    context['latest_value'] = round(latest_value, 2)
    #cur_ret, all_ret = calculate_xirr(folio_objs)
    #context['curr_ret'] = cur_ret
    #context['all_ret'] = all_ret
    context['realised_gain'] = round(realised_gain, 2)
    return render(request, template, context)

class ShareTransactionsListView(ListView):
    template_name = 'shares/transactions_list.html'
    #queryset = Transactions.objects.all()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        id_ = self.kwargs.get("id")
        print("id is:",id_)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        o = get_object_or_404(Share, id=id_)
        data['share_name'] = o.exchange+'/'+o.symbol+'/'+get_user_short_name_or_name_from_id(o.user)
        data['share_id'] = o.id
        return data

    def get_queryset(self):
        id_ = self.kwargs.get("id")
        print("id is:",id_)
        share = get_object_or_404(Share, id=id_)
        return Transactions.objects.filter(share=share)

class ShareDeleteView(DeleteView):
    template_name = 'shares/share_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Share, id=id_)

    def get_success_url(self):
        return reverse('shares:shares-list')

class TransactionDeleteView(DeleteView):
    template_name = 'shares/transaction_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Transactions, id=id_)

    def get_success_url(self):
        return reverse('shares:transactions-list')

class ShareDetailView(DetailView):
    template_name = 'shares/share_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Share, id=id_)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        obj = self.get_object()        
        try:
            stock = Stock.objects.get(exchange=obj.exchange, symbol=obj.symbol)
            divs = list()
            for dividend in Dividendv2.objects.filter(stock=stock).order_by('-announcement_date'):
                divs.append({'announcement_date':dividend.announcement_date, 'ex_date':dividend.ex_date, 'amount':dividend.amount})
            if len(divs) > 0:
                data['dividend'] = divs
            splits = list()
            for split in Splitv2.objects.filter(stock=stock).order_by('-announcement_date'):
                splits.append({'announcement_date':split.announcement_date, 'ex_date':split.ex_date, 'old_fv':str(split.old_fv), 'new_fv':str(split.new_fv)})
            if len(splits) > 0:
                data['split'] = splits
            bonuses = list()
            for bonus in Bonusv2.objects.filter(stock=stock).order_by('-announcement_date'):
                bonuses.append({'announcement_date':bonus.announcement_date, 'record_date':bonus.record_date, 'ex_date':bonus.ex_date, 'ratio':str(bonus.ratio_num)+':'+str(bonus.ratio_denom)})
            if len(bonuses) > 0:
                data['bonus'] = bonuses
        except Stock.DoesNotExist:
            print(f'stock doesnt exist in db {obj.exchange} {obj.symbol}')
        return data

class TransactionDetailView(DetailView):
    template_name = 'shares/transaction_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Transactions, id=id_)


def update_share(request, id):
    template = 'shares/update_share.html'
    share = Share.objects.get(id=id)
    if request.method == 'POST':
        goal = request.POST['goal']
        share.user = int(request.POST['user'])
        print('user is:',share.user)
        if goal != '':
            share.goal = int(goal)
        else:
            share.goal = None
        notes = request.POST['notes']
        share.notes = notes
        if 'etf' in request.POST:
            print('etf', request.POST['etf'])
            share.etf = True
        else:
            share.etf = False
        share.save()
        
    else:
        
        users = get_all_users()
        context = {'users':users,
                   'exchange':share.exchange,
                   'symbol':share.symbol,
                   'user':share.user,
                   'goal':share.goal,
                   'notes':share.notes,
                   'etf':share.etf}
        return render(request, template, context)
    return HttpResponseRedirect("../")

def upload_transactions(request):
    template = 'shares/upload_transactions.html'
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    get_challenge = 0
    pull_message = ''
    ca = None
    challenge_read_file = os.path.join(settings.MEDIA_ROOT, 'secrets', 'rh_challenge')
    user_id = None
    if request.method == 'POST':
        print(request.POST)
        if "pull-submit" in request.POST:
            if 'pullBrokerControlSelect' in request.POST:
                broker = request.POST.get('pullBrokerControlSelect')
            else:
                broker = 'ROBINHOOD'
            user_id = request.POST.get('pull-user-id')
            passwd = request.POST.get('pull-passwd')
            pass_2fa = request.POST.get('pull-2fa')
            ct = request.POST.get('challenge-type')
            challenge_type = 'by_sms'
            if ct == 'E-Mail':
                challenge_type = 'by_email'
            if broker == 'ROBINHOOD':
                if os.path.exists(challenge_read_file):
                    with open(challenge_read_file, 'w') as f:
                        ca = request.POST.get('run-time-input')
                        print(f'writing {ca} to {challenge_read_file}')
                        f.write(ca)
                else:
                    user = request.POST['pull-user']
                    print(f'logging in:  {broker}')
                    pull_share_trans_from_rh(user, broker, user_id, passwd, challenge_type, challenge_read_file)
                    attempts=0
                    while attempts < 5:
                        print(f'checking if login was successful {datetime.datetime.now()} file {challenge_read_file} attempt {str(attempts)}')
                        if os.path.exists(challenge_read_file):        
                            break
                        attempts += 1
                        time.sleep(10)
                    if os.path.exists(challenge_read_file):
                        print('login successful')
                        pull_message = 'Login Successful.  Enter challenge answer'
                        get_challenge = 1
                    else:
                        pull_message = 'login failed'
            elif broker == 'ZERODHA':
                user = request.POST['pull-user']
                pull_share_trans_from_broker(user, broker, user_id, passwd, pass_2fa)
            else:
                print('Unsupported broker')
        else:
            uploaded_file = request.FILES['document']
            user = request.POST['user']
            broker = request.POST.get('brokerControlSelect')
            print(uploaded_file)
            print(broker)
            fs = FileSystemStorage()
            file_locn = fs.save(uploaded_file.name, uploaded_file)
            print(file_locn)
            print(settings.MEDIA_ROOT)
            full_file_path = settings.MEDIA_ROOT + '/' + file_locn
            shares_add_transactions(broker, user, full_file_path)
            fs.delete(file_locn)
    users = get_all_users()
    if not get_challenge and not ca:
        if os.path.exists(challenge_read_file):
            os.remove(challenge_read_file)
    context = {'users':users, 'get_challenge':get_challenge, 'pull_message':pull_message}
    if user_id:
        context['user'] = user_id
    return render(request, template, context)

def add_transaction(request):
    template = 'shares/add_transaction.html'
    if request.method == 'POST':
        if "submit" in request.POST:
            exchange = request.POST['exchange']
            symbol = request.POST['symbol']
            user = request.POST['user']
            print('user is of type:',type(user))
            trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
            trans_type = request.POST['trans_type']
            price = get_float_or_none_from_string(request.POST['price'])
            quantity = get_float_or_none_from_string(request.POST['quantity'])
            conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
            trans_price = get_float_or_none_from_string(request.POST['trans_price'])
            broker = request.POST['broker']
            notes = request.POST['notes']
            insert_trans_entry(exchange, symbol, user, trans_type, quantity, price, trans_date, notes, broker, conversion_rate, trans_price)
        else:
            print('fetching exchange price')
            exchange = request.POST['exchange']
            symbol = request.POST['symbol']
            user = request.POST['user']
            trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
            exchange_rate = 1
            if exchange == 'NASDAQ' or exchange == 'NYSE':
                exchange_rate = get_forex_rate(trans_date, 'USD', 'INR')
            users = get_all_users()
            context = {'users':users, 'operation': 'Add Transaction', 'conversion_rate':exchange_rate,
                        'trans_date':trans_date.strftime("%Y-%m-%d"), 'user':user, 'exchange':exchange, 'symbol':symbol}
            return render(request, template, context)

    users = get_all_users()
    context = {'users':users, 'operation': 'Add Transaction', 'conversion_rate':1}
    return render(request, template, context)

def update_transaction(request,id):
    template = 'shares/update_transaction.html'
    trans = Transactions.objects.get(id=id)

    if request.method == 'POST':
        trans.trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
        trans.trans_type = request.POST['trans_type']
        trans.quantity = get_float_or_none_from_string(request.POST['quantity'])
        trans.conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
        trans.price = get_float_or_none_from_string(request.POST['price'])
        trans_price = get_float_or_none_from_string(request.POST['trans_price'])
        if not trans_price:
            trans_price = trans.price*trans.quantity*trans.conversion_rate
        trans.trans_price = trans_price
        trans.broker = request.POST['broker']
        trans.notes = request.POST['notes']
        trans.save()
        reconcile_share(trans.share)
    context = {
        'user':get_user_name_from_id(trans.share.user), 'operation': 'Update Transaction',
        'exchange': trans.share.exchange, 'symbol':trans.share.symbol, 'trans_date':trans.trans_date.strftime("%Y-%m-%d"),
        'price': trans.price, 'quantity':trans.quantity, 'conversion_rate':trans.conversion_rate,
        'trans_price': trans.trans_price, 'broker':trans.broker, 'notes':trans.notes
    }
    return render(request, template, context)


def refresh(request):
    print("inside refresh")
    reconcile_shares()
    update_shares_latest_val()
    check_discrepancies()
    print('done with request')
    return HttpResponseRedirect(reverse('shares:shares-list'))


class CurrentShares(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, user_id=None):
        print("inside CurrentShares")
        shares = dict()
        shares['shares'] = list()
        if user_id:
            share_objs = Share.objects.filter(quantity__gt=0).filter(user=user_id)
        else:
            share_objs = Share.objects.filter(quantity__gt=0)
        for share in share_objs:
            data = dict()
            data['exchange'] = share.exchange
            data['symbol'] = share.symbol
            data['quantity'] = share.quantity
            data['buy_price'] = share.buy_price
            data['buy_value'] = share.buy_value
            data['latest_price'] = share.latest_price
            data['latest_value'] = share.latest_value
            data['gain'] = share.gain
            data['user_id'] = share.user
            data['user'] = get_user_name_from_id(share.user)
            data['notes'] = share.notes
            data['as_on_date'] = share.as_on_date
            shares['shares'].append(data)
        return Response(shares)

def delete_shares(request):
    Share.objects.all().delete()
    return HttpResponseRedirect('../')

def shares_insights(request):
    template = 'shares/investment_insights.html'
    queryset = Share.objects.all()
    data = dict()
    country = dict()
    blend = dict()
    total = 0
    for s in queryset:
        if s.exchange in ['BSE', 'NSE', 'NSE/BSE']:
            country['India'] = add_two(country.get('India', 0), s.latest_value)
        elif s.exchange in ['NASDAQ', 'NYSE']:
            country['USA'] = add_two(country.get('USA', 0), s.latest_value)
        else:
            country['Others'] = add_two(country.get('Others', 0), s.latest_value)
        try:
            stock = Stock.objects.get(symbol=s.symbol,exchange=s.exchange)
            cap = stock.capitalisation if stock.capitalisation and stock.capitalisation != '' else 'Unknown'
            blend[cap] = add_two(blend.get(cap,0),s.latest_value)
        except Stock.DoesNotExist:
            cap = 'Unknown'
            blend[cap] = add_two(blend.get(cap,0),s.latest_value)

        total = add_two(total, s.latest_value)

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
    
    data['country_labels'] = list()
    data['country_vals'] = list()
    data['country_colors'] = list()
    data['country_percents'] = list()
    for k,v in country.items():
        if v:
            data['country_labels'].append(k)
            data['country_vals'].append(float(v))
            import random
            r = lambda: random.randint(0,255)
            data['country_colors'].append('#{:02x}{:02x}{:02x}'.format(r(), r(), r()))
            h = float(v)*100/float(total)
            h = int(round(h))
            data['country_percents'].append(h)
    print('returning:', data)
    return render(request, template, data)


def add_two(first, second):
    if first and second:
        return int(first+second)
    if first:
        return int(first)
    if second:
        return int(second)
    return None
