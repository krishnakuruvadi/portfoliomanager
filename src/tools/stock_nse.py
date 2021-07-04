import csv
import json
import os
import pathlib
import requests



DEFAULT_DOWNLOAD_DIR = str(pathlib.Path(__file__).parent.parent.parent.absolute())
nse_url = 'http://www1.nseindia.com/content/equities/EQUITY_L.csv'
nse_midcap_url = 'https://www1.nseindia.com/content/indices/ind_niftymidcap150list.csv'
nse_largecap_url = 'https://www1.nseindia.com/content/indices/ind_nifty100list.csv'
nse_smallcap_url = 'https://www1.nseindia.com/content/indices/ind_niftysmallcap250list.csv'
nse_microcap_url = 'https://www1.nseindia.com/content/indices/ind_niftymicrocap250_list.csv'


def nse_headers():
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

def nse_eq_file_path():
    full_file_path = os.path.join(DEFAULT_DOWNLOAD_DIR, 'nse_eq.csv')
    return full_file_path

def pull_nse():
    headers = nse_headers()
    r = requests.get(nse_url, headers=headers, timeout=15)
    full_file_path = nse_eq_file_path()
    with open(full_file_path, 'wb') as f:
        f.write(r.content)

def pull_nse_cap_file(cap):
    headers = nse_headers()
    if cap == 'Large':
        url = nse_largecap_url
    elif cap == 'Mid':
        url = nse_midcap_url
    elif cap == 'Small':
        url = nse_smallcap_url
    else:
        url = nse_microcap_url
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code==200:
        decoded_content = r.content.decode('utf-8')
        csv_reader = csv.DictReader(decoded_content.splitlines(), delimiter=',')
        ret = list()
        for row in csv_reader:
            #print(row)
            ret.append({'isin':row['ISIN Code'], 'symbol':row['Symbol'], 'industry':row['Industry']})
        return ret
    print(f'Got different response {r.status_code}')
    return None

def is_nse_eq_file_exists():
    full_file_path = nse_eq_file_path()
    if os.path.exists(full_file_path):
        return True
    return False

def nse_bse_eq_file_path():
    full_file_path = os.path.join(DEFAULT_DOWNLOAD_DIR, 'nse_bse_eq.json')
    return full_file_path

def is_nse_bse_eq_file_exists():
    full_file_path = nse_bse_eq_file_path()
    if os.path.exists(full_file_path):
        return True
    return False

def add_or_append(inp, new_str):
    if not inp or inp == '':
        return new_str
    l = inp.split(';')
    if new_str in l:
        return inp
    return inp + ';' + new_str

def clean(d):
    res = dict()
    for k,v in d.items():
        res[k.strip()] = v
    return res

if __name__ == "__main__":
    print(f'DEFAULT_DOWNLOAD_DIR {DEFAULT_DOWNLOAD_DIR}')
    n_path = nse_eq_file_path()
    n_b_path = nse_bse_eq_file_path()

    
    if os.path.exists(n_path):
        print(f'Removing {n_path}')
        os.remove(n_path)
    pull_nse()
    print(f'Downloaded NSE data to {n_path}')

    stocks = dict()

    if is_nse_bse_eq_file_exists():
        with open(n_b_path) as f:
            stocks = json.load(f)
    
    for k,v in stocks.items():
        if v['nse_symbol'] == v['old_nse_symbol']:
            v['old_nse_symbol'] = ''
        elif v['nse_symbol'] in v['old_nse_symbol']:
            print(f"needs checking {v['nse_symbol']} {v['old_nse_symbol']}")
    

    with open(n_path, mode='r', encoding='utf-8-sig') as nse_csv_file:
        csv_reader = csv.DictReader(nse_csv_file)
        for temp in csv_reader:
            row = clean(temp)
            print(row)
            isin = row['ISIN NUMBER'].strip()
            if isin == '' or isin == 'NA' or not isin.startswith('IN'):
                print(f'ignoring isin {isin}')
                continue
            if not isin in stocks:
                stocks[isin] = {
                                'bse_security_code':'', 
                                'bse_security_id':'', 
                                'bse_name':'', 
                                'status':'',  
                                'industry':'',
                                'old_bse_security_code':'',
                                'old_bse_security_id':'',
                                'nse_name':'',
                                'listing_date':'',
                                'face_value':row['FACE VALUE'],
                                'old_nse_symbol':'',
                                'nse_symbol':'',
                                'mc_code':'',
                                'cap':''
                                }

            stocks[isin]['nse_name'] = row['NAME OF COMPANY']
            stocks[isin]['listing_date'] = row['DATE OF LISTING']

            if row['SYMBOL'] != stocks[isin]['nse_symbol']:
                if not stocks[isin]['nse_symbol'] == '':
                    stocks[isin]['old_nse_symbol'] = add_or_append(stocks[isin].get('old_nse_symbol', None), row['SYMBOL'])
                stocks[isin]['nse_symbol'] = row['SYMBOL']
      
    for cap in ['Large','Mid','Small','Micro']:
        ret = pull_nse_cap_file(cap)
        for entry in ret:
            if entry['isin'] in stocks:
                stocks[entry['isin']]['cap'] = cap+'-Cap'
                if stocks[entry['isin']]['industry'] == '':
                    stocks[entry['isin']]['industry'] = entry['industry']
            else:
                print(f'Unknown isin to fill capitalization {entry["isin"]} {entry["symbol"]}')

    with open(n_b_path, 'w') as json_file:
        json.dump(stocks, json_file, indent=1)
    
    os.remove(n_path)
    