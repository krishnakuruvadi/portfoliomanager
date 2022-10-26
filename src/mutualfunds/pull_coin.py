from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import os
import pathlib
import time
from shared.utils import get_date_or_none_from_string, get_float_or_zero_from_string
from tasks.tasks import add_mf_transactions
from .mf_helper import mf_add_or_update_sip_coin
import re
import datetime
from django.conf import settings

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ', path)
    return path

def pull_coin(user, userid, passwd, twofa):
    dload_files = pull_zerodha(userid, passwd, twofa)
    for dload_file in dload_files:
        add_mf_transactions('COIN ZERODHA', user, dload_file)
    url = "https://coin.zerodha.com/login"
    chrome_options = webdriver.ChromeOptions()
    dload_path = pathlib.Path(__file__).parent.parent.absolute()
    dload_path = os.path.join(dload_path, 'media')

    prefs = {'download.default_directory' : dload_path}
    dload_file = os.path.join(dload_path,'coin_order_history.csv')
    if os.path.exists(dload_file):
        os.remove(dload_file)
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(), chrome_options=chrome_options)
    driver.get(url)
    try:
        #login_elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[text()[contains(.,'Log in')]]")))
        #login_elem.click()
        user_id_elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID,'userid')))
        user_id_elem.send_keys(userid)
        passwd_elem = driver.find_element(By.ID, 'password')
        passwd_elem.send_keys(passwd)
        submit_button = driver.find_element(By.XPATH, '//button[text()="Login "]')
        submit_button.click()
        time.sleep(3)
        pin_element = driver.find_element(By.ID, 'pin')
        pin_element.send_keys(twofa)
        submit_button = driver.find_element(By.XPATH, '//button[text()="Continue "]')
        submit_button.click()
        time.sleep(5)
        '''
        if driver.current_url != url+'dashboard':
            driver.get(url+'dashboard')
            time.sleep(5)
        driver.get(url+'portfolio/holdings')
        time.sleep(5)
        oh = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[text()[contains(.,'Order History')]]")))
        oh.click()
        csv = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[text()[contains(.,'Export to CSV')]]")))
        csv.click()
        time.sleep(10)
        '''
        #userid_elem = driver.find_element(By.XPATH, "//span[@class='mobile-show']")
        #userid_elem.click()
        #time.sleep(5)
        #logout_elem = driver.find_element(By.XPATH, "//a[text()[contains(.,'Logout')]]")
        #logout_elem.click()
        sips = pull_sip(driver)
        driver.get('https://coin.zerodha.com/logout')
        time.sleep(5)
        driver.quit()
        if sips:
            mf_add_or_update_sip_coin(sips, dload_files)
        
    except TimeoutException as t:
        print('timeout waiting', t)
        driver.close()
    except Exception as ex:
        print('Exception during processing', ex)
        driver.close()

def pull_sip(driver):
    sips = list()
    try:
        sc = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[text()[contains(.,'SIP & Conditional')]]")))
        sc.click()
        time.sleep(5)
        print('searching table')
        tables = driver.find_elements(By.TAG_NAME, 'table')
        #table = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'table-container']")))
        if len(tables) != 0:
            print('found table')
        else:
            print('table not found')
            return None
        table = tables[0]
        tbody = table.find_element(By.TAG_NAME, 'tbody')
        print('found table body')

        for tr in tbody.find_elements(By.TAG_NAME, 'tr'):
            print('inside row')

            tds = tr.find_elements(By.TAG_NAME, 'td')
            if len(tds) >= 6:
                name = get_content(tds[0])
                amount = get_content(tds[2]).replace('₹','')
                date = get_content(tds[3])
                date=date[date.find('on '):]
                date = int(date.strip().replace('on', '').replace('nd', '').replace('st', '').replace('rd', '').replace('nd', '').replace('th', '').strip())
                active = get_content(tds[6]).strip()
                plan = name[name.find('(')+1:name.find(')')]
                name = name[:name.find('(')-1]
                name=name.strip()
                print(name)
                print(plan)
                print(amount)
                print(date)
                print(active)
                sip = dict()
                sip['name'] = name
                sip['plan'] = plan
                sip['amount'] = float(amount)
                sip['date'] = int(date)
                sip['active'] = active
                sips.append(sip)
            else:
                print(f'len(tds): {len(tds)}')
        return sips
    except Exception as ex:
        print('exception in pulling sips from COIN ZERODHA')
        print(ex)
    return None

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

