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
from shared.utils import *
from shared.handle_get import *
from shared.handle_real_time_data import get_latest_vals, get_forex_rate
from .zerodha import Zerodha
from django.db import IntegrityError
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
        add_transactions(broker, user, full_file_path)
        fs.delete(file_locn)
    users = get_all_users()
    context = {'users':users}
    return render(request, template, context)

def add_transaction(request):
    template = 'shares/add_transaction.html'
    if request.method == 'POST':
        exchange = request.POST['exchange']
        symbol = request.POST['symbol']
        user = request.POST['user']
        print('user is of type:',type(user))
        trans_date = get_date_or_none_from_string(request.POST['trans_date'])
        trans_type = request.POST['trans_type']
        price = get_float_or_none_from_string(request.POST['price'])
        quantity = get_int_or_none_from_string(request.POST['quantity'])
        conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
        trans_price = get_float_or_none_from_string(request.POST['trans_price'])
        broker = request.POST['broker']
        notes = request.POST['notes']
        insert_trans_entry(exchange, symbol, user, trans_type, quantity, price, date, notes, broker, conversion_rate, trans_price)
    users = get_all_users()
    context = {'users':users, 'operation': 'Add Transaction'}
    return render(request, template, context)

def add_transactions(broker, user, full_file_path):
    if broker == 'ZERODHA':
        zerodha_helper = Zerodha(full_file_path)
        for trans in zerodha_helper.get_transactions():
            print("trans is", trans)
            insert_trans_entry(
                trans["exchange"], trans["symbol"], user, trans["type"], trans["quantity"], trans["price"], trans["date"], trans["notes"], 'ZERODHA')


def insert_trans_entry(exchange, symbol, user, trans_type, quantity, price, date, notes, broker, conversion_rate=1, trans_price=None):
    share_obj = None
    try:
        share_obj = Share.objects.get(exchange=exchange, symbol=symbol)
    except Share.DoesNotExist:
        print("Couldnt find share object exchange:", exchange, " symbol:", symbol)
        share_obj = Share.objects.create(exchange=exchange,
                                             symbol=symbol,
                                             user=user,
                                             quantity=0,
                                             buy_price=0,
                                             buy_value=0,
                                             gain=0)
    if not trans_price:
        trans_price = price*quantity*conversion_rate
    try:
        Transactions.objects.create(share=share_obj,
                                    trans_date=date,
                                    trans_type=trans_type,
                                    price=price,
                                    quantity=quantity,
                                    conversion_rate=conversion_rate,
                                    trans_price=trans_price,
                                    broker=broker,
                                    notes=notes)
        if trans_type == 'Buy':
            new_qty = int(share_obj.quantity)+quantity
            new_buy_value = float(share_obj.buy_value) + trans_price
            share_obj.quantity = new_qty
            share_obj.buy_value = new_buy_value
            share_obj.buy_price = new_buy_value/float(new_qty)
            share_obj.save()
        else:
            new_qty = share_obj.quantity-quantity
            if new_qty:
                new_buy_value = share_obj.buy_value - trans_price
                share_obj.quantity = new_qty
                share_obj.buy_value = new_buy_value
                share_obj.buy_price = new_buy_value/float(new_qty)
                share_obj.save()
            else:
                share_obj.delete()
    except IntegrityError:
        print('Transaction exists')

def refresh(request):
    print("inside refresh")
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()
    share_objs = Share.objects.all()
    for share_obj in share_objs:
        if share_obj.as_on_date != datetime.date.today():
            vals = get_latest_vals(share_obj.symbol, share_obj.exchange, start, end)
            if vals:
                for k, v in vals.items():
                    if k and v:
                        if not share_obj.as_on_date or k > share_obj.as_on_date:
                            share_obj.as_on_date = k
                            share_obj.latest_price = v
                            if share_obj.exchange == 'NASDAQ':
                                share_obj.conversion_rate = get_forex_rate(k, 'USD', 'INR')
                            else:
                                share_obj.conversion_rate = 1
                            share_obj.latest_value = float(share_obj.latest_price) * float(share_obj.conversion_rate) * float(share_obj.quantity)
                            share_obj.save()
        if share_obj.latest_value: 
            share_obj.gain=share_obj.latest_value-share_obj.buy_value
            share_obj.save()
    print('done with request')
    return HttpResponseRedirect(reverse('shares:shares-list'))
