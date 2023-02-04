from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from .models import Account401K, Transaction401K
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
import time
from shared.handle_get import get_path_to_chrome_driver
from users.tests import add_default_user
from selenium.webdriver.chrome.options import Options

# Create your tests here.
class Retirement401KTest(StaticLiveServerTestCase):
    def setUp(self):
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument("window-size=1920,1080")
        try:
            print(f'try default chrome launch with options')
            self.browser = webdriver.Chrome(options=options)
        except Exception as ex:
            print(f'exception {ex} with default chrome launch')
            options.add_argument("start-maximized")
            self.browser = webdriver.Chrome(executable_path=get_path_to_chrome_driver(), options=options)
    
    def tearDown(self):
        self.browser.close()
        self.browser.quit()
    
    def get_summary_val(self, text, key):
        sp = text.split('  ')
        for s in sp:
            if key in s:
                v = s.replace(key, '')
                v = v.replace(':', '')
                v = v.replace('$', '')
                v = v.replace('₹', '')
                return v.strip()
        return None
    
    def get_no_of_accounts(self):
        self.browser.get(self.live_server_url + reverse('retirement_401k:account-list'))

    def test_no_account(self):
        self.browser.get(self.live_server_url + reverse('retirement_401k:account-list'))
        ti = self.browser.find_element(By.XPATH, "//h6[text()='Total Investment']/..")
        self.assertEqual(float(self.get_summary_val(ti.text, 'Total Investment')), 0)
        ti = self.browser.find_element(By.XPATH, "//h6[text()='Current Value']/..")
        self.assertEqual(float(self.get_summary_val(ti.text, 'Current Value')), 0)
        ti = self.browser.find_element(By.XPATH, "//h6[text()='Gain']/..")
        self.assertEqual(float(self.get_summary_val(ti.text, 'Gain')), 0)

        time.sleep(3)
    
    #https://stackoverflow.com/questions/2581005/django-testcase-testing-order
    def test_add_account(self):
        user = add_default_user()
        self.browser.get(self.live_server_url + reverse('retirement_401k:account-list'))
        self.browser.find_element(By.XPATH, "//i[@title='Add 401K Account']").click()
        time.sleep(2)
        self.browser.find_element(By.ID, 'company').send_keys('Personal')
        self.browser.find_element(By.ID, 'start_date').send_keys('10/04/2010')
        self.browser.find_element(By.XPATH, "//select[@id='id_user']/option[text()='" + user.name + "']").click()

        time.sleep(2)
        self.browser.find_element(By.ID, 'submit').click()
        time.sleep(2)
        self.browser.get(self.live_server_url + reverse('retirement_401k:account-list'))
        accounts_table = self.browser.find_element(By.ID, 'accounts-table')
        body = accounts_table.find_elements(By.TAG_NAME, 'tbody')

        rows = body[0].find_elements(By.TAG_NAME, 'tr')
        self.assertEqual(len(rows), 1)
        columns = rows[0].find_elements(By.TAG_NAME, 'td')
        anc = columns[0].find_elements(By.TAG_NAME, 'a')
        self.assertEquals(anc[0].text, 'Personal')
        self.assertEquals(columns[1].text, 'Oct. 4, 2010')
        time.sleep(5)
        self.assertEquals(columns[2].text, 'None')
        self.assertEquals(columns[3].text, user.name)
        self.assertEquals(columns[4].text, '')
        self.assertEquals(columns[5].text, '0.00')
        self.assertEquals(columns[6].text, '0.00')
        self.assertEquals(columns[7].text, '0.00')
        self.assertEquals(columns[8].text, 'None')
        self.assertEquals(columns[9].text, '0.00')

        trans = columns[10].find_element(By.XPATH, "./a[contains(@href,'transactions')]")
        trans.click()
        time.sleep(5)
        self.assertTrue('No data available in table' in self.browser.page_source)
        time.sleep(5)
        
        

'''
source venv/bin/activate
python manage.py test retirement_401k
'''