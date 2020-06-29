from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView
from .models import Stock, MutualFund, HistoricalStockPrice, HistoricalMFPrice
from shared.handle_real_time_data import get_latest_vals
import datetime

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


class HistoricalStockPriceList(ListView):
    template_name = 'common/historical_stock_price_list.html'

    paginate_by = 15
    model = HistoricalStockPrice