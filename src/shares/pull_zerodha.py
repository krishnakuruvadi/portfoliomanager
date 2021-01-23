from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import pathlib
import time
import datetime
import pprint
import json
from dateutil.relativedelta import relativedelta
from selenium.webdriver.common.keys import Keys

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ', path)
    return path

def pull_zerodha(userid, passwd, pin):
    dload_files = list()
    url = 'https://console.zerodha.com/reports/tradebook'
    chrome_options = webdriver.ChromeOptions()
    dload_path = pathlib.Path(__file__).parent.parent.absolute()
    dload_path = os.path.join(dload_path, 'media')
    prefs = {'download.default_directory' : dload_path}
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(), chrome_options=chrome_options)
    driver.get(url)
    time.sleep(5)
    print(driver.current_url)
    user_id_elem = driver.find_element_by_id('userid')
    user_id_elem.send_keys(userid)
    passwd_elem = driver.find_element_by_id('password')
    passwd_elem.send_keys(passwd)
    submit_button = driver.find_element_by_xpath('//button[text()="Login "]')
    submit_button.click()
    time.sleep(3)
    pin_element = driver.find_element_by_id('pin')
    pin_element.send_keys(pin)
    submit_button = driver.find_element_by_xpath('//button[text()="Continue "]')
    submit_button.click()

    try:
        time.sleep(5)
        from_date = datetime.date(year=2013,month=4,day=1)
        while from_date < datetime.date.today():
            next_date = from_date + relativedelta(months=12)
            end_date = next_date + relativedelta(days=-1)
            if end_date > datetime.date.today():
                end_date = datetime.date.today()
            date_string = from_date.strftime("%Y-%m-%d") + " ~ " + end_date.strftime("%Y-%m-%d")
            print(date_string)
            view_element =  WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//button[text()[contains(.,"View")]]')))

            date_range = driver.find_element_by_name('date')
            date_range.clear()
            time.sleep(5)
            for _ in range(len(date_string)):
                date_range.send_keys(Keys.BACKSPACE)
            date_range.send_keys(date_string)
            time.sleep(5)
            view_element.click()
            
            WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//button[text()[contains(.,"View")]]')))
            if len(driver.find_elements_by_xpath("//a[text()[contains(.,'CSV')]]")) > 0:
                dload_elem = driver.find_element_by_xpath("//a[text()[contains(.,'CSV')]]")
                dload_elem.click()
                dload_file = os.path.join(dload_path, userid+'_tradebook_'+from_date.strftime("%Y-%m-%d") + "_to_" + end_date.strftime("%Y-%m-%d")+'.csv')
                for _ in range(10):
                    if os.path.exists(dload_file):
                        break
                    time.sleep(1)
                dload_files.append(dload_file)
            else:
                print(f'couldnt download any transactions for period {date_string}')
            from_date = next_date

        userid_elem = driver.find_element_by_xpath("//a[@class='dropdown-label user-id']")
        userid_elem.click()
        logout_elem = driver.find_element_by_xpath("//a[text()[contains(.,'Logout')]]")
        logout_elem.click()
        time.sleep(5)
        driver.close()
        return dload_files
    except TimeoutException as t:
        print('timeout waiting', t)
        driver.close()
    except Exception as ex:
        print('Exception during processing', ex)
        driver.close()
        return None
