from .exchange import Exchange
import requests
import csv
import datetime
import codecs
from dateutil.parser import parse
from pytz import timezone
from common.helper import get_preferences
from dateutil import tz
from django.utils import timezone
from shared.utils import get_float_or_zero_from_string

class Nasdaq(Exchange):
    def __init__(self, stock):
        self.name = 'Nasdaq'
        self.stock = stock

    def get_historical_value(self, start, end):
        get_response = None
        for i in range(5):
            urlData = "http://www.nasdaq.com/api/v1/historical/" + self.stock + "/stocks/"
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
                response[date] = get_float_or_zero_from_string(latest_val.replace('$',''))
        print('done with request')
        print(response)
        return response
    
    def get_index_val(self):
        get_response = None
        for i in range(5):
            urlData = "https://api.nasdaq.com/api/quote/"+self.stock+"/info?assetclass=index" 
            print("accessing "+urlData)
            headers =  {'Accept': 'application/json, text/plain, */*',
                 'DNT': "1",
                 'Origin': 'https://www.nasdaq.com/',
                 'Sec-Fetch-Mode': 'cors',
                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'}
            get_response = requests.request('GET', urlData, headers=headers)
            print(get_response)
            if get_response.status_code == 200:
                break
        if get_response.status_code != 200:
            return None
        #print(get_response.content)
        json_data = get_response.json()
        data = dict()
        if 'data' in json_data:
            data['symbol'] = json_data['data']['symbol']
            data['name'] = json_data['data']['companyName']
            data['lastPrice'] = json_data['data']['primaryData']['lastSalePrice']
            data['change'] = get_float_or_zero_from_string(json_data['data']['primaryData']['netChange'])
            data['pChange'] = json_data['data']['primaryData']['percentageChange']
            data['pChange'] = get_float_or_zero_from_string(data['pChange'].replace('%',''))
            date_str = json_data['data']['primaryData']['lastTradeTimestamp']
            date_str = date_str.replace('DATA AS OF', '')
            date_str = date_str.replace(' ET', '')
            date_obj = parse(date_str)
            from_zone = timezone('America/Cancun')
            date_obj = date_obj.replace(tzinfo=from_zone)
            to_zone = tz.tzutc()
            data['last_updated'] = date_obj.astimezone(to_zone).strftime("%Y-%m-%d %H:%M:%S")

        return data

    def get_all_index(self):
        get_response = None
        for i in range(5):
            urlData = "https://api.nasdaq.com/api/quote/watchlist?symbol=comp%7cindex&symbol=ndx%7cindex&symbol=indu%7cindex&symbol=rui%7cindex&symbol=omxs30%7cindex&symbol=omxn40%7cindex&symbol=omxb10%7cindex&symbol=cac40%7cindex&symbol=nik%25sl%25o%7cindex" 
            print("accessing "+urlData)
            headers =  {'Accept': 'application/json, text/plain, */*',
                 'DNT': "1",
                 'Origin': 'https://www.nasdaq.com/',
                 'Sec-Fetch-Mode': 'cors',
                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'}
            get_response = requests.request('GET', urlData, headers=headers)
            print(get_response)
            if get_response.status_code == 200:
                break
        if get_response.status_code != 200:
            return None
        #print(get_response.content)
        json_data = get_response.json()
        #print(json_data)
        data = dict()
        if 'data' in json_data:
            for ind in json_data['data']:
                symbol = ind['symbol']
                data[symbol] = dict()
                data[symbol]['name'] = ind['companyName']
                data[symbol]['lastPrice'] = ind['lastSalePrice']
                data[symbol]['change'] = get_float_or_zero_from_string(ind['netChange'])
                data[symbol]['pChange'] = ind['percentageChange']
                data[symbol]['pChange'] = get_float_or_zero_from_string(data[symbol]['pChange'].replace('%',''))
                try:
                    date_str = ind['lastTradeTimestamp']
                    date_str = date_str.replace('DATA AS OF', '')
                    date_str = date_str.replace(' ET', '')
                    date_obj = parse(date_str)
                    from_zone = timezone('America/Cancun')
                    date_obj = date_obj.replace(tzinfo=from_zone)
                    to_zone = tz.tzutc()
                    data[symbol]['last_updated'] = date_obj.astimezone(to_zone).strftime("%Y-%m-%d %H:%M:%S")
                except Exception as ex:
                    data[symbol]['last_updated'] = timezone.now()
        return data
    
    def get_latest_val(self):
        get_response = None
        for i in range(5):
            urlData = "https://api.nasdaq.com/api/quote/" + self.stock + "/info?assetclass=stocks"
            print("accessing "+urlData)
            '''
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
            '''
            headers =  {
                'Accept': 'application/json, text/plain, */*',
                'DNT': "1",
                'Origin': 'https://www.nasdaq.com/',
                'Sec-Fetch-Mode': 'cors',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'
            }
            get_response = requests.request('GET', urlData, headers=headers)
            #print(get_response)
            if get_response.status_code == 200:
                break
        if get_response.status_code != 200:
            print(get_response)
            return None
        json_data = get_response.json()
        #print(json_data)
        data = dict()
        if 'data' in json_data:
            if 'secondaryData' in json_data['data'] and  json_data['data']['secondaryData']:
                timestamp = json_data['data']['secondaryData']['lastTradeTimestamp']
                if 'ON' in timestamp:
                    pos = timestamp.find('ON')
                    timestamp = timestamp[pos+3:]
                    #print(timestamp)
                    date = datetime.datetime.strptime(timestamp, "%b %d, %Y").date()
                    data[date] = json_data['data']['secondaryData']['lastSalePrice']
            if 'primaryData' in json_data['data'] and  json_data['data']['primaryData']:
                timestamp = json_data['data']['primaryData']['lastTradeTimestamp']
                if 'ON' in timestamp:
                    pos = timestamp.find('ON')
                    timestamp = timestamp[pos+3:]
                if 'OF'in timestamp:
                    pos = timestamp.find('OF')
                    timestamp = timestamp[pos+3:]
                #print(timestamp)
                date = datetime.datetime.strptime(timestamp, "%b %d, %Y").date()
                latest_val = json_data['data']['primaryData']['lastSalePrice']
                data[date] = get_float_or_zero_from_string(latest_val.replace('$',''))
        #print('done with request')
        #print(data)
        return data