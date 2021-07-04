from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import json
import os
import pathlib
import time


DEFAULT_DOWNLOAD_DIR = str(pathlib.Path(__file__).parent.parent.parent.absolute())
bse_url = 'https://www.bseindia.com/corporates/List_Scrips.aspx'


def get_files_in_dir(dir):
    file_list = list()
    for file in os.listdir(dir):
        path = os.path.join(dir, file)
        file_list.append(path)

    return file_list

def get_new_files_added(dir, existing_list):
    new_file_list = list()
    for file in os.listdir(dir):
        path = os.path.join(dir, file)
        if path not in existing_list:
            new_file_list.append(path)
    return new_file_list

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ',path)
    return path

def pull_bse():
    existing_files = get_files_in_dir(DEFAULT_DOWNLOAD_DIR)

    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory' : DEFAULT_DOWNLOAD_DIR}
    chrome_options.add_experimental_option('prefs', prefs)
    chrome_options.add_argument("--headless")
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
            new_file_list = get_new_files_added(DEFAULT_DOWNLOAD_DIR, existing_files)        
            if len(new_file_list) == 1:
                dload_file_name = new_file_list[0]
                break
            elif len(new_file_list) > 1:
                description = ''
                for fil in new_file_list:
                    description = description + fil
                
                summary='Failure to get bse equity list.  More than one file found;' + description
                print(summary)
                exit(1)
        if dload_file_name:
            os.rename(dload_file_name, bse_eq_file_path())

    except Exception as ex:
        print('Exception during pulling from bse', ex)
    driver.close()
    driver.quit()

def bse_eq_file_path():
    full_file_path = os.path.join(DEFAULT_DOWNLOAD_DIR, 'bse_eq.csv')
    return full_file_path

def is_bse_eq_file_exists():
    full_file_path = bse_eq_file_path()
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

def nse_bse_eq_file_path():
    full_file_path = os.path.join(DEFAULT_DOWNLOAD_DIR, 'nse_bse_eq.json')
    return full_file_path

def is_nse_bse_eq_file_exists():
    full_file_path = nse_bse_eq_file_path()
    if os.path.exists(full_file_path):
        return True
    return False

if __name__ == "__main__":
    print(f'DEFAULT_DOWNLOAD_DIR {DEFAULT_DOWNLOAD_DIR}')
    b_path = bse_eq_file_path()
    n_b_path = nse_bse_eq_file_path()

    if os.path.exists(b_path):
        print(f'Removing {b_path}')
        os.remove(b_path)
    pull_bse()
    print(f'Downloaded BSE data to {b_path}')
    stocks = dict()

    if is_nse_bse_eq_file_exists():
        with open(n_b_path) as f:
            stocks = json.load(f)
    
    
    with open(b_path, mode='r', encoding='utf-8-sig') as bse_csv_file:
        csv_reader = csv.DictReader(bse_csv_file)
        for temp in csv_reader:
            #print(row)
            row = clean(temp)
            isin = row['ISIN No'].strip()
            if isin == '' or isin == 'NA' or not isin.startswith('IN'):
                print(f'ignoring isin {isin}')
                continue
            if not isin in stocks: 
                stocks[isin] = {
                                'bse_security_code':row['Security Code'], 
                                'bse_security_id':row['Security Id'], 
                                'bse_name': row['Security Name'], 
                                'status':row['Status'], 
                                'face_value':row['Face Value'], 
                                'industry':row['Industry'],
                                'old_bse_security_code':'',
                                'old_bse_security_id':'',
                                'nse_name':'',
                                'listing_date':'',
                                'old_nse_symbol':'',
                                'nse_symbol':'',
                                'mc_code':'',
                                'cap':''
                                }
            else:
                if row['Security Code'] != stocks[isin]['bse_security_code']:
                    if stocks[isin]['bse_security_code'] != '':
                        stocks[isin]['old_bse_security_code'] = add_or_append(stocks[isin].get('old_bse_security_code', None), row['Security Code'])
                    stocks[isin]['bse_security_code'] = row['Security Code']
                if row['Security Id'] != stocks[isin]['bse_security_id']:
                    if stocks[isin]['bse_security_id'] != '':
                        stocks[isin]['old_bse_security_id'] = add_or_append(stocks[isin].get('old_bse_security_id', None), row['Security Id'])
                    stocks[isin]['bse_security_id'] = row['Security Id']
                stocks[isin]['status'] = row['Status']
                stocks[isin]['face_value'] = row['Face Value']
                stocks[isin]['industry'] = row['Industry']

    
    with open(n_b_path, 'w') as json_file:
        json.dump(stocks, json_file)
    
    os.remove(b_path)
    