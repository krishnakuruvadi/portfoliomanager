import bs4
import datetime
import json
import os
import pathlib
import requests


DEFAULT_DOWNLOAD_DIR = str(pathlib.Path(__file__).parent.parent.parent.absolute())


def extract_stock_data(tickerName):
    
    url = "https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php?classic=true&query="+tickerName+"&type=1&format=json"
    print("Retrieving stock data from money control {}".format(url))
    
    # fetch data
    response = requests.get(url, timeout=15)
    response_body = response.json()
    
    assert len(response_body) == 1
    
    print("Information fetched:")
    print(response_body[0])
    
    link_src = response_body[0]['link_src']
    extracted_link = link_src.split('/')
    
    return extracted_link[-1] , extracted_link[-2]


def nse_bse_eq_file_path():
    full_file_path = os.path.join(DEFAULT_DOWNLOAD_DIR, 'nse_bse_eq.json')
    return full_file_path

def is_nse_bse_eq_file_exists():
    full_file_path = nse_bse_eq_file_path()
    if os.path.exists(full_file_path):
        return True
    return False

def get_dividends(mc_code, dest_file=None):
    if not dest_file:
        dest_file = os.path.join(DEFAULT_DOWNLOAD_DIR, mc_code+'.json')
    
    data = dict()
    if os.path.exists(dest_file):
        with open(dest_file) as f:
            data = json.load(f)
    
    if not 'dividends' in data:
        data['dividends'] = list()
    
    dividends_url = f'https://www.moneycontrol.com/company-facts/infosys/dividends/{mc_code}#{mc_code}'
    r = requests.get(dividends_url, timeout=15)
    if r.status_code==200:
        print(f'found page')
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        table = soup.find("table", {"class":"mctable1"})
        tbody = table.find("tbody")
        rows = tbody.findChildren("tr")
        ret_dict = dict()
        for row in rows:
            print(f'row {row}')
            cols = row.findChildren("td")
            if cols and len(cols) >=5:
                ret_dict[cols[0].text.strip()] = {'amount': get_float_or_zero_from_string(cols[4].text.strip()), 'ex_date':get_date_or_none_from_string(cols[1].text, '%d-%m-%Y')}
        for dt,v in ret_dict.items():
            found = False
            announcement_date = get_date_or_none_from_string(dt, '%d-%m-%Y')
            for s in data['dividends']:
                if get_date_or_none_from_string(s['announcement_date'], '%d-%m-%Y') == announcement_date:
                    found = True
            if not found:
                data['dividends'].append({'announcement_date':announcement_date, 'amount': v['amount'], 'ex_date':v['ex_date']})
        
        print(data)
        with open(dest_file, 'w') as json_file:
            json.dump(data, json_file, indent=1, default=default)
    
    elif r.status_code==404:
        print(f"Page not found url: {r.url}")
    else:
        print(f"A different status code received : {str(r.status_code)} for url: {r.url}")

def get_bonus(mc_code, dest_file=None):
    if not dest_file:
        dest_file = os.path.join(DEFAULT_DOWNLOAD_DIR, mc_code+'.json')
    
    data = dict()
    if os.path.exists(dest_file):
        with open(dest_file) as f:
            data = json.load(f)
    
    if not 'bonus' in data:
        data['bonus'] = list()
    
    bonus_url = f'https://www.moneycontrol.com/company-facts/infosys/bonus/{mc_code}#{mc_code}'
    r = requests.get(bonus_url, timeout=15)
    if r.status_code==200:
        print(f'found page')
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        table = soup.find("table", {"class":"mctable1"})
        tbody = table.find("tbody")
        rows = tbody.findChildren("tr")
        ret_dict = dict()
        for row in rows:
            print(f'row {row}')
            cols = row.findChildren("td")
            if cols and len(cols) >=3:
                ret_dict[cols[0].text.strip()] = {'ratio': cols[1].text.strip(), 'record_date':get_date_or_none_from_string(cols[2].text, '%d-%m-%Y'), 'ex_date':get_date_or_none_from_string(cols[3].text, '%d-%m-%Y')}
        for dt,v in ret_dict.items():
            found = False
            announcement_date = get_date_or_none_from_string(dt, '%d-%m-%Y')
            for s in data['bonus']:
                if get_date_or_none_from_string(s['announcement_date'], '%d-%m-%Y') == announcement_date:
                    found = True
            if not found:
                data['bonus'].append({'announcement_date':announcement_date, 'ratio': v['ratio'], 'record_date':v['record_date'], 'ex_date':v['ex_date']})
        
        print(data)
        with open(dest_file, 'w') as json_file:
            json.dump(data, json_file, indent=1, default=default)
    
    elif r.status_code==404:
        print(f"Page not found url: {r.url}")
    else:
        print(f"A different status code received : {str(r.status_code)} for url: {r.url}")

