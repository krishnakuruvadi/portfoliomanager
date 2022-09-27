from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView
)
from .models import Stock, MutualFund, HistoricalStockPrice, HistoricalMFPrice, ScrollData, Preferences, Passwords, HistoricalIndexPoints, Index
from .helper import *
from shared.handle_real_time_data import get_latest_vals, get_historical_mf_nav, get_conversion_rate
from dateutil.relativedelta import relativedelta
import datetime
from mftool import Mftool
from django.db import IntegrityError
from django.core.files.storage import FileSystemStorage
from .bsestar import BSEStar
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
import json
from dateutil import tz
from pytz import timezone
from common.helper import get_preferences, get_current_app_version
from pytz import common_timezones
from shared.nasdaq import Nasdaq
from common.nse import NSE
from shared.utils import *
from .bsestar import update_bsestar_schemes
from shared.handle_get import *
import os
import shutil
import requests
import semver

def common_list_view(request):
    context = dict()
    template = 'common/common_list.html'
    context['current_app_version'] = get_current_app_version()
    context['curr_module_id'] = 'id_internals_module'
    return render(request, template, context)

def check_app_updates(request):
    template = 'common/check_app_updates.html'
    context = dict()
    current_version = get_current_app_version()
    url = 'https://raw.githubusercontent.com/krishnakuruvadi/portfoliomanager/main/src/metadata.json'

    try:
        request = requests.get(url, timeout=15)
        request.raise_for_status()
        data = request.json()
        try:
            new_version = data['release_version']
                
        except KeyError:
            new_version = 'Unable to retrieve metadata key'
        
    except requests.exceptions.Timeout:
        new_version = 'Connection has timed out'
    except requests.exceptions.HTTPError:
        new_version = 'An HTTP error has occurred'
    except requests.exceptions.ConnectionError:
        new_version = 'Connection error'
    except requests.exceptions.RequestException:
        new_version = 'An error has occurred'

    try:
        ver_comparison = semver.compare(current_version, new_version)
        
    except Exception:
        ver_comparison = 'Unable to check for updates'
    
    context['new_app_version'] = new_version
    context['current_app_version'] = current_version
    context['compared_versions'] = ver_comparison

    return render(request, template, context)

def refresh(request):
    print("inside refresh")
    stock_objs = Stock.objects.all()
    for stock in stock_objs:
        collection_start_date = stock.collection_start_date
        historical_entries = HistoricalStockPrice.objects.filter(id=stock.id)
        # TODO: optimize
        for entry in historical_entries:
            if entry.date>collection_start_date:
                collection_start_date = entry.date
        vals = get_latest_vals(stock.symbol, stock.exchange, collection_start_date, datetime.date.today())
        for k,v in vals.items():
            try:
                entry = HistoricalStockPrice.objects.create(symbol=stock, date=k, price=v)
                entry.save()
            except IntegrityError as ex:
                print(f'entry exists {stock.symbol} {stock.exchange} {k} {ex}')

        print(vals)
    return HttpResponseRedirect(reverse('common:common-list'))

def mf_refresh(request):
    update_mf_scheme_codes()
    return HttpResponseRedirect(reverse('common:mf-list'))

class HistoricalIndexPointList(ListView):
    template_name = 'common/historical_index_point_list.html'

    paginate_by = 15
    model = HistoricalIndexPoints
    def get_queryset(self):
        return HistoricalIndexPoints.objects.filter(index__id=self.kwargs['id'])

class HistoricalStockPriceList(ListView):
    template_name = 'common/historical_stock_price_list.html'

    paginate_by = 15
    model = HistoricalStockPrice
    def get_queryset(self):
        return HistoricalStockPrice.objects.filter(symbol__id=self.kwargs['id'])

class HistoricalMFPriceList(ListView):
    template_name = 'common/historical_mf_price_list.html'

    paginate_by = 15
    model = HistoricalMFPrice

    def get_queryset(self):
        return HistoricalMFPrice.objects.filter(code__id=self.kwargs['id']).order_by("-date")
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['curr_module_id'] = 'id_internals_module'
        return data

class IndexListView(ListView):
    template_name = 'common/index_list.html'
    model = Index

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['curr_module_id'] = 'id_internals_module'
        return data

class IndexDetailView(DetailView):
    template_name = 'common/index_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Index, id=id_)

class StockListView(ListView):
    template_name = 'common/stock_list.html'
    model = Stock

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['curr_module_id'] = 'id_internals_module'
        return data

