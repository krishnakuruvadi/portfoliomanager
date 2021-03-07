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
        driver.get(url+'logout')
        time.sleep(5)
        driver.quit()
        driver.close()
        add_mf_transactions('COIN ZERODHA', user, dload_file)
    except TimeoutException as t:
        print('timeout waiting', t)
        driver.close()
    except Exception as ex:
        print('Exception during processing', ex)
        driver.close()
        return None
