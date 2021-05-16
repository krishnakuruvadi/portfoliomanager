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
import re
from alerts.alert_helper import create_alert, Severity


def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ', path)
    return path

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
            date_range = driver.find_element_by_name('date')
            date_range.clear()
            time.sleep(5)
            for _ in range(len(date_string)):
                date_range.send_keys(Keys.BACKSPACE)
            date_range.send_keys(date_string)
            time.sleep(5)
            view_element.click()
            
            #WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//button[text()[contains(.,"View")]]')))
            WebDriverWait(driver,60).until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @class="btn-blue"]')))
            if len(driver.find_elements_by_xpath("//a[text()[contains(.,'CSV')]]")) > 0:
                dload_elem = driver.find_element_by_xpath("//a[text()[contains(.,'CSV')]]")
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
                            severity=Severity.error
                        )
                
            else:
                print(f'couldnt download any transactions for period {date_string}')
                if len(driver.find_elements_by_xpath("//h3[@id='mainText' and @text='Something went wrong']")) > 0:
                    break
                if len(driver.find_elements_by_xpath("//h3[@id='mainText']"))>0:
                    h3_elem = driver.find_element_by_xpath("//h3[@id='mainText']")
                    print(f'h3 element found with text {h3_elem.text}')
                src = driver.page_source
                text_found = re.search(r'Something went wrong', src)
                if text_found:
                    break
            yr = yr -1

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
        return None
    except Exception as ex:
        print('Exception during processing', ex)
        driver.close()
        return None
