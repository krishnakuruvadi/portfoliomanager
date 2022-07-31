import csv
import datetime
import json
import os
import pathlib
import requests
import bs4



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

def get_holidays(file):
    holidays = dict()
    if os.path.exists(file):
        with open(file) as f:
            holidays = json.load(f)
    '''
    r = requests.get('https://raw.githubusercontent.com/jugaad-py/master-data/master/holidays/holidays.csv')

    decoded_content = r.content.decode('utf-8')
    csv_reader = csv.reader(decoded_content.splitlines(), delimiter=',')
    for temp in csv_reader:
        print(temp[0])
        d = get_date_or_none_from_string(temp[0],'%Y-%m-%d')
        if d.year not in holidays:
            holidays[d.year] = list()
        holidays[d.year].append(d.strftime('%d-%m-%Y'))
    '''

    yr = datetime.date.today().year
    if yr in holidays:
        return
        
    url = 'https://www1.nseindia.com/products/content/equities/equities/mrkt_timing_holidays.htm'
    r = requests.get(url, headers = nse_headers(), timeout=15)
    if r.status_code==200:
        html = bs4.BeautifulSoup(r.content, 'html.parser')

        tables = html.find("table", { "class" : "holiday_list" })
        rows = tables.findAll('td')
        string_array = list()
        for row in rows:
            string_array.extend(row.text.splitlines())

        for string in string_array:
            valid = get_date_or_none_from_string(string, '%d-%b-%Y')
            if not valid:
                continue
            if yr not in holidays:
                holidays[yr] = list()
            holidays[yr].append(valid.strftime('%d-%m-%Y'))

        print(holidays)
        with open(file, 'w') as json_file:
            json.dump(holidays, json_file, indent=1)
    else:
        print(f'got unexpected response code {r.status_code}')

# default format expected of kind 2020-06-01
def get_date_or_none_from_string(input, format='%Y-%m-%d', printout=True):
    if input != None and input != '':
        try:
            res = datetime.datetime.strptime(input, format).date()
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to date. returning none' + str(e))
    return None

def get_nse_holidays(yr=None):
    url = 'https://gist.githubusercontent.com/krishnakuruvadi/7e12b660410e4be642f87977be009e65/raw/13072a48a4ccd687a2002eeaf46546402b5764e4/nse_holidays.json'
    r = requests.get(url, timeout=30)
    status = r.status_code
    if status != 200:
        print(f"An error has occured. [Status code {status} ]")
        return None
    if yr:
        return r.json().get(str(yr), None)
    return r.json()

def is_a_holiday(dt):
    '''
    Takes a date or string in format %d-%m-%Y and returns true or false
    Throws an exception if it cant reach the gist that has the holidays list or year not in gist
    '''
    if isinstance(dt, datetime.date):
        dt_str = dt.strftime('%d-%m-%Y')
        yr = str(dt.year)
    else:
        yr = dt[dt.rfind('-')+1:]
        dt_str = dt
    h = get_nse_holidays(yr)
    if dt_str in h:
        return True
    return False


if __name__ == "__main__":
    print(f'DEFAULT_DOWNLOAD_DIR {DEFAULT_DOWNLOAD_DIR}')
    #print(is_a_holiday(datetime.date(day=26,month=1,year=2021)))
    #r = get_nse_holidays("2021")
    #print(r)
    get_holidays(os.path.join(DEFAULT_DOWNLOAD_DIR, 'nse_holidays.json'))

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
    