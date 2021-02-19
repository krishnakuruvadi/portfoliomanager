from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import (
    ListView,
    DetailView
)
from .models import Stock, MutualFund, HistoricalStockPrice, HistoricalMFPrice, ScrollData, Preferences
from .helper import update_mf_scheme_codes
from shared.handle_real_time_data import get_latest_vals, get_historical_mf_nav
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
from common.helper import get_preferences
from pytz import common_timezones
from shared.nasdaq import Nasdaq
from nsetools import Nse


def common_list_view(request):
    template = 'common/common_list.html'
    return render(request, template)

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
            entry = HistoricalStockPrice(symbol=stock, date=k, price=v)
            entry.save()
        print(vals)
    return HttpResponseRedirect(reverse('common:common-list'))

def mf_refresh(request):
    update_mf_scheme_codes()
    return HttpResponseRedirect(reverse('common:mf-list'))

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
        return HistoricalMFPrice.objects.filter(code__id=self.kwargs['id'])

class StockListView(ListView):
    template_name = 'common/stock_list.html'

    paginate_by = 15
    model = Stock

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
        print(data)
        return data

class MfDetailView(DetailView):
    template_name = 'common/mf_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(MutualFund, id=id_)
    
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
    mfs = list()
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
    #s = json.dumps(mfs)
    return JsonResponse(mfs, safe=False)

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
        pref_obj.document_backup_locn = request.POST.get('timezone')
        pref_obj.save()
 
    tzs = list()
    for i_tz in common_timezones:
        tzs.append(i_tz)
    avail_indexes = list()
    n = Nasdaq('')
    index_data = n.get_all_index()
    for _,v in index_data.items():
        avail_indexes.append(v['name'])
    
    nse = Nse()
    for item in nse.get_index_list():
        avail_indexes.append(item)
    
    sel_indexes = list()
    if pref_obj.indexes_to_scroll:
        for index in pref_obj.indexes_to_scroll.split('|'):
            sel_indexes.append(index)
    else:
        for index in avail_indexes:
            sel_indexes.append(index)

    context = {
        'tz': pref_obj.timezone, 
        'tzs':tzs, 'indexes':avail_indexes, 
        'sel_indexes':sel_indexes, 
        'document_backup_locn':'' if not pref_obj.document_backup_locn else pref_obj.document_backup_locn
    }
    return render(request, template, context)