def get_splits(mc_code, dest_file=None):
    if not dest_file:
        dest_file = os.path.join(DEFAULT_DOWNLOAD_DIR, mc_code+'.json')
    
    data = dict()
    if os.path.exists(dest_file):
        with open(dest_file) as f:
            data = json.load(f)
    
    if not 'splits' in data:
        data['splits'] = list()
    
    splits_url = f'https://www.moneycontrol.com/company-facts/infosys/splits/{mc_code}#{mc_code}'
    r = requests.get(splits_url, timeout=15)
    if r.status_code==200:
        print(f'found page')
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        table = soup.find("table", {"class":"mctable1"})
        tbody = table.find("tbody")
        rows = tbody.findChildren("tr")
        ret_dict = dict()
        for row in rows:
            print(f'row {row}')
            cols = row.findChildren("td")
            if cols and len(cols) >=3:
                ret_dict[cols[0].text.strip()] = {'old_fv': int(cols[1].text), 'new_fv':int(cols[2].text), 'ex_date':get_date_or_none_from_string(cols[3].text, '%d-%m-%Y')}
        for dt,v in ret_dict.items():
            found = False
            for s in data['splits']:
                if s['old_fv'] == v['old_fv']:
                    found = True
            if not found:
                data['splits'].append({'announcement_date':get_date_or_none_from_string(dt, '%d-%m-%Y'), 'old_fv': v['old_fv'], 'new_fv':v['new_fv'], 'ex_date':v['ex_date']})
        
        print(data)
        with open(dest_file, 'w') as json_file:
            json.dump(data, json_file, indent=1, default=default)
    
    elif r.status_code==404:
        print(f"Page not found url: {r.url}")
    else:
        print(f"A different status code received : {str(r.status_code)} for url: {r.url}")

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

def get_float_or_zero_from_string(input):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            print('error converting ', input, ' to float. returning 0')
    return 0

def fill_mc_code(n_b_path):
    stocks = dict()

    if is_nse_bse_eq_file_exists():
        with open(n_b_path) as f:
            stocks = json.load(f)
    
    print(stocks)
    for k in stocks.keys():
        try:
            c, _ = extract_stock_data(k)
            stocks[k]['mc_code'] = c
        except Exception as ex:
            print(f'{ex} finding mc code for {k}')
    
    with open(n_b_path, 'w') as json_file:
        json.dump(stocks, json_file)

if __name__ == "__main__":
    print(f'DEFAULT_DOWNLOAD_DIR {DEFAULT_DOWNLOAD_DIR}')
    '''
    n_b_path = nse_bse_eq_file_path()
    fill_mc_code(n_b_path)
    '''
    get_splits('SP19', '/Users/kkuruvad/Desktop/krishna/personal/portfoliomanager/src/media/corporateActions/INE03QK01018.json')
    get_bonus('SP19', '/Users/kkuruvad/Desktop/krishna/personal/portfoliomanager/src/media/corporateActions/INE03QK01018.json')
    get_dividends('SP19', '/Users/kkuruvad/Desktop/krishna/personal/portfoliomanager/src/media/corporateActions/INE03QK01018.json')
    