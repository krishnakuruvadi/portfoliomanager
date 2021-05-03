from shared.utils import convert_date_to_string
import os
import requests
from django.conf import settings
import zipfile
import csv
import json
from nsetools.utils import byte_adaptor
import time


class NSE:
    nse_equity_url = 'http://www1.nseindia.com/content/equities/EQUITY_L.csv'

    def __init__(self, symbol):
        self.symbol = symbol
        self.index_url="http://www1.nseindia.com/homepage/Indices1.json"


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
        for _ in range(5):
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
        for _ in range(5):
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