def pull_zerodha(userid, passwd, pin):
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--headless")
    url = "https://coin.zerodha.com/login"
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(), chrome_options=chrome_options)
    driver.get(url)
    time.sleep(5)
    print(driver.current_url)
    try:
        user_id_elem = driver.find_element(By.ID, 'userid')
        user_id_elem.send_keys(userid)
        passwd_elem = driver.find_element(By.ID, 'password')
        passwd_elem.send_keys(passwd)
        submit_button = driver.find_element(By.XPATH, '//button[text()="Login "]')
        submit_button.click()
        time.sleep(3)
        pin_element = driver.find_element(By.ID, 'pin')
        pin_element.send_keys(pin)
        submit_button = driver.find_element(By.XPATH, '//button[text()="Continue "]')
        submit_button.click()
        time.sleep(5)
        mf_url = "https://coin.zerodha.com/dashboard/mf/"
        driver.get(mf_url)

        time.sleep(5)
        transactions = dict()
        divs = driver.find_elements(By.XPATH, "//div[@class='fund-name text-16']")
        for div in divs:
            folio = None
            isin = None
            div.click()
            time.sleep(5)
            header = driver.find_element(By.XPATH, '//div[@class="fund-header"]')
            for anchor in header.find_elements(By.TAG_NAME, "a"):
                print(f'text: {anchor.text} href: {anchor.get_attribute("href")}')
                isin = anchor.get_attribute("href").replace('https://coin.zerodha.com/mf/fund/', '')
                
            footer = driver.find_element(By.XPATH, '//div[@class="three columns left"]')
            for span in footer.find_elements(By.TAG_NAME, "span"):
                if 'folio' in span.text.lower():
                    pass
                else:
                    folio = span.text
                    if folio not in transactions:
                        transactions[folio] = dict()
                    if isin not in transactions[folio]:
                        transactions[folio][isin] = list()
            trans = driver.find_element(By.XPATH, '//div[text()="View transactions"]')
            trans.click()
            time.sleep(5)
            trans_tbl = driver.find_element(By.XPATH, "//table[@class='holdings-breakdown__table']")
            for row in trans_tbl.find_elements(By.TAG_NAME, "tr"):
                #print(row)
                entry = dict()
                found = False
                for index, col in enumerate(row.find_elements(By.TAG_NAME, "td")):
                    found = True
                    if index == 0:
                        dt = col.text.replace('nd', '').replace('st', '').replace('rd', '').replace('th', '')
                        entry['date'] = get_date_or_none_from_string(dt, '%d %b %Y')
                    elif index == 2:
                        entry['amount'] = get_float_or_zero_from_string(col.text.replace(',',''))
                        if entry['amount'] < 0:
                            entry['amount'] = -1*entry['amount']
                            entry['trade_type'] = 'sell'
                        else:
                            entry['trade_type'] = 'buy'
                    elif index == 3:
                        entry['nav'] = get_float_or_zero_from_string(col.text.replace(',',''))
                    elif index == 4:
                        entry['units'] = get_float_or_zero_from_string(col.text.replace(',',''))
                        if entry['units'] < 0:
                            entry['units'] = -1*entry['units']
                            entry['trade_type'] = 'sell'
                        else:
                            entry['trade_type'] = 'buy'
                if found:
                    print(f'folio {folio} entry {entry} isin {isin}')
                    if isin and folio:
                        transactions[folio][isin].append(entry)
            
            sp = driver.find_element(By.XPATH, "//span[@class='icon feather-x']")
            sp.click()
            time.sleep(3)
            sp = driver.find_element(By.XPATH, "//span[@class='icon feather-chevron-up']")
            sp.click()
            time.sleep(3)

        userid_elem = driver.find_element(By.XPATH, "//span[@class='user-name']")
        userid_elem.click()
        time.sleep(5)
        logout_elem = driver.find_element(By.XPATH, "//a[text()[contains(.,'Logout')]]")
        logout_elem.click()
        driver.close()
        time.sleep(5)
        f = write_trans_to_csv_file(transactions)
        return [f]

    except Exception as ex:
        print(f'exception getting transactions from coin/zerodha {ex}')
        driver.close()

def write_trans_to_csv_file(transactions):
    import csv  

    header = ['isin', 'folio_number', 'trade_date', 'trade_type', 'quantity', 'price', 'amount']
    f = os.path.join(settings.MEDIA_ROOT, datetime.datetime.now().strftime("%m%d%Y%H%M%S")+'.csv')
    with open(f, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)

        # write the header
        writer.writerow(header)

        for folio, folio_data in transactions.items():
            for isin, trans in folio_data.items():
                for t in trans:
                    writer.writerow([isin, folio, t['date'],t['trade_type'], t['units'], t['nav'], t['amount']])
    return f.name

