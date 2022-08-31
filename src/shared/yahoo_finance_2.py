import requests
from .exchange import Exchange
import re
from io import StringIO
import datetime
import csv


class YahooFinance2(Exchange):
    timeout = 5
    crumb_link = 'https://finance.yahoo.com/quote/{0}/history?p={0}'
    crumble_regex = r'CrumbStore":{"crumb":"(.*?)"}'
    quote_link = 'https://query1.finance.yahoo.com/v7/finance/download/{quote}?period1={dfrom}&period2={dto}&interval=1d&events=history&crumb={crumb}'
    quote_link_no_crumb = 'https://query1.finance.yahoo.com/v7/finance/download/{quote}?period1={dfrom}&period2={dto}&interval=1d&events=history'
    live_link = 'https://query1.finance.yahoo.com/v8/finance/chart/{quote}?region=US&lang=en-US&includePrePost=false&interval=2m&useYfid=true&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance'
    live_link_2 = "https://query2.finance.yahoo.com/v7/finance/quote?symbols={quote}"
    
    user_agent_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    def __init__(self, symbol, retries=5):
        self.symbol = symbol
        self.session = None
        self.crumb = None
        self.retries = retries
        self.get_session()

    def get_session(self):
        self.session = requests.Session()

    def close(self):
        self.session.close()
        self.session = None
        self.crumb = None

    def get_crumb(self):
        response = self.session.get(self.crumb_link.format(self.symbol), timeout=self.timeout, headers=self.user_agent_headers)
        response.raise_for_status()
        match = re.search(self.crumble_regex, response.text)
        if not match:
            raise ValueError('Could not get crumb from Yahoo Finance')
        else:
            self.crumb = match.group(1)

    def get_datetime_from_date(self, date_obj, use_min=True):
        dt = datetime.datetime.combine(date_obj, datetime.datetime.min.time() if use_min else datetime.datetime.max.time())
        return dt

    def get_historical_value(self, start, end, include_crumb=False):
        print('getting historical values from ', start, ' to ', end, ' for symbol ', self.symbol)
        for _ in range(self.retries):
            try:
                if not self.session or len(self.session.cookies) == 0:
                    self.get_session()
                if not self.crumb and include_crumb:
                    self.get_crumb()
                dt_to =  self.get_datetime_from_date(end,False)
                dt_from = self.get_datetime_from_date(start)
                dateto = int(dt_to.timestamp())
                datefrom = int(dt_from.timestamp())
                url = self.quote_link_no_crumb.format(quote=self.symbol, dfrom=datefrom, dto=dateto)
                if include_crumb:
                    url = self.quote_link.format(quote=self.symbol, dfrom=datefrom, dto=dateto, crumb=self.crumb)
                response = self.session.get(url, timeout=self.timeout, headers=self.user_agent_headers)
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
        if not include_crumb:
            return self.get_historical_value(start, end, True)
        return None

    def get_live_price(self, name, include_crumb=False):
        ret_v2 = self.get_live_price_v2()
        if ret_v2:
            return ret_v2
        print('getting live values for symbol ', self.symbol)
        for _ in range(self.retries):
            data = None
            try:
                if not self.session or len(self.session.cookies) == 0:
                    self.get_session()
                if not self.crumb and include_crumb:
                    self.get_crumb()
                url= self.live_link.format(quote=self.symbol)
                response = self.session.get(url, timeout=self.timeout, headers=self.user_agent_headers)
                response.raise_for_status()
                text = StringIO(response.text)#response.text
                #print("in YahooFinance2 response.text:", response.text)
                data = response.json()
                #print(data)
                ret = dict()
                ret['name'] = name
                meta_data = data["chart"]["result"][0]['meta']
                ret['lastPrice'] = meta_data['regularMarketPrice']
                ret['change'] = round(meta_data['regularMarketPrice'] - meta_data['chartPreviousClose'], 2)
                ret['pChange'] = round(ret['change']*100/meta_data['chartPreviousClose'], 2)
                date_obj = datetime.datetime.fromtimestamp(meta_data['regularMarketTime'])
                ret['version'] = 'v1'
                '''
                from_zone = pytz.timezone(meta_data['exchangeTimezoneName'])
                date_obj = date_obj.replace(tzinfo=from_zone)
                to_zone = tz.tzutc()
                ret['last_updated'] = date_obj.astimezone(to_zone).strftime("%Y-%m-%d %H:%M:%S")
                #ret['last_updated']:2021-05-07 00:03:29, date_obj:2021-05-06 19:07:29-04:56
                #print(f"ret['last_updated']:{ret['last_updated']}, date_obj:{date_obj}")
                '''
                ret['last_updated'] = date_obj
                return ret

            except Exception as e:
                print(f'exception {e} when processing {data}')
        if not include_crumb:
            return self.get_live_price(name, True)

        return None
    
    def get_live_price_v2(self, include_crumb=False):
        print('getting live values (v2) for symbol ', self.symbol)
        for _ in range(self.retries):
            data = None
            try:
                if not self.session or len(self.session.cookies) == 0:
                    self.get_session()
                if not self.crumb and include_crumb:
                    self.get_crumb()
                url= self.live_link_2.format(quote=self.symbol)
                response = self.session.get(url, timeout=self.timeout, headers=self.user_agent_headers)
                response.raise_for_status()
                data = response.json()
                #print(data)
                ret = dict()
                meta_data = data["quoteResponse"]["result"][0]
                ret['lastPrice'] = round(meta_data['regularMarketPrice'], 2)
                ret['prevClose'] = round(meta_data['regularMarketPreviousClose'], 2)
                ret['change'] = round(meta_data['regularMarketChange'], 2)
                ret['pChange'] = round(meta_data['regularMarketChangePercent'], 2)
                date_obj = datetime.datetime.fromtimestamp(meta_data['regularMarketTime'])
                ret['52wHigh'] = round(meta_data['fiftyTwoWeekHigh'], 2)
                ret['52wLow'] = round(meta_data['fiftyTwoWeekLow'], 2)
                ret['version'] = 'v2'
                ret['200dAvg'] = round(meta_data['twoHundredDayAverage'], 2)
                ret['50dAvg'] = round(meta_data['fiftyDayAverage'], 2)
                ret['dayHigh'] = round(meta_data['regularMarketDayHigh'], 2)
                ret['dayLow'] = round(meta_data['regularMarketDayLow'], 2)
                if 'priceToBook' in meta_data:
                    ret['PB'] = round(meta_data['priceToBook'], 2)
                else:
                    ret['PB'] = None
                if 'forwardPE' in meta_data:
                    ret['fwdPE'] = round(meta_data['forwardPE'], 2)
                else:
                    ret['fwdPE'] = None
                if 'trailingPE' in meta_data:
                    ret['trailingPE'] = round(meta_data['trailingPE'], 2)
                else:
                    ret['trailingPE'] = None
                if 'epsForward' in meta_data:
                    ret['epsForward'] = round(meta_data['epsForward'], 2)
                else:
                    ret['epsForward'] = None
                if 'epsCurrentYear' in meta_data:
                    ret['epsCurrentYear'] = round(meta_data['epsCurrentYear'], 2)
                else:
                    ret['epsCurrentYear'] = None
                if 'averageAnalystRating' in meta_data:
                    ret['averageAnalystRating'] = meta_data['averageAnalystRating']
                else:
                    ret['averageAnalystRating'] = None
                ret['last_updated'] = date_obj
                return ret

            except Exception as e:
                print(f'exception {e} when processing {data}')
        if not include_crumb:
            return self.get_live_price_v2(True)

        return None
