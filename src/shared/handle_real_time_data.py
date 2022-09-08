import requests
from dateutil.relativedelta import relativedelta
import datetime
import json
from common.models import HistoricalForexRates, HistoricalStockPrice, MutualFund, HistoricalMFPrice
from shared.utils import get_float_or_none_from_string
from .nasdaq import Nasdaq
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
                yf = YahooFinance2(stock)
                response = yf.get_historical_value(start, end)
                yf.close()
        return response
    if exchange == 'NSE' or exchange == 'NSE/BSE':
        #response = Nse(stock).get_historical_value(start, end)
        yf = YahooFinance2(stock+'.NS')
        response = yf.get_historical_value(start, end)
        yf.close()
        return response
    if exchange == 'BSE':
        #response = Nse(stock).get_historical_value(start, end)
        yf = YahooFinance2(stock+'.BO')
        response = yf.get_historical_value(start, end)
        yf.close()
        return response


def get_historic_vals(stock, exchange, start, end, etf=False):
    print(f"inside get_historic_vals exchange {exchange} start date: {start} end date: {end}")
    if exchange == 'NASDAQ':
        response = Nasdaq(stock, etf).get_historical_value(start, end)
        if not response:
            yf = YahooFinance2(stock)
            response = yf.get_historical_value(start, end)
            yf.close()
        return response
    if exchange == 'NSE' or exchange == 'NSE/BSE':
        #response = Nse(stock).get_historical_value(start, end)
        yf = YahooFinance2(stock+'.NS')
        response = yf.get_historical_value(start, end)
        yf.close()
        return response
    if exchange == 'BSE':
        #response = Nse(stock).get_historical_value(start, end)
        yf = YahooFinance2(stock+'.BO')
        response = yf.get_historical_value(start, end)
        yf.close()
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
                print(" data in get_mf_vals ", amfi_code, data)
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
            print(f"exception in getting historial mf vals for {amfi_code} for year {year} {ex}")
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
            ret = response.json().get('rates').get(to_cur)
            if not ret:
                print(f'no result for {date} {from_cur} {to_cur} using {url}')
            else:
                return round(ret, 2)
        except Exception as ex:
            print(f'exception while getting forex rate for: date {date}, from_cur {from_cur}, to_cur {to_cur} using {url}')
            time.sleep(5)
    if date == datetime.date.today():
        r = get_forex_goog(from_cur, to_cur)
        if r:
            return round(r, 2)
    r = get_forex_xe(date, from_cur, to_cur)
    return round(r, 2)

def get_forex_goog(from_cur, to_cur):
    from google_currency import convert
    for _ in range(5):
        try:
            res = json.loads(convert(from_cur, to_cur, 1))
            print(res)
            print(type(res))
            if res['converted']:
                a = get_float_or_none_from_string(res['amount'])
                if a:
                    return a
        except Exception as ex:
            print(f'goog exception while getting forex rate for: {from_cur} to {to_cur} {ex}')
            time.sleep(5)
    return None

def get_forex_xe(date, from_cur, to_cur):
    for _ in range(5):
        try:
            url = 'https://www.xe.com/_next/data/2erF0jj1nxvJi0kCVnQuw/en/currencytables.json?from='+from_cur+'&date='+date.strftime('%Y-%m-%d')
            response = requests.get(url, timeout=15) 
            # print response 
            # print json content
            j = response.json()
            #print(j)
            #print(j['pageProps']['historicRates'])
            for entry in j['pageProps']['historicRates']:
                if entry['currency'] == to_cur:
                    return entry['rate'] 
        except Exception as ex:
            print(f'xe: exception while getting forex rate for: date {date}, from_cur {from_cur}, to_cur {to_cur} {ex}')
            time.sleep(5)
    return None

def get_preferred_currency():
    from common.helper import get_preferences

    preferred_currency = get_preferences('currency')
    if not preferred_currency:
        preferred_currency = 'INR'
    return preferred_currency

# get provided amount in preferred currency given the date, amount and the from currency
def get_in_preferred_currency(amount, from_curr, dt, precision=2):
    if amount == 0:
        return 0
    preferred_currency = get_preferred_currency()
    if from_curr == preferred_currency:
        return amount
    conv_rate = get_conversion_rate(from_curr, preferred_currency, dt)
    if not conv_rate:
        print(f'failed to get conversion rate between {from_curr} and {preferred_currency} for {dt}')
        conv_rate = 0
    return round(amount * conv_rate, precision)

def get_conversion_rate(from_cur, to_cur, date):
    if from_cur == to_cur:
        return 1
    try:
        forex_rate = HistoricalForexRates.objects.get(from_cur=from_cur, to_cur=to_cur, date=date)
        return float(forex_rate.rate)
    except HistoricalForexRates.DoesNotExist:
        val = get_forex_rate(date, from_cur, to_cur)
        if val:
            new_entry = HistoricalForexRates(from_cur=from_cur, to_cur=to_cur, date=date, rate=val)
            new_entry.save()
            print(val)
            return float(val)
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
        begin_dt = end+relativedelta(days=-5)
        get_vals = get_historic_vals(stock.symbol, stock.exchange, begin_dt, datetime.date.today())
        if not get_vals:
            from tasks.tasks import pull_and_store_stock_historical_vals
            if stock.trading_status != 'Delisted' or (stock.delisting_date == None and stock.suspension_date == None) or (stock.delisting_date and stock.delisting_date > begin_dt) \
                or (stock.suspension_date and stock.suspension_date > begin_dt):
                pull_and_store_stock_historical_vals(stock.exchange, stock.symbol, start)
            return ret_vals
        for k,v in get_vals.items():
            new_date = k
            if isinstance(new_date, datetime.datetime):
                new_date = new_date.date()

            if isinstance(start, datetime.datetime):
                start = start.date()

            if isinstance(end, datetime.datetime):
                end = end.date()
                
            if new_date >= start and new_date<= end:
                try:
                    new_entry = HistoricalStockPrice.objects.create(symbol=stock, date=new_date, price=v)
                except IntegrityError as ex:
                    print(f'entry exists {stock.symbol} {stock.exchange} {new_date} {ex}')
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
    #print(f"getting historical mf nav for code {amfi_code} between {start} and {end}")
    ret_vals = list()
    start_date = end
    try:
        code = MutualFund.objects.get(code=amfi_code)
        while(start_date>=start):
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
            while(start_date>=start):
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