'''
def pull_zerodha(userid, passwd, pin):
    from kiteconnect import KiteConnect
    import requests
    import json
    session = requests.Session()
    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                    }
    session.headers.update(headers)
    base_url = "https://kite.zerodha.com"
    login_url = "https://kite.zerodha.com/api/login"
    twofa_url = "https://kite.zerodha.com/api/twofa"
    r = session.get(base_url)
    r = session.post(login_url, data={"user_id": userid, "password":passwd})
    j = json.loads(r.text)

    data = {"user_id": userid, "request_id": j['data']["request_id"], "twofa_value": pin }
    r = session.post(twofa_url, data=data)
    j = json.loads(r.text)


def pull_zerodha(userid, passwd, pin):
    dload_files = list()
    url = 'https://console.zerodha.com/reports/tradebook'
    chrome_options = webdriver.ChromeOptions()
    dload_path = pathlib.Path(__file__).parent.parent.absolute()
    dload_path = os.path.join(dload_path, 'media')
    prefs = {'download.default_directory' : dload_path}
    files_in_dload_dir = get_files_in_dir(dload_path)
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(), chrome_options=chrome_options)
    driver.get(url)
    time.sleep(5)
    print(driver.current_url)
    try:
        user_id_elem = driver.find_element(By.ID, 'userid')
        user_id_elem.send_keys(userid)
        passwd_elem = driver.find_element(By.ID, 'password')
        passwd_elem.send_keys(passwd)
        submit_button = driver.find_element(By.XPATH, '//button[text()="Login "]')
        submit_button.click()
        time.sleep(3)
        pin_element = driver.find_element(By.ID, 'pin')
        pin_element.send_keys(pin)
        submit_button = driver.find_element(By.XPATH, '//button[text()="Continue "]')
        submit_button.click()
        time.sleep(5)
        if driver.current_url != url:
            driver.get(url)
            time.sleep(5)
    except Exception as ex:
        print(f'Exception {ex} while logging in')
        driver.close()
        return None

    try:
        time.sleep(5)
        #selects = driver.find_elements(By.TAG_NAME, 'select')
        #for s in selects:
        #    print(s)
        sel_choice=driver.find_element(By.XPATH, "//select/option[@value='MF']")
        sel_choice.click()
        time.sleep(5)
        #from_date = datetime.date(year=2013,month=4,day=1)
        yr = datetime.date.today().year
        if datetime.date.today().month < 4:
            yr -= 1
        while True:
            from_date = datetime.date(year=yr, month=4, day=1)
            to_date = datetime.date(year=yr+1, month=3, day=31)
            if to_date > datetime.date.today():
                to_date = datetime.date.today()
            date_string = from_date.strftime("%Y-%m-%d") + " ~ " + to_date.strftime("%Y-%m-%d")
            print(date_string)
            #view_element =  WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//button[text()[contains(.,"View")]]')))
            view_element =  WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @class="btn-blue"]')))
            date_range = driver.find_element(By.NAME, ('date')
            date_range.clear()
            time.sleep(5)
            for _ in range(len(date_string)):
                date_range.send_keys(Keys.BACKSPACE)
            date_range.send_keys(date_string)
            time.sleep(5)
            view_element.click()
            
            #WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//button[text()[contains(.,"View")]]')))
            WebDriverWait(driver,60).until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @class="btn-blue"]')))
            if len(driver.find_elements(By.XPATH, "//a[text()[contains(.,'CSV')]]")) > 0:
                dload_elem = driver.find_element(By.XPATH, "//a[text()[contains(.,'CSV')]]")
                dload_elem.click()
                dload_file = os.path.join(dload_path, userid+'_tradebook_'+from_date.strftime("%Y-%m-%d") + "_to_" + to_date.strftime("%Y-%m-%d")+'.csv')
                file_found = False
                for _ in range(10):
                    if os.path.exists(dload_file):
                        print(f'file found {dload_file}.  Will parse for transactions.')
                        file_found = True
                        dload_files.append(dload_file)
                        break
                    time.sleep(1)
                if not file_found:
                    new_file_list = get_new_files_added(dload_path,files_in_dload_dir)
                    
                    if len(new_file_list) == 1:
                        dload_files.append(new_file_list[0])
                        files_in_dload_dir.append(new_file_list[0])
                        print(f'file found {new_file_list[0]}.  Will parse for transactions.')

                    if len(new_file_list) > 1:
                        description = ''
                        for fil in new_file_list:
                            description = description + fil
                        create_alert(
                            summary='Failure to get transactions for ' + userid + '.  More than one file found',
                            content= description,
                            severity=Severity.error,
                            alert_type="Action"
                        )
                
            else:
                print(f'couldnt download any transactions for period {date_string}')
                if len(driver.find_elements(By.XPATH, "//h3[@id='mainText' and @text='Something went wrong']")) > 0:
                    break
                if len(driver.find_elements(By.XPATH, "//h3[@id='mainText']"))>0:
                    h3_elem = driver.find_element(By.XPATH, "//h3[@id='mainText']")
                    print(f'h3 element found with text {h3_elem.text}')
                src = driver.page_source
                text_found = re.search(r'Something went wrong', src)
                if text_found:
                    break
            yr = yr -1

        userid_elem = driver.find_element(By.XPATH, "//a[@class='dropdown-label user-id']")
        userid_elem.click()
        logout_elem = driver.find_element(By.XPATH, "//a[text()[contains(.,'Logout')]]")
        logout_elem.click()
        time.sleep(5)
        driver.close()
        return dload_files
    except TimeoutException as t:
        print('timeout waiting', t)
        driver.close()
        return dload_files
    except Exception as ex:
        print('Exception during processing', ex)
        driver.close()
        return dload_files
'''

def get_content(el):
    content = el.get_attribute('innerHTML')
    #print(f'innerHTML {content}')
    content = content.strip()
    content = cleanhtml(content)
    content = content.strip()
    return content


def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext