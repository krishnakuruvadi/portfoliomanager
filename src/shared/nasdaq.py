from .exchange import Exchange
import requests
import csv
import datetime
import codecs

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
                response[date] = float(latest_val.replace('$',''))
        print('done with request')
        print(response)
        return response