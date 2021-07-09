import os
import pathlib
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from .models import Ppf
from shared.utils import *

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ', path)
    return path

def pull_transactions(user, password, number):
    print(f'pulling transactions for {number}')
    ppf_obj = Ppf.objects.get(number=number)
    return pull_sbi_transactions(user, password, number, ppf_obj.start_date)

def pull_sbi_transactions(user, password, number, start_date):
    transactions = list()
    start_year = start_date.year
    if start_date.month < 4:
        start_year = start_year - 1
    try:
        url = 'https://retail.onlinesbi.com/retail/login.htm'
        driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver())
        driver.get(url)
        time.sleep(5)
        continue_elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'login_button')]")))
        continue_elem.click()
        time.sleep(2)
        #captcha_id = driver.find_element_by_id('refreshImgCaptcha')
        #print(captcha_id)        
        #https://retail.onlinesbi.com/retail/simpleCaptchaServ?1625812148436
        login_id = driver.find_element_by_id('username')
        login_id.send_keys(user)
        passwd_id = driver.find_element_by_id('label2')
        passwd_id.send_keys(password)
        for i in range(10):
            time.sleep(2)
            captcha_id = driver.find_element_by_id('loginCaptchaValue')
            if len(captcha_id.get_attribute("value")) > 4:
                break
        login_button = driver.find_element_by_id('Button2')
        login_button.click()
        time.sleep(5)
        #https://retail.onlinesbi.com/retail/loginsubmit.htm

        for i in range(60):
            time.sleep(2)
            sms_pass = driver.find_element_by_id('smsPassword')
            if len(sms_pass.get_attribute("value")) > 7:
                break

        continue_button = driver.find_element_by_id('btContinue')
        continue_button.click()
        time.sleep(5)

        try:
            for fy in range(start_date.year, datetime.date.today().year):
                from_date = datetime.date(year=fy,month=4,day=1)
                to_date = datetime.date(year=fy+1,month=3,day=31)
                if to_date > datetime.date.today():
                    to_date = datetime.date.today()

                try:
                    req_elem = driver.find_element_by_xpath('//a[text()[contains(.,"Request & Enquiries")]]')
                    req_elem.click()
                    time.sleep(5)
                    trans_elem = driver.find_element_by_xpath('//a[text()[contains(.,"Find Transactions")]]')
                    driver.execute_script("arguments[0].click();", trans_elem)
                    time.sleep(5)
                    tbl = driver.find_element_by_id('tblAcctd')
                    rows = tbl.find_elements_by_tag_name("tr")
                    found_col = False
                    for row in rows:
                        cols = row.find_elements_by_tag_name("td")
                        for col in cols:
                            if col.text.strip() == number:
                                print('clicking on col')
                                col.click()
                                col.click()
                                col.click()
                                found_col = True
                                break
                            else:
                                print('not the col we want. continuing')
                        if found_col:
                            break
                    from_date_str = convert_date_to_string(from_date, '%d/%m/%Y')
                    to_date_str = convert_date_to_string(to_date, '%d/%m/%Y')
                    print(f'getting transactions between {from_date_str} and {to_date_str}')
                    from_elem = driver.find_element_by_id('datepicker3')
                    from_elem.send_keys(from_date_str)
                    #from_elem.send_keys('01/04/2020')
                    to_elem = driver.find_element_by_id('datepicker4')
                    #to_elem.send_keys('31/03/2021')
                    to_elem.send_keys(to_date_str)
                    get_elem = driver.find_element_by_name('submit')
                    get_elem.click()
                    time.sleep(5)
                    if 'There are no financial transactions performed' in driver.page_source:
                        pass
                    else:
                        print('getting transactions')
                        trans_table_div = driver.find_element_by_xpath('//div[contains(@class,"table_scrl")]')
                        trans_table = trans_table_div.find_element_by_tag_name('table')
                        for tbody in trans_table.find_elements_by_tag_name('tbody'):
                            for tr in tbody.find_elements_by_tag_name('tr'):
                                tds = tr.find_elements_by_tag_name('td')
                                if len(tds) == 4:
                                    for i in range(4):
                                        print(f'td[{str(i)}] text {tds[i].text} innerHTML {tds[i].get_attribute("innerHTML")}')
                                    trans_date = tds[0].text
                                    trans_date = trans_date[trans_date.find('(')+1:trans_date.find(')')]
                                    description = tds[1].text
                                    description = description.replace('<br>','-')
                                    description = description.replace('\n','-')
                                    debit = tds[2].text
                                    debit = debit.strip().replace(',','')
                                    debit = get_float_or_zero_from_string(debit)
                                    credit = tds[3].text
                                    credit = credit.strip().replace(',','')
                                    credit = get_float_or_zero_from_string(credit)
                                    trans = dict()
                                    trans['date'] = trans_date
                                    trans['description'] = description
                                    trans['debit'] = debit
                                    trans['credit'] = credit
                                    transactions.append(trans)
                                else:
                                    print(f'not matching length of td {str(len(tds))}')
                except Exception as ex:
                    print(f'exception while getting transactions {ex}')
        except TimeoutException as t:
            print(f'timeout waiting {t}')
        except Exception as ex:
            print(f'Exception during processing {ex}')
        time.sleep(5)
        logout_elem = driver.find_element_by_xpath("//a[contains(@class,'wpanel_logout')]")
        #wpanel_logout hidden-xs
        #logout_elem.click()
        driver.execute_script("arguments[0].click();", logout_elem)
        time.sleep(5)
        later_elem = driver.find_element_by_xpath('//button[text()[contains(.,"Maybe later")]]')
        driver.execute_script("arguments[0].click();", later_elem)
        time.sleep(5)
        driver.close()
        driver.quit()
    except Exception as ex:
        print('exception when pulling transactions from sbi')
        print(ex)
    return transactions
    
