import requests
from django.conf import settings
import os
import csv
import time
from shared.handle_get import get_path_to_chrome_driver, get_files_in_dir, get_new_files_added
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from alerts.alert_helper import create_alert, Severity


nse_url = 'http://www1.nseindia.com/content/equities/EQUITY_L.csv'
bse_url = 'https://www.bseindia.com/corporates/List_Scrips.aspx'

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
    full_file_path = os.path.join(settings.MEDIA_ROOT, 'nse_eq.csv')
    return full_file_path

def pull_nse():
    headers = nse_headers()
    r = requests.get(nse_url, headers=headers, timeout=15)
    full_file_path = nse_eq_file_path()
    with open(full_file_path, 'wb') as f:
        f.write(r.content)

def is_nse_eq_file_exists():
    full_file_path = nse_eq_file_path()
    if os.path.exists(full_file_path):
        return True
    return False

def check_nse_api(nse):
    url_oc = "https://www.nseindia.com/option-chain"
    #url = f"https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                            'like Gecko) '
                            'Chrome/80.0.3987.149 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8', 'accept-encoding': 'gzip, deflate, br'}
    session = requests.Session()
    request = session.get(url_oc, headers=headers, timeout=5)
    cookies = dict(request.cookies)

    nse_meta_url = 'https://www.nseindia.com/api/equity-meta-info?symbol='+nse
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

def get_stock_code_nse(nse, isin):
    result = dict()
    if not is_nse_eq_file_exists():
        pull_nse()
    found = False

    with open(nse_eq_file_path(), 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if nse and nse != '':
                for k,v in row.items():
                    if k.strip() == 'SYMBOL' and v == nse:
                        result['nse'] = nse
                        found = True
                        break
                if found:
                    for k,v in row.items():
                        if k.strip() == 'ISIN NUMBER':
                            result['isin'] = v
            elif isin and isin != '':
                for k,v in row.items():
                    if k.strip() == 'ISIN NUMBER' and v == isin:
                        result['isin'] = isin
                        found = True
                        break
                if found:
                    for k,v in row.items():
                        if k.strip() == 'SYMBOL':
                            result['nse'] = v
            if found:
                break
    if not found and nse and nse != '':
        isin = check_nse_api(nse)
        if isin:
            result['nse'] = nse
            result['isin'] = isin
        else:
            return None

    return result

def get_stock_code_bse(bse, isin):
    result = dict()
    if not is_bse_eq_file_exists():
        pull_bse()
    found = False
    with open(bse_eq_file_path(), 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if bse and bse != '':
                for k,v in row.items():
                    if k.strip() == 'Security Id' and v == bse:
                        result['bse'] = bse
                        found = True
                        break
                if found:
                    for k,v in row.items():
                        if k.strip() == 'ISIN No':
                            result['isin'] = v
            elif isin and isin != '':
                for k,v in row.items():
                    if k.strip() == 'ISIN No' and v == isin:
                        result['isin'] = isin
                        found = True
                        break
                if found:
                    for k,v in row.items():
                        if k.strip() == 'Security Id':
                            result['bse'] = v
            if found:
                break
    if not found:
        return None

    return result

def bse_eq_file_path():
    full_file_path = os.path.join(settings.MEDIA_ROOT, 'bse_eq.csv')
    return full_file_path

def is_bse_eq_file_exists():
    full_file_path = bse_eq_file_path()
    if os.path.exists(full_file_path):
        return True
    return False

def pull_bse():
    existing_files = get_files_in_dir(settings.MEDIA_ROOT)

    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory' : settings.MEDIA_ROOT}
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(),options=chrome_options)
    driver.get(bse_url)
    timeout = 10
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, "ContentPlaceHolder1_ddSegment")))
        print('select element located')
        driver.find_element_by_xpath("//select[@id='ContentPlaceHolder1_ddSegment']/option[text()='Equity']").click()
        print('select element clicked')
        driver.find_element_by_xpath("//input[@id='ContentPlaceHolder1_btnSubmit']").click()
        print('submit element clicked')
        dload = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_lnkDownload')))
        print('download element located')
        dload.click()
        print('download element clicked')
        dload_file_name = None
        for _ in range(5):
            time.sleep(5)
            new_file_list = get_new_files_added(settings.MEDIA_ROOT, existing_files)        
            if len(new_file_list) == 1:
                dload_file_name = new_file_list[0]
                break
            elif len(new_file_list) > 1:
                description = ''
                for fil in new_file_list:
                    description = description + fil
                create_alert(
                    summary='Failure to get bse equity list.  More than one file found',
                    content= description,
                    severity=Severity.error
                )
                break
        if dload_file_name:
            os.rename(dload_file_name, bse_eq_file_path())

    except Exception as ex:
        print('Exception during pulling from bse', ex)
    driver.close()
    driver.quit()
    
def get_nse_bse(nse, bse, isin):
    quote = dict()
    if isin and isin != '':
        bse_data = get_stock_code_bse(bse, isin)
        if bse_data:
            quote['bse'] = bse_data['bse']
            quote['isin'] = bse_data['isin']
        nse_data = get_stock_code_nse(nse, isin)
        if nse_data:
            quote['nse'] = nse_data['nse']
            quote['isin'] = nse_data['isin']
        if len(quote) > 0:
            return quote
        else:
            return None
    
    if bse and bse != '':
        bse_data = get_stock_code_bse(bse, isin)
        if bse_data:
            quote['bse'] = bse_data['bse']
            quote['isin'] = bse_data['isin']
        else:
            return None
        nse_data = get_stock_code_nse(nse, quote['isin'])
        if nse_data:
            quote['nse'] = nse_data['nse']
            quote['isin'] = nse_data['isin']
        return quote
            
            
    if nse and nse != '':
        nse_data = get_stock_code_nse(nse, isin)
        if nse_data:
            quote['nse'] = nse_data['nse']
            quote['isin'] = nse_data['isin']
        else:
            return None   
        bse_data = get_stock_code_bse(bse, quote['isin'])
        if bse_data:
            quote['bse'] = bse_data['bse']
            quote['isin'] = bse_data['isin']
        return quote

    return None
    
