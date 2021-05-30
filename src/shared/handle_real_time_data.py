import requests
from dateutil.relativedelta import relativedelta
import datetime
import csv
import codecs
from contextlib import closing
from common.models import HistoricalForexRates, HistoricalStockPrice, MutualFund, HistoricalMFPrice
from .nasdaq import Nasdaq
#from .nse import Nse
from .yahoo_finance_2 import YahooFinance2
from mftool import Mftool
from common.models import Stock
from django.db import IntegrityError
import time


def get_latest_vals(stock, exchange, start, end, etf=False):
    print("inside get_latest_vals exchange ", exchange, "start date:", start, " end date:", end)
    if exchange == 'NASDAQ':
        #response = Nasdaq(stock).get_historical_value(start, end)
        response = Nasdaq(stock, etf).get_latest_val()
        if not response:
            response = Nasdaq(stock, etf).get_historical_value(start, end)
            if not response:
                response = YahooFinance2(stock).get_historical_value(start, end)
        return response
    if exchange == 'NSE' or exchange == 'NSE/BSE':
        #response = Nse(stock).get_historical_value(start, end)
        response = YahooFinance2(stock+'.NS').get_historical_value(start, end)
        return response
    if exchange == 'BSE':
        #response = Nse(stock).get_historical_value(start, end)
        response = YahooFinance2(stock+'.BO').get_historical_value(start, end)
        return response

def get_mf_vals(amfi_code, start, end):
    mf = Mftool()
    response = dict()
    for _ in range(3):
        try:
            vals = mf.get_scheme_historical_nav_year(amfi_code,start.year)
            if vals:
                data = vals['data']
                #print(f' data in get_mf_vals for code {amfi_code} : {data}')
                for entry in data:
                    if 'date' in entry.keys():
                        entry_date = datetime.datetime.strptime(entry['date'], "%d-%m-%Y").date()
                        if entry_date >= start and entry_date <= end:
                            response[entry_date] = float(entry['nav'])
                    if 'Error' in entry.keys():
                        break
                break
        except Exception as ex:
            print(ex)
            pass
    return response

def get_historical_year_mf_vals(amfi_code, year):
    mf = Mftool()
    today = datetime.date.today()
    for _ in range(3):
        try:
            vals = mf.get_scheme_historical_nav_year(amfi_code,year)
            if vals:
                data = vals['data']
                #print(" data in get_mf_vals ", amfi_code, data)
                for entry in data:
                    entry_date = datetime.datetime.strptime(entry['date'], "%d-%m-%Y").date()
                    if entry_date.day in [27,28,29,30,31,1] or (entry_date.year == today.year and abs((today - entry_date).days) <= 5):
                        nav = float(entry['nav'])
                        try:
                            code = MutualFund.objects.get(code=amfi_code)
                            new_entry = HistoricalMFPrice(code=code, date=entry_date, nav=nav)
                            new_entry.save()
                        except IntegrityError:
                            pass
                        except Exception as ex:
                            print("error getting historical mf vals for mutual fund object with code ", amfi_code, ex)
                            pass
                break
        except Exception as ex:
            print("exception in getting historial mf vals for year", year, ex)
            pass

def get_forex_rate(date, from_cur, to_cur):
    for _ in range(5):
        try:
            # https://api.ratesapi.io/api/2020-01-31?base=USD&symbols=INR
            #url = "https://api.ratesapi.io/api/" + date.strftime('%Y-%m-%d') + "?base=" + from_cur + "&symbols=" + to_cur
            url = 'https://api.exchangerate.host/' + date.strftime('%Y-%m-%d') + "?base=" + from_cur + "&symbols=" + to_cur
            response = requests.get(url, timeout=15) 
            # print response 
            print(response) 
            # print json content 
            print(response.json())
            return response.json().get('rates').get(to_cur)
        except Exception as ex:
            print(f'exception while getting forex rate for: date {date}, from_cur {from_cur}, to_cur {to_cur}')
            time.sleep(5)
    return None

def get_conversion_rate(from_cur, to_cur, date):
    try:
        forex_rate = HistoricalForexRates.objects.get(from_cur=from_cur, to_cur=to_cur, date=date)
        return forex_rate.rate
    except HistoricalForexRates.DoesNotExist:
        val = get_forex_rate(date, from_cur, to_cur)
        if val:
            new_entry = HistoricalForexRates(from_cur=from_cur, to_cur=to_cur, date=date, rate=val)
            new_entry.save()
            print(val)
            return val
        else:
            return None

def get_historical_stock_price_based_on_symbol(symbol, exchange, start, end):
    try:
        stock = Stock.objects.get(exchange=exchange, symbol=symbol)
        vals = get_historical_stock_price(stock, start, end)
        if vals:
            return vals[0]
    except Exception as ex:
        print('exception', ex)
        print(f'no historical value for {symbol}/{exchange} between {start} and {end}')
        return None

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
        get_vals = get_latest_vals(stock.symbol, stock.exchange, end+relativedelta(days=-5), datetime.date.today())
        if not get_vals:
            return ret_vals
        for k,v in get_vals.items():
            new_date = k
            if isinstance(new_date, datetime.datetime):
                new_date = new_date.date()
            else:
                print('new_date is already of type date')

            if isinstance(start, datetime.datetime):
                start = start.date()
            else:
                print('start is already of type date')

            if isinstance(end, datetime.datetime):
                end = end.date()
            else:
                print('end is already of type date')
                
            if new_date >= start and new_date<= end:
                new_entry = HistoricalStockPrice(symbol=stock, date=new_date, price=v)
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

def get_historical_mf_nav(amfi_code, start, end, fetch=False):
    #print("getting historical mf nav for code ", amfi_code)
    ret_vals = list()
    start_date = end
    try:
        code = MutualFund.objects.get(code=amfi_code)
        while(start_date>start):
            try:
                hmfp = HistoricalMFPrice.objects.get(code=code, date=start_date)
                ret_vals.append({hmfp.date:hmfp.nav})
            except HistoricalMFPrice.DoesNotExist:
                pass
            start_date = start_date+relativedelta(days=-1)
        if len(ret_vals) == 0 and fetch:
            poll_date = end+relativedelta(days=-5)
            get_historical_year_mf_vals(amfi_code=amfi_code, year=poll_date.year)
            
            start_date = end
            while(start_date>start):
                try:
                    hmfp = HistoricalMFPrice.objects.get(code=code, date=start_date)
                    ret_vals.append({hmfp.date:hmfp.nav})
                except HistoricalMFPrice.DoesNotExist:
                    pass
                start_date = start_date+relativedelta(days=-1)
    except MutualFund.DoesNotExist:
        print('couldnt find mutual fund with amfi code ', amfi_code)
    #print("returning mf vals ", ret_vals)
    return ret_vals

def get_historical_nearest_mf_nav(amfi_code, rdate):
    vals = get_historical_mf_nav(amfi_code, rdate+relativedelta(days=-6), rdate, True)
    if len(vals) > 0:
        for _,v in vals[0].items():
            return float(v)
    return None