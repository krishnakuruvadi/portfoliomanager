from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import (
    ListView,
    DetailView
)
from .models import Stock, MutualFund, HistoricalStockPrice, HistoricalMFPrice
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