class StockDetailView(DetailView):
    template_name = 'common/stock_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Stock, id=id_)

class MFListView(ListView):
    template_name = 'common/mf_list.html'
    queryset = MutualFund.objects.all()
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['curr_module_id'] = 'id_internals_module'
        print(data)
        return data

class MfDetailView(DetailView):
    template_name = 'common/mf_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(MutualFund, id=id_)

def update_password(request, id):
    template = 'common/update_password.html'
    password = Passwords.objects.get(id=int(id))

    if request.method == 'POST':
        passwd = request.POST.get('passwd')
        additional_passwd = request.POST.get('additional_passwd')
        input_additional_field = request.POST.get('input_additional_field')
        notes = request.POST.get('notes')
        add_or_edit_password(password.user, password.source, password.user_id, passwd, additional_passwd, input_additional_field, notes)
        return HttpResponseRedirect(reverse('common:passwords-list'))
    context = {'user': password.user, 'source':password.source, 'user_id':password.user_id, 'notes':password.notes, 'input_additional_field':password.additional_input}
    return render(request, template, context)

def password_add_view(request):
    err = None
    mp = get_master_password()
    template = 'common/add_master_password.html'
    if mp:
        template = 'common/add_password.html'
    if request.method == 'POST':
        if mp:
            user = request.POST.get('user')
            source = request.POST.get('pullSourceControlSelect')
            user_id = request.POST.get('user_id')
            passwd = request.POST.get('passwd')
            additional_passwd = request.POST.get('additional_passwd')
            input_additional_field = request.POST.get('input_additional_field')
            notes = request.POST.get('notes')
            print(f'{user}, {source}, {user_id}, {passwd}, {additional_passwd}, {input_additional_field}')
            #token, token2, salt = encrypt_password(passwd, additional_passwd)
            #print(f'{token}, {token2}, {salt}')
            add_or_edit_password(user, source, user_id, passwd, additional_passwd, input_additional_field, notes)

        else:
            passwd = request.POST.get('passwd')
            reenter_passwd = request.POST.get('re_enter_passwd')
            if passwd == reenter_passwd:
                add_master_password(passwd)
            else:
                err = "ERROR: Passwords dont match"
                print(err)
    context = dict()
    context['error'] = err
    mp = get_master_password()
    template = 'common/add_master_password.html'
    if mp:
        users = get_all_users()
        context['users'] = users
        template = 'common/add_password.html'

    return render(request, template, context)


def password_detail_view(request):
    template = 'common/password_detail.html'
    password_obj = Passwords.objects.get(id=request.GET.get('id'))
    p = dict()
    p['user'] = password_obj.user
    p['source'] = password_obj.source
    p['user_id'] = password_obj.user_id
    return render(request, template, p)

def password_list_view(request):
    template = 'common/password_list.html'
    password_objs = Passwords.objects.all()
    context = dict()
    passwords = list()
    for password_obj in password_objs:
        p = dict()
        p['id'] = password_obj.id
        p['user'] = password_obj.user
        p['source'] = password_obj.source
        p['user_id'] = password_obj.user_id
        p['last_updated'] = password_obj.last_updated
        passwords.append(p)
    context['passwords'] = passwords
    context['user_name_mapping'] = get_all_users()
    return render(request, template, context)

def password_trash(request):
    template = 'common/password_trash.html'
    print('inside password_trash request.method',request.method)
    if request.method == 'POST':
        Passwords.objects.all().delete()
        secrets_path = get_secrets_path()
        if os.path.exists(secrets_path):
            try:
                shutil.rmtree(secrets_path)
            except OSError as e:
                print("Error: %s : %s" % (secrets_path, e.strerror))
        return HttpResponseRedirect(reverse('common:passwords-list'))
    return render(request, template)

class PasswordDeleteView(DeleteView):
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Passwords, id=id_)

    def get_success_url(self):
        return reverse('common:passwords-list')
    
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

def mf_trash(request):
    template = 'common/mf_trash.html'
    print('inside mf_trash request.method',request.method)
    if request.method == 'POST':
        MutualFund.objects.all().delete()
        return HttpResponseRedirect(reverse('common:mf-list'))
    return render(request, template)

