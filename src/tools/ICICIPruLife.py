from tika import parser
import datetime
import requests
from dateutil.relativedelta import relativedelta

def get_date_or_none_from_string(input, format='%Y-%m-%d', printout=False):
    if input != None and input != '':
        try:
            res = datetime.datetime.strptime(input, format).date()
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to date. returning none' + str(e))
    return None

def get_float_or_none_from_string(input, printout=False):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to float. returning none')
    return None

class ICICIPruLife:

    def __init__(self):
        pass
    
    def get_transactions(self, trans_file):
        parsed = parser.from_file(trans_file)
        #print(parsed["content"])
        prev = None
        fund = None
        last_dt_trans = list()
        transactions = dict()
        for l in parsed['content'].splitlines():
            if l.strip() == '':
                continue
            if 'TransactionDate' in l and prev:
                fund = prev.replace('TRANSACTION SUMMARY FOR ', '')
            elif 'Opening Balance' in l:
                continue
            elif 'Closing Balance' in l:
                ldt = get_date_or_none_from_string(l.split(' ')[0], '%d-%b-%Y')
                for t in last_dt_trans:
                    t['date'] = ldt
                    transactions[fund].append(t)
                last_dt_trans.clear()
                fund = None
            elif fund:
                tran = dict()
                description = ''
                field = 0
                for i, token in enumerate(l.split(' ')):
                    if i == 0:
                        dt = get_date_or_none_from_string(token, '%d-%b-%Y')
                        if dt:
                            tran['date'] = dt
                            field = 1
                        else:
                            if description == '':
                                description = token
                            else:
                                description += ' ' + token
                            field = 1
                    else:
                        temp = get_float_or_none_from_string(token)
                        if not temp and temp != 0:
                            if description == '':
                                description = token
                            else:
                                description += ' ' + token
                        else:
                            if field == 1:
                                tran['units'] = temp
                                tran['description'] = description
                            elif field == 2:
                                tran['nav'] = temp
                            elif field == 3:
                                tran['trans_amount'] = temp
                            field += 1
                if not fund in transactions:
                    transactions[fund] = list()
                if 'date' in tran:
                    transactions[fund].append(tran)
                else:
                    last_dt_trans.append(tran)
            else:
                print(f'ignore {l}')
            prev = l
        return transactions
    
    def get_url_code_from_fund_code(self, fund_code):
        res = self.get_fund_details(fund_code)
        if res:
            return res['LAfundCode']
        return None

    def get_nav(self, fund_url_code, from_dt, to_dt):
        st_dt = from_dt.strftime("%d-%b-%Y").upper()
        end_dt = to_dt.strftime("%d-%b-%Y").upper()
        url = f'https://buy.iciciprulife.com/buy/funds-nav-history.htm?fundCode={fund_url_code}&startDate={st_dt}&endDate={end_dt}'
        headers = {'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Origin': 'https://www.iciciprulife.com',
                    'Host': 'buy.iciciprulife.com',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
                    'X-Requested-With': 'XMLHttpRequest'
                }
        r = requests.get(url, headers=headers, timeout=15)
        status = r.status_code
        if status != 200:
            print(f"An error has occured. [Status code {status} ]")
            return None
        print(f'result: {r.text} for url {url}')
        return r.json()

    def get_fund_details(self, fund_code):
        to_dt = datetime.date.today()
        from_dt = to_dt + relativedelta(days=-7)
        url = f'https://buy.iciciprulife.com/buy/funds-all-products.htm?startDate={from_dt.strftime("%d-%b-%Y").upper()}&endDate={to_dt.strftime("%d-%b-%Y").upper()}'
        headers = {'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Origin': 'https://www.iciciprulife.com',
                    'Host': 'buy.iciciprulife.com',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
                    'X-Requested-With': 'XMLHttpRequest'
                }
        r = requests.get(url, headers=headers, timeout=15)
        status = r.status_code
        if status != 200:
            print(f"An error has occured. [Status code {status} ]")
            return None
        for item in r.json():
            if item['SFIN'] == fund_code:
                res = {
                    'name': item['Fund'],
                    'asset_class': item['AssetClass'],
                    '1M': get_float_or_none_from_string(item['Perf1Month'].replace('%','')),
                    '6M': get_float_or_none_from_string(item['Perf6Month'].replace('%','')),
                    '1Y': get_float_or_none_from_string(item['Perf1Year'].replace('%','')),
                    '2Y': get_float_or_none_from_string(item['Perf2Year'].replace('%','')),
                    '3Y': get_float_or_none_from_string(item['Perf3Year'].replace('%','')),
                    '4Y': get_float_or_none_from_string(item['Perf4Year'].replace('%','')),
                    '5Y': get_float_or_none_from_string(item['Perf5Year'].replace('%','')),
                    'inception': get_float_or_none_from_string(item['PerfInception'].replace('%','')),
                    'start_date': get_date_or_none_from_string(item['InceptionDate'],'%Y-%m-%d'),
                    'nav': get_float_or_none_from_string(item['NAVLatest']),
                    'nav_date': get_date_or_none_from_string(item['NAVLatestDate'],'%d-%b-%Y'),
                    'LAfundCode':item['LAfundCode']
                }
                return res
        return None
    
    def get_latest_nav(self, fund_code):
        res = self.get_fund_details(fund_code)
        if res:
            return {'date':res['nav_date'], 'nav':res['nav']}
        return None
    
    def get_historical_nav(self, fund_code, dt):
        url_code = self.get_url_code_from_fund_code(fund_code)
        if not url_code:
            print(f'invalid code {fund_code} to get url code')
            return None
        res = self.get_nav(url_code, dt+relativedelta(days=-7), dt)
        if not res:
            print(f'failed to get nav for code {fund_code} url code {url_code}')
            return None
        for item in reversed(res):
            dt = get_date_or_none_from_string(item['x'],'%d-%b-%Y')
            nav = get_float_or_none_from_string(item['y'])
            if dt and nav:
                return {'date':dt, 'nav':nav}
            else:
                print(f"failed to convert {item['x']} and {item['y']} to valid values")
        return None
