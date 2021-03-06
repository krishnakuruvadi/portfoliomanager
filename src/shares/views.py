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
from .shares_helper import insert_trans_entry, shares_add_transactions, reconcile_share, update_shares_latest_val
from shared.utils import *
from shared.handle_get import *
from shared.handle_real_time_data import get_latest_vals, get_forex_rate
from .zerodha import Zerodha
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from tasks.tasks import pull_share_trans_from_broker
# Create your views here.

class TransactionsListView(ListView):
    template_name = 'shares/transactions_list.html'
    queryset = Transactions.objects.all()

class SharesListView(ListView):
    template_name = 'shares/shares_list.html'
    queryset = Share.objects.all()
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        total_investment = 0
        latest_value = 0
        as_on_date= None
        total_gain = 0
        share_objs = Share.objects.all()
        for share_obj in share_objs:
            if not share_obj.latest_value:
                continue
            if not as_on_date:
                as_on_date = share_obj.as_on_date
            else:
                if as_on_date < share_obj.as_on_date:
                    as_on_date = share_obj.as_on_date
            latest_value += share_obj.latest_value
            total_investment += share_obj.buy_value
            total_gain += share_obj.gain
        data['as_on_date'] = as_on_date
        data['total_gain'] = total_gain
        data['total_investment'] = total_investment
        data['latest_value'] = latest_value
        return data

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
        share.save()
        
    else:
        
        users = get_all_users()
        context = {'users':users,
                   'exchange':share.exchange,
                   'symbol':share.symbol,
                   'user':share.user,
                   'goal':share.goal,
                   'notes':share.notes}
        return render(request, template, context)
    return HttpResponseRedirect("../")

def upload_transactions(request):
    template = 'shares/upload_transactions.html'
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    if request.method == 'POST':
        print(request.POST)
        if "pull-submit" in request.POST:
            user = request.POST['pull-user']
            broker = request.POST.get('pullBrokerControlSelect')
            user_id = request.POST.get('pull-user-id')
            passwd = request.POST.get('pull-passwd')
            pass_2fa = request.POST.get('pull-2fa')
            pull_share_trans_from_broker(user, broker, user_id, passwd, pass_2fa)
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
    context = {'users':users}
    return render(request, template, context)

def add_transaction(request):
    template = 'shares/add_transaction.html'
    if request.method == 'POST':
        if "submit" in request.POST:
            exchange = request.POST['exchange']
            symbol = request.POST['symbol']
            user = request.POST['user']
            print('user is of type:',type(user))
            trans_date = get_date_or_none_from_string(request.POST['trans_date'])
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
            trans_date = get_date_or_none_from_string(request.POST['trans_date'])
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
        trans.trans_date = get_date_or_none_from_string(request.POST['trans_date'])
        trans.trans_type = request.POST['trans_type']
        trans.quantity = get_float_or_none_from_string(request.POST['quantity'])
        trans.conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
        trans_price = get_float_or_none_from_string(request.POST['trans_price'])
        trans.price = trans_price
        if not trans_price:
            trans_price = trans.trans_price*trans.quantity*trans.conversion_rate
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
    update_shares_latest_val()
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