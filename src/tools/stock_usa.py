import bs4
import datetime
import json
import os
import pathlib
import requests

DEFAULT_DOWNLOAD_DIR = str(pathlib.Path(__file__).parent.parent.parent.absolute())
VERSION = 1

def get_sp_large_cap_500(data):
    print('Gathering up-to-date list of S&P Largecap 500 stock tickers...')
    wikiurl = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', timeout=15)
    scrape = bs4.BeautifulSoup(wikiurl.text, "lxml")
    table = scrape.find('table', {'class':'wikitable sortable'})
    for row in table.findAll('tr')[1:]:
        cols = row.findAll('td')
        stock = cols[0].text.strip()
        industry = cols[3].text.strip()
        name = cols[1].text.strip()
        data['stocks'][stock] = {'industry':industry, 'name':name, 'cap':'Large-Cap'}
    
    print('Stocks successfully acquired')
    return data

def get_sp_midcap_400(data):
    print('Gathering up-to-date list of S&P Midcap 400 stock tickers...')
    wikiurl = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies', timeout=15)
    scrape = bs4.BeautifulSoup(wikiurl.text, "lxml")
    table = scrape.find('table', {'class':'wikitable sortable'})
    
    for row in table.findAll('tr')[1:]:
        cols = row.findAll('td')
        stock = cols[1].text.strip()
        industry = cols[2].text.strip()
        name = cols[0].text.strip()
        data['stocks'][stock] = {'industry':industry, 'name':name, 'cap':'Mid-Cap'}
    
    print('Stocks successfully acquired')
    return data

def store_stocks(data, dest=None):
    if not dest:
        dest = os.path.join(DEFAULT_DOWNLOAD_DIR, 'usa.json')
    with open(dest, 'w') as json_file:
        json.dump(data, json_file, indent=1)

def get_init_data(dest=None):
    data = dict()
    if not dest:
        dest = os.path.join(DEFAULT_DOWNLOAD_DIR, 'usa.json')
    if os.path.exists(dest):
        with open(dest) as f:
            data = json.load(f)
    else:
        data['stocks'] = dict()
    return data

def get_mcap(symbol):
    user_agent_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    defaultKeyStatistics = requests.get(f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?formatted=true&crumb=8ldhetOu7RJ&lang=en-US&region=US&modules=defaultKeyStatistics%2CfinancialData%2CcalendarEvents&corsDomain=finance.yahoo.com', timeout=15, headers=user_agent_headers)
    summaryDetail = requests.get(f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?formatted=true&crumb=8ldhetOu7RJ&lang=en-US&region=US&modules=summaryDetail&corsDomain=finance.yahoo.com', timeout=15, headers=user_agent_headers)
    profile = requests.get(f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=assetProfile', timeout=15, headers=user_agent_headers)
    defaultKeyStatistics = defaultKeyStatistics.json()
    summaryDetail = summaryDetail.json()
    profile = profile.json()

    print("totalCash " + str(defaultKeyStatistics['quoteSummary']['result'][0]['financialData']['totalCash']['raw']))
    print("totalDebt " + str(defaultKeyStatistics['quoteSummary']['result'][0]['financialData']['totalDebt']['raw']))
    print("freeCashflow " + str(defaultKeyStatistics['quoteSummary']['result'][0]['financialData']['freeCashflow']['raw']))
    print("ebitda " + str(defaultKeyStatistics['quoteSummary']['result'][0]['financialData']['ebitda']['raw']))
    print("grossMargins " + str(defaultKeyStatistics['quoteSummary']['result'][0]['financialData']['grossMargins']['raw']))
    print("marketCap " + str(summaryDetail['quoteSummary']['result'][0]['summaryDetail']['marketCap']['raw']))
    #print("industry " + str(profile['quoteSummary']['result'][0]['assetProfile']['industry']))
    print("fullTimeEmployees " + str(profile['quoteSummary']['result'][0]['assetProfile']['fullTimeEmployees']))

def get_corp_actions(symbol, dest_file=None):
    import yfinance as yf
    t = yf.Ticker(symbol)
    hist = t.history(period="max")
    ss = t.get_splits()
    ss = ss.to_dict()
    ds = t.get_dividends()
    ds = ds.to_dict()
    splits = dict()
    dividends = dict()
    data = dict()
    if os.path.exists(dest_file):
        with open(dest_file) as f:
            data = json.load(f)
    
    if not 'splits' in data:
        data['splits'] = list()

    for dt, val in ss.items():
        #print(f'split: {type(dt)} {dt} {val}')
        splits[dt.to_pydatetime().date()] = float(val)
    
    for dt, val in ds.items():
        #print(f'dividend: {type(dt)} {dt} {val}')
        dividends[dt.to_pydatetime().date()] = float(val)
    
    for k,v in splits.items():
        new_fv = 1
        old_fv = v

        x = get_date_or_none_from_string(k, '%d-%m-%Y')

        data['splits'].append({'announcement_date':x, 'old_fv': old_fv, 'new_fv':new_fv, 'ex_date':x})


    print(data)
    with open(dest_file, 'w') as json_file:
        json.dump(data, json_file, indent=1, default=default)
    return splits, dividends

def default(o):
    if type(o) is datetime.date or type(o) is datetime.datetime:
        return o.strftime('%d-%m-%Y')
    return o

# default format expected of kind 2020-06-01
def get_date_or_none_from_string(input, format='%Y-%m-%d', printout=True):
    if input != None and input != '':
        if type(input) is datetime.date:
            return input
        try:
            res = datetime.datetime.strptime(input, format).date()
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to date. returning none' + str(e))
    return None

if __name__ == "__main__":
    #stock = yf.Ticker('QQQ')
    #print(stock.get_info())
    #get_corp_actions('NVDA')
    #get_mcap('FB')


    # show actions (dividends, splits)
    splits, dividends = get_corp_actions('NVDA')
    print(splits)
    

    exit(0)
    data = get_init_data()
    data = get_sp_large_cap_500(data)
    data = get_sp_midcap_400(data)
    last_updated_format = '%Y-%m-%d'
    data['version'] = VERSION
    data['last_updated'] = datetime.datetime.today().strftime(last_updated_format)
    data['last_updated_format'] = last_updated_format
    store_stocks(data)

    