def mf_bse_star(request):
    template = 'common/upload_bsestar.html'
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        print(uploaded_file)
        fs = FileSystemStorage()
        file_locn = fs.save(uploaded_file.name, uploaded_file)
        print(file_locn)
        print(settings.MEDIA_ROOT)
        full_file_path = settings.MEDIA_ROOT + '/' + file_locn
        bse_star = BSEStar()
        schemes = bse_star.get_all_schemes(full_file_path)
        fs.delete(file_locn)
        update_bsestar_schemes(schemes)
        return HttpResponseRedirect(reverse('common:mf-list'))
    return render(request, template)

@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_mutual_funds(request):
    print('inside get_mutual_funds')
    filte = request.GET.get('q', '')
    fund_house = request.GET.get('fund_house', '')
    print(f' {filte} {fund_house}')
    mfs = list()
    '''
    try:
        i = 0
        for mfo in MutualFund.objects.filter(name__contains=filte):
            data = dict()
            data['value'] = mfo.code
            data['label'] = mfo.name
            mfs.append(data)
            i = i +1
            if i > 10:
                break
    except Exception as ex:
        print('exception in AvailableMutualFunds', ex)
    '''
    mf = Mftool()
    sc = get_scheme_codes(mf)
    print(f'Total number of schemes: {len(sc)}')
    i = 0
    for code, details in sc.items():
        if details['fund_house'] == fund_house:
            if filte.lower() in details['name'].lower():
                data = dict()
                data['value'] = code
                data['label'] = details['name']
                mfs.append(data)
                i  += 1
                if i > 10:
                    break
            #else:
            #    print(f"ignoring {details['name']}")
    #s = json.dumps(mfs)
    print(f'returning {len(mfs)} matching items')

    return JsonResponse(mfs, safe=False)

class UserPreferenceInvestmentTypesView(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None):
        its = get_preferences('investment_types')
        sel_investment_types = list()
        if its:
            for inv in its.split('|'):
                sel_investment_types.append(inv)
        print(f'{its}')
        data = dict()
        data['sel_investment_types'] = list()
        mapping = {
            'Fixed Deposits':'id_fd_module',
            'PPF':'id_ppf_module',
            'SSY':'id_ssy_module',
            'EPF':'id_epf_module',
            'ESPP':'id_espp_module',
            'Insurance':'id_insurance_module',
            'RSU':'id_rsu_module',
            '401K':'id_401k_module',
            'Shares':'id_shares_module',
            'Mutual Funds':'id_mf_module',
            'Gold':'id_gold_module',
            'Cash':'id_bank_acc_module',
            'Crypto':'id_crypto_module'
        }
        if len(sel_investment_types) > 0:
            for m, module in mapping.items():
                if m in sel_investment_types:
                    data['sel_investment_types'].append(module)
        else:
            for m, module in mapping.items():
                data['sel_investment_types'].append(module)
        print(f'returning {data}')
        return Response(data)

class ScrollDataView(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None):
        data = dict()
        data['scroll_data'] = list()
        scroll_objs = ScrollData.objects.all()
        for scroll_obj in scroll_objs:
            if scroll_obj.display:
                obj = dict()
                obj['scrip'] = scroll_obj.scrip
                obj['val'] = scroll_obj.val
                obj['change'] = scroll_obj.change
                obj['percent'] = scroll_obj.percent
                utc = scroll_obj.last_updated
                from_zone = tz.tzutc()
                utc = utc.replace(tzinfo=from_zone)
                preferred_tz = get_preferences('timezone')
                if not preferred_tz:
                    preferred_tz = 'Asia/Kolkata'
                obj['last_updated'] = utc.astimezone(timezone(preferred_tz)).strftime("%Y-%m-%d %H:%M:%S")
                data['scroll_data'].append(obj)
        return Response(data)

class ForexDataView(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, year, month, day, from_currency, to_currency, format=None):
        data = dict()
        date = datetime.date(year=year, month=month, day=day)
        ret = get_conversion_rate(from_currency, to_currency, date)
        print(ret)
        data[convert_date_to_string(date)] = ret
        return Response(data)

