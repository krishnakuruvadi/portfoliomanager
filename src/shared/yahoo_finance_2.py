import requests
#import pandas as pd
from .exchange import Exchange
import re
from io import StringIO
import datetime
import csv
import codecs

class YahooFinance2(Exchange):
    timeout = 2
    crumb_link = 'https://finance.yahoo.com/quote/{0}/history?p={0}'
    crumble_regex = r'CrumbStore":{"crumb":"(.*?)"}'
    quote_link = 'https://query1.finance.yahoo.com/v7/finance/download/{quote}?period1={dfrom}&period2={dto}&interval=1d&events=history&crumb={crumb}'
    retries = 5

    def __init__(self, symbol):
        self.symbol = symbol
        self.session = requests.Session()
        #self.dt = timedelta(days=days_back)

    def get_crumb(self):
        response = self.session.get(self.crumb_link.format(self.symbol), timeout=self.timeout)
        response.raise_for_status()
        match = re.search(self.crumble_regex, response.text)
        if not match:
            raise ValueError('Could not get crumb from Yahoo Finance')
        else:
            self.crumb = match.group(1)

    def get_datetime_from_date(self, date_obj):
        dt = datetime.datetime.combine(date_obj, datetime.datetime.min.time())
        return dt

    def get_historical_value(self, start, end):
        print('getting historical values from ', start, ' to ', end, ' for symbol ', self.symbol)
        for i in range(self.retries):
            try:
                if not hasattr(self, 'crumb') or len(self.session.cookies) == 0:
                    self.get_crumb()
                dt_to =  self.get_datetime_from_date(end)
                dt_from = self.get_datetime_from_date(start)
                dateto = int(dt_to.timestamp())
                datefrom = int(dt_from.timestamp())
                url = self.quote_link.format(quote=self.symbol, dfrom=datefrom, dto=dateto, crumb=self.crumb)
                response = self.session.get(url)
                response.raise_for_status()
                text = StringIO(response.text)#response.text
                print("in YahooFinance2 response.text:", response.text)
                reader = csv.DictReader(text, delimiter=',')
                response = dict()
                for row in reader:
                    date= None
                    latest_val = None
                    for k,v in row.items():
                        if "Date" in k:
                            date = datetime.datetime.strptime(v, "%Y-%m-%d").date()
                        elif "Close" in k:
                            latest_val = v.strip()

                    if date and latest_val and latest_val != 'null':
                        response[date] = float(latest_val)
                print('done with request')
                print(response)
                return response
            except Exception as e:
                print(e)
        return None
