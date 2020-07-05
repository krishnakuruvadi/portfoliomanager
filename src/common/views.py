from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import (
    ListView,
    DetailView
)
from .models import Stock, MutualFund, HistoricalStockPrice, HistoricalMFPrice
from shared.handle_real_time_data import get_latest_vals, get_historical_mf_nav
from dateutil.relativedelta import relativedelta
import datetime
from mftool import Mftool
from django.db import IntegrityError

def common_list_view(request):
    template = 'common/common_list.html'
    context = dict()
    stock_list = list()
    mf_list = list()
    stock_objs = Stock.objects.all()
    for stock in stock_objs:
        stock_entry = dict()
        stock_entry['id'] = stock.id
        stock_entry['exchange'] = stock.exchange
        stock_entry['symbol'] = stock.symbol
        stock_entry['collection_start_date'] = stock.collection_start_date
        stock_list.append(stock_entry)
    mf_objs = MutualFund.objects.all()
    for mf in mf_objs:
        mf_entry = dict()
        mf_entry['id'] = mf.id
        mf_entry['code'] = mf.code
        mf_entry['name'] = mf.name
        mf_entry['collection_start_date'] = mf.collection_start_date
        mf_list.append(mf_entry)
    context['mf_objs'] = mf_list
    context['stock_list'] = stock_list
    print(context)
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
            entry = HistoricalStockPrice(symbol=stock, date=k, price=v)
            entry.save()
        print(vals)
    return HttpResponseRedirect(reverse('common:common-list'))

def mf_refresh(request):
    print("inside mf_refresh")
    mf = Mftool()
    mf_schemes = get_scheme_codes(mf, False)
    print(mf_schemes)
    for code, details in mf_schemes.items():
        isin2 = None
        if details['isin2'] and details['isin2'] != '' and details['isin2'] != '-':
            isin2 = details['isin2']
        mf_obj = None
        try:
            mf_obj = MutualFund.objects.get(code=code)
        except MutualFund.DoesNotExist:
            mf_obj = MutualFund.objects.create(code=code,
                                               name=details['name'],
                                               isin=details['isin1'],
                                               isin2=isin2,
                                               collection_start_date=datetime.date.today())

        mf_obj.isin = details['isin1']
        mf_obj.isin2 = isin2
        mf_obj.name = details['name']
        mf_obj.save()
        try:
            HistoricalMFPrice.objects.create(code=mf_obj,
                                             date=datetime.datetime.strptime(details['date'],'%d-%b-%Y').date(),
                                             nav=float(details['nav']))
        except Exception as ex:
            print(ex)
    '''
    mf_objs = MutualFund.objects.all()
    for mf in mf_objs:
        collection_start_date = datetime.date.today()+relativedelta(days=-5)       
        _ = get_historical_mf_nav(mf.code, collection_start_date, datetime.date.today())
    '''

    return HttpResponseRedirect(reverse('common:mf-list'))

def get_scheme_codes(mf, as_json=False):
    """
    returns a dictionary with key as scheme code and value as scheme name.
    cache handled internally
    :return: dict / json
    """
    scheme_info = {}
    url = mf._get_quote_url
    response = mf._session.get(url)
    data = response.text.split("\n")
    for scheme_data in data:
        if ";INF" in scheme_data:
            scheme = scheme_data.rstrip().split(";")
            #print(scheme[1],', ',scheme[2])
            scheme_info[scheme[0]] = {'isin1': scheme[1],
                                      'isin2':scheme[2],
                                      'name':scheme[3],
                                      'nav':scheme[4],
                                      'date':scheme[5]}

    return mf.render_response(scheme_info, as_json)

class HistoricalStockPriceList(ListView):
    template_name = 'common/historical_stock_price_list.html'

    paginate_by = 15
    model = HistoricalStockPrice

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

class MFListView(ListView):
    template_name = 'common/mf_list.html'

    paginate_by = 15
    model = MutualFund

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