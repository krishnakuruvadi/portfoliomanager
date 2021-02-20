
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
from tasks.tasks import add_mf_transactions

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ', path)
    return path


def pull_kuvera(user, email, passwd, pull_user_name):
    url = 'https://kuvera.in/reports/transactions'
    chrome_options = webdriver.ChromeOptions()
    dload_path = pathlib.Path(__file__).parent.parent.absolute()
    dload_path = os.path.join(dload_path, 'media')

    prefs = {'download.default_directory' : dload_path}
    dload_file = os.path.join(dload_path,'transactions2.csv')
    if os.path.exists(dload_file):
        os.remove(dload_file)
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(), chrome_options=chrome_options)
    driver.get(url)
    time.sleep(5)
    try:
        email_elem = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "email")))
        #email_elem = driver.find_element_by_id('email')
        email_elem.send_keys(email)
        passwd_elem = driver.find_element_by_id('password')
        passwd_elem.send_keys(passwd)
        submit_button = driver.find_element_by_xpath('//button[text()="LOGIN"]')
        submit_button.click()
        time.sleep(10)
        user_cont = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'username-container')]")))
        user_cont.click()
        time.sleep(3)
        user_name_div = driver.find_element_by_xpath("//div[contains(@class,'b-nav-dropdown__user__name')]")
        if user_name_div.text != pull_user_name:
            user_found = False
            span_elems = driver.find_elements_by_xpath("//span[contains(@class,'b-nav-dropdown__account__subtext')]")
            for span_elem in span_elems:
                if span_elem.text == pull_user_name:
                    span_elem.click()
                    time.sleep(5)
                    user_found = True
            if not user_found:
                print(f'user {pull_user_name} not found')
                return None
        else:
            user_name_div.click()
        print(f'user {pull_user_name} found')
        time.sleep(5)
        dload = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//img[contains(@src,'download.svg')]")))
        time.sleep(5)
        dload = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//img[contains(@src,'download.svg')]")))
        dload.click()
        for i in range(10):
            if os.path.exists(dload_file):
                break
            time.sleep(1)
        add_mf_transactions('KUVERA', user, dload_file)
        user_cont = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'username-container')]")))
        user_cont.click()
        time.sleep(3)
        logout = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Logout']")))
        logout.click()
        time.sleep(3)
        driver.quit()
        return None
    except TimeoutException as t:
        print('timeout waiting', t)
        driver.quit()
    except Exception as ex:
        print('Exception during processing', ex)
        driver.quit()
        return None
