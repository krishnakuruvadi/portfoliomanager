import requests
from dateutil.relativedelta import relativedelta
import datetime
import csv
import codecs
from contextlib import closing
from common.models import HistoricalForexRates, HistoricalStockPrice


def get_latest_vals(stock, exchange, start, end):

    if exchange == 'NASDAQ':
        get_response = None
        for i in range(5):
            urlData = "http://www.nasdaq.com/api/v1/historical/" + stock + "/stocks/"
            urlData += start.strftime('%Y-%m-%d')+ '/'
            urlData += end.strftime('%Y-%m-%d')
            print("accessing "+urlData)
            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
                'User-Agent': "PostmanRuntime/7.13.0",
                'Accept': "*/*",
                'Cache-Control': "no-cache",
                'Host': "www.nasdaq.com",
                'accept-encoding': "gzip, deflate",
                'content-length': "166",
                'Connection': "close",
                'cache-control': "no-cache"
                }
            get_response = requests.request('GET', urlData, headers=headers)
            print(get_response)
            if get_response.status_code == 200:
                break
        if get_response.status_code != 200:
            return None
        text = get_response.iter_lines()
        reader = csv.DictReader(codecs.iterdecode(text, 'utf-8'), delimiter=',')
        response = dict()
        for row in reader:
            date= None
            latest_val = None
            for k,v in row.items():
                if "Date" in k:
                    date = datetime.datetime.strptime(v, "%m/%d/%Y").date()
                elif "Close/Last" in k:
                    latest_val = v.strip()

            if date and latest_val:
                response[date] = float(latest_val.replace('$',''))
        print('done with request')
        print(response)
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
        get_vals = get_latest_vals(stock.symbol, stock.exchange, end+relativedelta(months=-1), datetime.date.today())
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
