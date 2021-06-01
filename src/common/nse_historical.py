from shared.utils import convert_date_to_string
import os
import requests
from django.conf import settings
import zipfile
import csv

class NSEHistorical:

    def __init__(self, symbol, historical_date, debug=False):
        self.historical_date = historical_date
        self.symbol = symbol
        self.debug = debug

    def get_bhav_copy_csv_file_name(self):
        month = convert_date_to_string(self.historical_date, format='%b')
        month = month.upper()
        return 'cm' + convert_date_to_string(self.historical_date, format='%d') + month + str(self.historical_date.year) + 'bhav.csv'

    def get_bhav_copy_zip_file_name(self):
        month = convert_date_to_string(self.historical_date, format='%b')
        month = month.upper()
        return 'cm' + convert_date_to_string(self.historical_date, format='%d') + month + str(self.historical_date.year) + 'bhav.csv.zip'
    '''
    https://www1.nseindia.com/content/historical/EQUITIES/2018/OCT/cm24OCT2018bhav.csv.zip
    '''
    def get_bhav_nse_equity_url(self):
        nse_bhav_url = 'https://www1.nseindia.com/content/historical/EQUITIES/' + str(self.historical_date.year) + '/'
        month = convert_date_to_string(self.historical_date, format='%b')
        month = month.upper()
        nse_bhav_url += month
        nse_bhav_url += '/' + self.get_bhav_copy_zip_file_name()

        return nse_bhav_url

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

    def nse_bhav_copy_file_path(self):
        bc_path = os.path.join(settings.MEDIA_ROOT, 'bhav_copy')
        if not os.path.exists(bc_path):
            os.makedirs(bc_path)
        return bc_path

    def pull_nse(self, nse_url):
        headers = self.nse_headers()
        r = requests.get(nse_url, headers=headers, timeout=15)
        full_file_path = self.nse_bhav_copy_file_path()
        with open(full_file_path, 'wb') as f:
            f.write(r.content)

    def download_url(self, url, save_path, chunk_size=128):
        print(f'getting url {url}')
        r = requests.get(url, headers=self.nse_headers(), stream=True, timeout=15)
        if r.status_code == 200:
            with open(save_path, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    fd.write(chunk)
            return True
        print(f'failed to download bhav copy from: {url}')
        return False

    def get_isin_from_bhav_copy(self):
        bc_path = self.nse_bhav_copy_file_path()
        bc_zip_file = os.path.join(bc_path, self.get_bhav_copy_zip_file_name())
        
        bc_file = os.path.join(bc_path, self.get_bhav_copy_csv_file_name())
        if not os.path.exists(bc_zip_file):
            if self.debug:
                print(f'getting bhav copy for date {self.historical_date}')
            if self.download_url(self.get_bhav_nse_equity_url(), bc_zip_file):
                with zipfile.ZipFile(os.path.join(bc_path,bc_zip_file), 'r') as zip_ref:
                    zip_ref.extractall(bc_path)
            else:
                print(f'failed to download bhav copy of {self.symbol} for date {self.historical_date}')
        else:
            if self.debug:
                print(f'bhav copy exists locally for date {self.historical_date}')
            if not os.path.exists(bc_file):
                if os.path.exists(bc_zip_file):
                    with zipfile.ZipFile(os.path.join(bc_path,bc_zip_file), 'r') as zip_ref:
                        zip_ref.extractall(bc_path)
                else:
                    print(f'ERROR: bhav copy zip file not found locally for date {self.historical_date}')
            else:
                print(f'bhav copy exists locally and is extracted for date {self.historical_date}')
        if os.path.exists(bc_file):
            if self.debug:
                print(f"checking for isin for row['SYMBOL'] in bhav copy file {bc_file}")
            with open(bc_file, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    if row['SYMBOL'] == self.symbol:
                        return row['ISIN']
        return None
