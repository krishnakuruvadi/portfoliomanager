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
from .models import Folio, MutualFundTransaction
from common.models import MutualFund
from .kuvera import Kuvera
from rest_framework.views import APIView
from rest_framework.response import Response
from .mf_helper import add_transactions, insert_trans_entry
from tasks.tasks import add_mf_transactions

# Create your views here.

class FolioListView(ListView):
    template_name = 'mutualfunds/folio_list.html'
    queryset = Folio.objects.all()
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        return data

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
            folio_obj = Folio.objects.create(folio=folio,
                                            fund=mf_obj,
                                            user=user,
                                            goal=goal_id)
    users = get_all_users()
    context = {'users':users, 'operation': 'Add Folio'}
    return render(request, template, context)

def add_transaction(request, id):
    template = 'mutualfunds/add_transaction.html'
    folio = Folio.objects.get(id=id)
    user = get_user_name_from_id(folio.user)
    if request.method == 'POST':
        trans_date = get_date_or_none_from_string(request.POST['trans_date'])
        trans_type = request.POST['trans_type']
        price = get_float_or_none_from_string(request.POST['price'])
        units = get_float_or_none_from_string(request.POST['units'])
        conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
        trans_price = get_float_or_none_from_string(request.POST['trans_price'])
        broker = request.POST['broker']
        notes = request.POST['notes']
        insert_trans_entry(folio.folio, folio.fund.code, folio.user, trans_type, units, price, trans_date, notes, broker, conversion_rate, trans_price)
    users = get_all_users()
    context = {'users':users, 'operation': 'Add Transaction', 'folio':folio.folio, 'user':user, 'fund_name':folio.fund.name}
    return render(request, template, context)

def update_transaction(request, id):
    template = 'mutualfunds/update_transaction.html'
    transaction = MutualFundTransaction.objects.get(id=id)
    if request.method == 'POST':
        #folio = request.POST['folio']
        #fund = request.POST['fund']
        #user = request.POST['user']
        #print('user is of type:',type(user))
        transaction.trans_date = get_date_or_none_from_string(request.POST['trans_date'])
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
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        return data

class FolioDeleteView(DeleteView):
    template_name = 'mutualfunds/folio_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Folio, id=id_)

    def get_success_url(self):
        return reverse('mutualfund:folio-list')

class FolioTransactionsListView(ListView):
    template_name = 'mutualfunds/transactions_list.html'

    paginate_by = 15
    model = MutualFundTransaction
    def get_queryset(self):
        #folio = get_object_or_404(Folio, id=self.kwargs['id'])
        return MutualFundTransaction.objects.filter(folio__id=self.kwargs['id'])


class TransactionsListView(ListView):
    template_name = 'mutualfunds/transactions_list.html'
    paginate_by = 15
    model = MutualFundTransaction

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
        add_mf_transactions(broker, user, full_file_path)
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
                   'notes':folio.notes}
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
