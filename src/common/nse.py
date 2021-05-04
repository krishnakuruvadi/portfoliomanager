from shared.utils import convert_date_to_string
import os
import requests
from django.conf import settings
import zipfile
import csv
import json
from nsetools.utils import byte_adaptor
import time
import re
import six
if six.PY2:
    from urllib2 import build_opener, HTTPCookieProcessor, Request
    from urllib import urlencode
    from cookielib import CookieJar
else:
    from urllib.request import build_opener, HTTPCookieProcessor, Request
    from urllib.parse import urlencode
    from http.cookiejar import CookieJar

class NSE:
    nse_equity_url = 'http://www1.nseindia.com/content/equities/EQUITY_L.csv'

    def __init__(self, symbol):
        self.symbol = symbol
        self.index_url="http://www1.nseindia.com/homepage/Indices1.json"
        self.get_quote_url = 'https://www1.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?'
        self.opener = self.nse_opener()
    
    def nse_headers(self):
        """
        Headers required for requesting http://nseindia.com
        :return: a dict with http headers
        """
        return {'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Host': 'www1.nseindia.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
                'X-Requested-With': 'XMLHttpRequest'
                }

    def nse_eq_file_path(self):
        full_file_path = os.path.join(settings.MEDIA_ROOT, 'nse_eq.csv')
        return full_file_path

    def pull_nse(self):
        headers = self.nse_headers()
        r = requests.get(self.nse_equity_url, headers=headers)
        full_file_path = self.nse_eq_file_path()
        with open(full_file_path, 'wb') as f:
            f.write(r.content)

    def is_nse_eq_file_exists(self):
        full_file_path = self.nse_eq_file_path()
        if os.path.exists(full_file_path):
            return True
        return False

    def check_nse_api(self):
        url_oc = "https://www.nseindia.com/option-chain"
        #url = f"https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                'like Gecko) '
                                'Chrome/80.0.3987.149 Safari/537.36',
                'accept-language': 'en,gu;q=0.9,hi;q=0.8', 'accept-encoding': 'gzip, deflate, br'}
        session = requests.Session()
        request = session.get(url_oc, headers=headers, timeout=5)
        cookies = dict(request.cookies)

        nse_meta_url = 'https://www.nseindia.com/api/equity-meta-info?symbol=' + self.symbol
        r = session.get(nse_meta_url, headers=headers, timeout=5, cookies=cookies)
        status = r.status_code
        if status != 200:
            print(f"An error has occured. [Status code {status} ] for {nse_meta_url}")
        else:
            print(r.json())
            result = r.json()
            if 'isin' in result:
                return result['isin']
        return None

    def get_isin(self):
        isin = None
        if not self.is_nse_eq_file_exists():
            self.pull_nse()
        found = False

        with open(self.nse_eq_file_path(), 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                for k,v in row.items():
                    if k.strip() == 'SYMBOL' and v == self.symbol:
                        found = True
                        break
                if found:
                    for k,v in row.items():
                        if k.strip() == 'ISIN NUMBER':
                            return v

        if not isin:
            isin = self.check_nse_api()

        return isin
    
    def get_symbol(self, isin):
        if not self.is_nse_eq_file_exists():
            self.pull_nse()
        found = False

        with open(self.nse_eq_file_path(), 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                for k,v in row.items():
                    if k.strip() == 'ISIN NUMBER' and v == isin:
                        found = True
                        break
                if found:
                    for k,v in row.items():
                        if k.strip() == 'SYMBOL':
                            return v
        return None

    def get_index_list(self):
        for _ in range(3):
            try:
                headers = self.nse_headers()
                r = requests.get(self.index_url, headers=headers, timeout=10)
                resp = r.content
                #print(f'resp {resp}')
                j = json.loads(resp)
                #print(f'j {j}')
                resp_list = j['data']
                index_list = [str(item['name']) for item in resp_list]
                return index_list
            except Exception as ex:
                print(f'exception getting index list {ex}')
                time.sleep(3)
        return None

    def get_index_quote(self, code):
        for _ in range(3):
            try:
                headers = self.nse_headers()
                r = requests.get(self.index_url, headers=headers, timeout=10)
                resp = r.content
                #print(f'resp {resp}')
                j = json.loads(resp)
                #print(f'j {j}')
                resp_list = j['data']
                for item in resp_list:
                    if item['name'] == code:
                        item['lastPrice'] = float(item['lastPrice'].replace(',',''))
                        item['change'] = float(item['change'].replace(',',''))
                        item['pChange'] = float(item['pChange'].replace(',',''))
                        return item
            except Exception as ex:
                print(f'exception getting index list {ex}')
                time.sleep(3)
        return None
    
    def build_url_for_quote(self, code):
        """
        builds a url which can be requested for a given stock code
        :param code: string containing stock code.
        :return: a url object
        """
        if code is not None and type(code) is str:
            encoded_args = urlencode([('symbol', code), ('illiquid', '0'), ('smeFlag', '0'), ('itpFlag', '0')])
            return self.get_quote_url + encoded_args
        else:
            raise Exception('code must be string')

    def nse_opener(self):
        """
        builds opener for urllib2
        :return: opener object
        """
        cj = CookieJar()
        return build_opener(HTTPCookieProcessor(cj))

    def get_quote(self, code):
        code = code.upper()
        url = self.build_url_for_quote(code)
        for _ in range(3):
            try:
                headers = self.nse_headers()
                req = Request(url, None, headers)
                #r = requests.get(url, headers=headers, timeout=10)
                res = self.opener.open(req, timeout=10)
                res = byte_adaptor(res)
                res = res.read()
                #resp = r.content
                #print(resp)
                match = re.search(\
                        r'<div\s+id="responseDiv"\s+style="display:none">(.*?)</div>',
                        res, re.S
                    )
                try:
                    buffer = match.group(1).strip()
                    #print(f'buffer:{buffer}')
                    response = self.clean_server_response(json.loads(buffer)['data'][0])
                    #print(f'response {response}')
                    return response
                except SyntaxError as err:
                    raise Exception('ill formatted response')
            except Exception as ex:
                print(f'exception getting index list {ex}')
                time.sleep(3)
        return None

    def clean_server_response(self, resp_dict):
        """cleans the server reponse by replacing:
            '-'     -> None
            '1,000' -> 1000
        :param resp_dict:
        :return: dict with all above substitution
        """

        # change all the keys from unicode to string
        d = {}
        for key, value in resp_dict.items():
            d[str(key)] = value
        resp_dict = d
        for key, value in resp_dict.items():
            if type(value) is str or isinstance(value, six.string_types):
                if re.match('-', value):
                    try:
                        if float(value) or int(value):
                            dataType = True
                    except ValueError:
                        resp_dict[key] = None
                elif re.search(r'^[0-9,.]+$', value):
                    # replace , to '', and type cast to int
                    resp_dict[key] = float(re.sub(',', '', value))
                else:
                    resp_dict[key] = str(value)
        return resp_dict
