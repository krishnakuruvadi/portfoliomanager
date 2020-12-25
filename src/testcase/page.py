from locator import *
from element import BasePageElement, BasePageSelectElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
from bs4 import BeautifulSoup


class BasePage(object):
    def __init__(self, driver):
        self.driver = driver

class FDAddPage(BasePage):
    num_element = BasePageElement(*FDAddPageLocator.NUMBER_INPUT)
    bank_element = BasePageElement(*FDAddPageLocator.BANK_NAME_INPUT)
    start_date_element = BasePageElement(*FDAddPageLocator.START_DATE_INPUT)
    user_element = BasePageSelectElement(*FDAddPageLocator.USER_INPUT)
    principal_element = BasePageElement(*FDAddPageLocator.PRINCIPAL_INPUT)
    roi_element = BasePageElement(*FDAddPageLocator.ROI_INPUT)
    time_period_element = BasePageElement(*FDAddPageLocator.TIME_PERIOD_INPUT)

    def is_title_matches(self):
        return "Add Fixed Deposit" in self.driver.page_source
    
    def add_new(self):
        time.sleep(5)
        
        calculate_button = self.driver.find_element(*FDAddPageLocator.CALCULATE_BUTTON)
        calculate_button.click()

        submit_button = self.driver.find_element(*FDAddPageLocator.SUBMIT_BUTTON)
        submit_button.click()

class FDListPage(BasePage):
    num_element = BasePageElement(*FDAddPageLocator.NUMBER_INPUT)
    bank_element = BasePageElement(*FDAddPageLocator.BANK_NAME_INPUT)
    start_date_element = BasePageElement(*FDAddPageLocator.START_DATE_INPUT)
    user_element = BasePageSelectElement(*FDAddPageLocator.USER_INPUT)
    principal_element = BasePageElement(*FDAddPageLocator.PRINCIPAL_INPUT)
    roi_element = BasePageElement(*FDAddPageLocator.ROI_INPUT)
    time_period_element = BasePageElement(*FDAddPageLocator.TIME_PERIOD_INPUT)

    def is_title_matches(self):
        return "Add Fixed Deposit" in self.driver.page_source
    
    def get_link_to_delete(self, fd_name):
        row = self.get_variables_col_values(*FDListPageLocator.FD_TABLE, fd_name)
        if row:
            cols = row.find_elements(By.TAG_NAME, "td")
            #for i, col in enumerate(cols):
            #    print(i, col.text)
            last_col = cols[len(cols)-1]
            #print(dir(last_col))
            html_code = last_col.get_attribute("innerHTML")
            soup = BeautifulSoup(html_code)
            for a in soup.findAll('a'):
                #print(a)
                print('href', a['href'])
                if 'delete' in a['href']:
                    return a['href']
        print(row)

    def get_variables_col_values(self, typ, value, search):
        try:
            #WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME,'td')))
            table_id = self.driver.find_element(typ, value)
            #time.sleep(10)
            rows = table_id.find_elements(By.TAG_NAME, "tr")
            print("Rows length", len(rows))
            for row in rows:
                # Get the columns
                #print("cols length", len(row.find_elements(By.TAG_NAME, "td")))
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) > 0: # This is the Name column                print "col_name.text = "
                    for col in cols:
                        #print(col.text)
                        if col.text == search:
                            return row
        except Exception as e:
            print(e)
            return False
