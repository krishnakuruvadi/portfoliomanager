from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import pathlib
import time
from tasks.tasks import add_mf_transactions
from .mf_helper import mf_add_or_update_sip_coin
import re

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ', path)
    return path

def pull_coin(user, userid, passwd, twofa):
    url = "https://coin.zerodha.com/"
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
        login_elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Login']")))
        login_elem.click()
        user_id_elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID,'userid')))
        user_id_elem.send_keys(userid)
        passwd_elem = driver.find_element_by_id('password')
        passwd_elem.send_keys(passwd)
        submit_button = driver.find_element_by_xpath('//button[text()="Login "]')
        submit_button.click()
        time.sleep(3)
        pin_element = driver.find_element_by_id('pin')
        pin_element.send_keys(twofa)
        submit_button = driver.find_element_by_xpath('//button[text()="Continue "]')
        submit_button.click()
        time.sleep(5)
        if driver.current_url != url+'dashboard':
            driver.get(url+'dashboard')
            time.sleep(5)
        oh = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[text()[contains(.,'Order History')]]")))
        oh.click()
        csv = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[text()[contains(.,'Export to CSV')]]")))
        csv.click()
        time.sleep(10)
        #userid_elem = driver.find_element_by_xpath("//span[@class='mobile-show']")
        #userid_elem.click()
        #time.sleep(5)
        #logout_elem = driver.find_element_by_xpath("//a[text()[contains(.,'Logout')]]")
        #logout_elem.click()
        sips = pull_sip(driver)
        driver.get(url+'logout')
        time.sleep(5)
        driver.quit()
        if sips:
            mf_add_or_update_sip_coin(sips, dload_file)
        add_mf_transactions('COIN ZERODHA', user, dload_file)
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
        tables = driver.find_elements_by_tag_name('table')
        #table = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'table-container']")))
        if len(tables) != 0:
            print('found table')
        else:
            print('table not found')
            return None
        table = tables[0]
        tbody = table.find_element_by_tag_name('tbody')
        print('found table body')

        for tr in tbody.find_elements_by_tag_name('tr'):
            print('inside row')

            tds = tr.find_elements_by_tag_name('td')
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