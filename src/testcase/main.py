import unittest
from selenium import webdriver
import os
import pathlib
import time
import page
from selenium.webdriver.common.by import By

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    avail_options = list()
    for file in os.listdir(path):    
        if "chromedriver" in file.lower():
            avail_options.append(file)
    if len(avail_options) == 1:
        path = os.path.join(path, avail_options[0])
    else:
        found = False
        for ao in avail_options:
            print(f'{ao}')
            if ao == "chromedriver":
                found = True
                path = os.path.join(path, ao)
                break
        if not found:
            path = os.path.join(path, avail_options[0])
    print('path to chrome driver ',path)
    return path

def get_base_page_website():
    return "http://127.0.0.1:8000/"

class PMFixedDeposit(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome(get_path_to_chrome_driver())
        fd_page = get_base_page_website() + 'fixed-deposit/' 
        self.driver.get(fd_page)

    def tearDown(self):
        self.driver.close()

    
    def test_add(self):
        print("test case test_add start")
        add_fd_page_url = get_base_page_website() + 'fixed-deposit/create' 
        self.driver.get(add_fd_page_url)
        addFDPage = page.FDAddPage(self.driver)
        assert addFDPage.is_title_matches()
        addFDPage.num_element = "12345678"
        addFDPage.bank_element = "HDFC Bank"
        addFDPage.start_date_element = "12/12/2020"
        addFDPage.user_element = "Krishna Kumar Kuruvadi"
        addFDPage.principal_element = 4000
        addFDPage.roi_element = 8
        addFDPage.time_period_element = 365
        addFDPage.add_new()
        print("test case test_add end")
        time.sleep(10)
    

    def test_delete(self):
        list_fd_page_url = get_base_page_website()+ 'fixed-deposit/'
        self.driver.get(list_fd_page_url)
        fd_element = self.driver.find_element(By.XPATH, "//a[contains(.,'12345678')]")
        assert(fd_element != None)
        link = fd_element.get_attribute('href')
        print('link', link)
        delete_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href,'delete')]")
        for de in delete_elements:
            print(de.get_attribute('href'))
            if link in de.get_attribute('href'):
                de.click()
        submit_element = self.driver.find_element(By.XPATH, "//input[@value='Submit']")
        submit_element.click()
        '''
        print(delete_element.get_attribute('href'))
        
        print(fd_element)
        print(dir(fd_element))     
        print(fd_element.text)
        attrs=[]
        for attr in fd_element.get_property('attributes'):
            attrs.append([attr['name'], attr['value']])
        print(attrs)
        '''

        '''
        listFDPage = page.FDListPage(self.driver)
        link = listFDPage.get_link_to_delete("12345678")
        assert(link != None)
        link = get_base_page_website()+link
        link = link.replace("//","/")
        self.driver.get(link)
        '''
        time.sleep(10)

if __name__ == "__main__":
    unittest.main()