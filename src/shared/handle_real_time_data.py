import requests
from dateutil.relativedelta import relativedelta
import datetime
import csv
import codecs
from contextlib import closing
from common.models import HistoricalForexRates, HistoricalStockPrice
from .nasdaq import Nasdaq
from .nse import Nse
from .yahoo_finance_2 import YahooFinance2


def get_latest_vals(stock, exchange, start, end):
    print("inside get_latest_vals exchange ", exchange, "start date:", start, " end date:", end)
    if exchange == 'NASDAQ':
        response = Nasdaq(stock).get_historical_value(start, end)
        return response
    if exchange == 'NSE':
        #response = Nse(stock).get_historical_value(start, end)
        response = YahooFinance2(stock+'.NS').get_historical_value(start, end)
        return response

def get_forex_rate(date, from_cur, to_cur):
    # https://api.ratesapi.io/api/2020-01-31?base=USD&symbols=INR
    url = "https://api.ratesapi.io/api/" + date.strftime('%Y-%m-%d') + "?base=" + from_cur + "&symbols=" + to_cur
    response = requests.get(url) 
    # print response 
    print(response) 
    # print json content 
    print(response.json())
    return response.json().get('rates').get(to_cur)

def get_conversion_rate(from_cur, to_cur, date):
    try:
        forex_rate = HistoricalForexRates.objects.get(from_cur=from_cur, to_cur=to_cur, date=date)
        return forex_rate.rate
    except HistoricalForexRates.DoesNotExist:
        val = get_forex_rate(date, from_cur, to_cur)
        new_entry = HistoricalForexRates(from_cur=from_cur, to_cur=to_cur, date=date, rate=val)
        new_entry.save()
        print(val)
        return val

def get_historical_stock_price(stock, start, end):
    ret_vals = list()
    start_date = end
    while(start_date>start):
        try:
            hsp = HistoricalStockPrice.objects.get(symbol=stock, date=start_date)
            ret_vals.append({hsp.date:hsp.price})
        except HistoricalStockPrice.DoesNotExist:
            pass
        start_date = start_date+relativedelta(days=-1)
    if len(ret_vals) == 0:
        get_vals = get_latest_vals(stock.symbol, stock.exchange, end+relativedelta(months=-1), end)
        for k,v in get_vals.items():
            if k >= start and k<= end:
                new_entry = HistoricalStockPrice(symbol=stock, date=k, price=v)
                new_entry.save()
        start_date = end
        while(start_date>start):
            try:
                hsp = HistoricalStockPrice.objects.get(symbol=stock, date=start_date)
                ret_vals.append({hsp.date:hsp.price})
            except HistoricalStockPrice.DoesNotExist:
                pass
            start_date = start_date+relativedelta(days=-1)
    
    return ret_vals
