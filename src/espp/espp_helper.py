import requests
from dateutil.relativedelta import relativedelta
import datetime
import csv
import codecs
from contextlib import closing

def get_latest_vals(espp_obj):

    if espp_obj.exchange == 'NASDAQ':
        urlData = "http://www.nasdaq.com/api/v1/historical/" + espp_obj.symbol + "/stocks/"
        urlData += (datetime.date.today()+relativedelta(days=-5)).strftime('%Y-%m-%d')+ '/'
        urlData += datetime.date.today().strftime('%Y-%m-%d')
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
        response = requests.request('GET', urlData, headers=headers)
        text = response.iter_lines()
        reader = csv.DictReader(codecs.iterdecode(text, 'utf-8'), delimiter=',')
        for row in reader:
            date= None
            latest_val = None
            for k,v in row.items():
                if "Date" in k:
                    date = v
                elif "Close/Last" in k:
                    latest_val = v.strip()

            if date and latest_val:
                espp_obj.as_on_date = datetime.datetime.strptime(date, "%m/%d/%Y").date()
                espp_obj.latest_price = float(latest_val.replace('$',''))
                espp_obj.latest_conversion_rate = get_forex_rate(espp_obj.as_on_date, 'USD', 'INR')
                espp_obj.latest_value = float(espp_obj.latest_price) * float(espp_obj.latest_conversion_rate) * float(espp_obj.shares_purchased)
                espp_obj.gain = float(espp_obj.latest_value) - float(espp_obj.total_purchase_price)
                espp_obj.save()
                break
        print('done with request')

def get_forex_rate(date, from_cur, to_cur):
    # https://api.ratesapi.io/api/2020-01-31?base=USD&symbols=INR
    url = "https://api.ratesapi.io/api/" + date.strftime('%Y-%m-%d') + "?base=" + from_cur + "&symbols=" + to_cur
    response = requests.get(url) 
    # print response 
    print(response) 
    # print json content 
    print(response.json())
    return response.json().get('rates').get(to_cur)
