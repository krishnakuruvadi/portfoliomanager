import csv
import datetime
import os
import pathlib
import requests
from mftool import Mftool

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ', path)
    return path

def get_path_to_kuvera_csv():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    csv_file = os.path.join(path, 'kuvera.csv')
    return csv_file

def get_kuvera_mapping(csv_file):
    data = dict()

    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = True
        for row in reader:
            if not header:
                data[row[0]] = {'kuvera_name':row[1], 'kuvera_fund_category':row[2], 'kuvera_code':row[3]}
            header = False
    
    url = "https://api.kuvera.in/mf/api/v4/fund_schemes/list.json"
    r = requests.get(url, timeout=30)
    status = r.status_code
    if status != 200:
        print(f"An error has occured. [Status code {status} ]")
    else:
        ak_mapping = get_amfi_kuvera_fund_house_mapping()
        a_schemes = get_amfi_schemes()
        modified = 0
        added = 0

        for fund_type,v in r.json().items():
            #print(fund_type)
            for sub_category, details in v.items():
                #print(sub_category)
                for fund_house, fund_details in details.items():
                    #print(fund_house)
                    for fund in fund_details:
                        name = fund['n']
                        code = fund['c']
                        scheme_url = f"https://api.kuvera.in/mf/api/v4/fund_schemes/{code}.json"

                        response = requests.get(scheme_url, timeout=15)
                        if response.status_code != 200:
                            print('failed to get scheme details for {scheme_url}')
                            continue
                        j = response.json()
                        #dt = fund['r'].get('date')
                        print(j)
                        k_isin = j[0]['ISIN']
                        for code,det in a_schemes.items():
                            if det['isin1'] == k_isin or det['isin2'] == k_isin:
                                if code in data:
                                    changed = False
                                    if data[code]['kuvera_name'] != j[0]['name']:
                                        data[code]['kuvera_name'] = j[0]['name']
                                        changed = True
                                    if data[code]['kuvera_fund_category'] != j[0]['fund_category']:
                                        data[code]['kuvera_fund_category'] = j[0]['fund_category']
                                        changed = True
                                    if data[code]['kuvera_code'] != j[0]['code']:
                                        data[code]['kuvera_code'] = j[0]['code']
                                        changed = True
                                    if changed:
                                        modified += 1
                                else:
                                    data[code] = {'kuvera_name':j[0]['name'], 'kuvera_code':j[0]['code'], 'kuvera_fund_category':j[0]['fund_category']}
                                    added += 1
                                break
                        
    print(f'added {added} modified {modified}')
    if added >0 or modified > 0:
        fields = ['code','kuvera_name','kuvera_fund_category','kuvera_code']
        with open(csv_file, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            for i in sorted (data.keys()) :
                csvwriter.writerow([i, data[i]['kuvera_name'], data[i]['kuvera_fund_category'], data[i]['kuvera_code']])


def get_amfi_kuvera_fund_house_mapping():
    return {
        'BirlaSunLifeMutualFund_MF':'Aditya Birla Sun Life Mutual Fund',
        'AXISMUTUALFUND_MF':'Axis Mutual Fund',
        'BARODAMUTUALFUND_MF':'Baroda Mutual Fund',
        'BNPPARIBAS_MF':'BNP Paribas Mutual Fund',
        'BHARTIAXAMUTUALFUND_MF':'BOI AXA Mutual Fund',
        'CANARAROBECOMUTUALFUND_MF':'Canara Robeco Mutual Fund',
        'DSP_MF':'DSP Mutual Fund',
        'EDELWEISSMUTUALFUND_MF':'Edelweiss Mutual Fund',
        'FRANKLINTEMPLETON':'Franklin Templeton Mutual Fund',
        'HDFCMutualFund_MF':'HDFC Mutual Fund',
        'HSBCMUTUALFUND_MF':'HSBC Mutual Fund',
        'ICICIPrudentialMutualFund_MF':'ICICI Prudential Mutual Fund',
        'IDBIMUTUALFUND_MF':'IDBI Mutual Fund',
        'IDFCMUTUALFUND_MF':'IDFC Mutual Fund',
        'JM FINANCIAL MUTUAL FUND_MF':'JM Financial Mutual Fund',
        'KOTAKMAHINDRAMF':'Kotak Mahindra Mutual Fund',
        'LICMUTUALFUND_MF':'LIC Mutual Fund',
        'MOTILALOSWAL_MF':'Motilal Oswal Mutual Fund',
        'NipponIndiaMutualFund_MF':'Nippon India Mutual Fund',
        'PGIMINDIAMUTUALFUND_MF':'PGIM India Mutual Fund',
        'PRINCIPALMUTUALFUND_MF':'Principal Mutual Fund',
        'QUANTMUTUALFUND_MF':'quant Mutual Fund',
        'SBIMutualFund_MF':'SBI Mutual Fund',
        'SUNDARAMMUTUALFUND_MF':'Sundaram Mutual Fund',
        'TATAMutualFund_MF':'Tata Mutual Fund',
        'TAURUSMUTUALFUND_MF':'Taurus Mutual Fund',
        'UNIONMUTUALFUND_MF':'Union Mutual Fund'
    }

def get_amfi_schemes():
    """
    returns a dictionary with key as scheme code and value as scheme name.
    cache handled internally
    :return: dict / json
    """
    mf = Mftool()
    scheme_info = {}
    url = mf._get_quote_url
    response = mf._session.get(url)
    data = response.text.split("\n")
    fund_house = ""
    for scheme_data in data:
        if ";INF" in scheme_data:
            scheme = scheme_data.rstrip().split(";")
            if get_float_or_zero_from_string(scheme[4]) > 0:
                d = get_date_or_none_from_string(scheme[5], '%d-%b-%Y')
                #print(scheme[1],', ',scheme[2])
                if d:
                    scheme_info[scheme[0]] = {'isin1': scheme[1],
                                            'isin2':scheme[2],
                                            'name':scheme[3],
                                            'nav':get_float_or_zero_from_string(scheme[4]),
                                            'date':d,
                                            'fund_house':fund_house}
            else:
                print(f'ignoring {scheme[4]} nav fund {scheme[3]}')
        elif scheme_data.strip() != "":
            if ';' not in scheme_data:
                fund_house = scheme_data.strip()
    return scheme_info

def get_float_or_zero_from_string(input, printout=True):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to float. returning 0')
    return 0

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

if __name__ == "__main__":
    csv_file = get_path_to_kuvera_csv()
    get_kuvera_mapping(csv_file)