def preferences(request):
    template = 'common/preferences.html'
    pref_obj = Preferences.get_solo()

    if request.method == 'POST':
        print(request.POST)
        tz_pref = request.POST.get('timezone')
        if tz_pref and tz_pref != '':
            if isinstance(tz_pref, list): 
                pref_obj.timezone = tz_pref[0]
            else:
                pref_obj.timezone = tz_pref
        sel_indexes = request.POST.getlist('index_scroll')
        if sel_indexes:
            sel_index_str = None
            for sel_index in sel_indexes:
                if not sel_index_str:
                    sel_index_str = sel_index
                else:
                    sel_index_str = sel_index_str + '|' + sel_index
            if sel_index_str:
                print(f'sel_index_str {sel_index_str}')
                pref_obj.indexes_to_scroll = sel_index_str

        sel_investment_types = request.POST.getlist('investment_types')
        if sel_investment_types:
            sel_inv_str = None
            for sel_inv in sel_investment_types:
                if not sel_inv_str:
                    sel_inv_str = sel_inv
                else:
                    sel_inv_str = sel_inv_str + '|' + sel_inv
            if sel_inv_str:
                print(f'sel_inv_str {sel_inv_str}')
                pref_obj.investment_types = sel_inv_str

        pref_obj.document_backup_locn = request.POST.get('doc_backup')
        pref_obj.show_zero_value_mfs = 'show_zero_val_mfs' in request.POST
        pref_obj.show_zero_value_shares = 'show_zero_val_shares' in request.POST
        curr = request.POST.get('currency')
        if curr:
            pref_obj.currency = curr.upper()
        email_backend = request.POST['email_backend']
        if email_backend != '' and email_backend.replace('-', '') != '':
            pref_obj.email_backend = email_backend
            pref_obj.email_api_key = request.POST['email_api_key']
            pref_obj.email_api_secret = request.POST['email_api_secret']
            pref_obj.sender_email = request.POST['sender_email']
        else:
            pref_obj.email_backend = ''
            pref_obj.email_api_key = ''
            pref_obj.email_api_secret = ''
            pref_obj.sender_email = ''
        pref_obj.save()
 
    tzs = list()
    for i_tz in common_timezones:
        tzs.append(i_tz)
    avail_investment_types = ['Fixed Deposits', 'PPF', 'SSY', 'EPF', 'ESPP', 'Insurance', 'RSU', '401K', 'Shares', 'Mutual Funds', 'Gold', 'Cash', 'Crypto']
    avail_indexes = list()
    n = Nasdaq('', None)
    index_data = n.get_all_index()
    if not index_data:
        avail_indexes.append('NASDAQ Composite')
    else:
        for _,v in index_data.items():
            avail_indexes.append(v['name'])
    
    nse = NSE(None)
    il = nse.get_index_list()
    if il:
        for item in il:
            avail_indexes.append(item)
    else:
        index_data = {'NIFTY 50':'^NSEI', 'NIFTY BANK':'^NSEBANK', 'INDIA VIX':'^INDIAVIX', 'NIFTY 100':'^CNX100',
                    'NIFTY 500':'^CRSLDX', 'NIFTY MIDCAP 100':'NIFTY_MIDCAP_100.NS', 'NIFTY PHARMA':'^CNXPHARMA',
                    'NIFTY IT':'^CNXIT', 'NIFTY SMLCAP 100':'^CNXSC', 'NIFTY 200':'^CNX200', 'NIFTY AUTO':'^CNXAUTO'}
        for k,_ in index_data.items():
            avail_indexes.append(k)
    
    sel_indexes = list()
    if pref_obj.indexes_to_scroll:
        for index in pref_obj.indexes_to_scroll.split('|'):
            sel_indexes.append(index)
    else:
        for index in avail_indexes:
            sel_indexes.append(index)

    sel_investment_types = list()
    if pref_obj.investment_types:
        for inv in pref_obj.investment_types.split('|'):
            sel_investment_types.append(inv)
    else:
        for inv in avail_investment_types:
            sel_investment_types.append(inv)

    context = {
        'tz': pref_obj.timezone,
        'tzs':tzs,
        'indexes':avail_indexes, 
        'sel_indexes':sel_indexes,
        'investment_types': avail_investment_types,
        'sel_investment_types': sel_investment_types, 
        'document_backup_locn':'' if not pref_obj.document_backup_locn else pref_obj.document_backup_locn,
        'show_zero_val_mfs': pref_obj.show_zero_value_mfs,
        'show_zero_val_shares': pref_obj.show_zero_value_shares,
        'currency': pref_obj.currency,
        'email_backend': pref_obj.email_backend,
        'sender_email': pref_obj.sender_email,
        'email_api_key': pref_obj.email_api_key,
        'email_api_secret': pref_obj.email_api_secret,
    }
    return render(request, template, context)
