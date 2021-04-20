from django.test import TestCase
from selenium import webdriver
from .models import Account401K, Transaction401K
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
import time
from shared.handle_get import get_path_to_chrome_driver
from users.tests import add_default_user

# Create your tests here.
class Retirement401KTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Chrome(executable_path=get_path_to_chrome_driver())
    
    def tearDown(self):
        self.browser.close()
        self.browser.quit()
    
    def get_summary_val(self, text, key):
        sp = text.split('  ')
        for s in sp:
            if key in s:
                v = s.replace(key, '')
                v = v.replace(':', '')
                return v.strip()
        return None
    
    def test_no_account(self):
        self.browser.get(self.live_server_url + reverse('retirement_401k:account-list'))
        ti = self.browser.find_element_by_xpath("//b[text()='Total Investment:']/..")
        self.assertEqual(float(self.get_summary_val(ti.text, 'Total Investment')), 0)
        self.assertEqual(float(self.get_summary_val(ti.text, 'Current Value')), 0)
        self.assertEqual(float(self.get_summary_val(ti.text, 'Gain')), 0)

        time.sleep(10)
    
    #https://stackoverflow.com/questions/2581005/django-testcase-testing-order
    def test_add_account(self):
        user = add_default_user()
        self.browser.get(self.live_server_url + reverse('retirement_401k:account-list'))
        self.browser.find_element_by_xpath("//i[@title='Add 401K Account']").click()
        time.sleep(5)
        self.browser.find_element_by_id('company').send_keys('Personal')
        self.browser.find_element_by_id('start_date').send_keys('10/01/2010')
        self.browser.find_element_by_xpath("//select[@id='id_user']/option[text()='" + user.name + "']").click()

        time.sleep(5)
        self.browser.find_element_by_id('submit').click()
        time.sleep(5)

'''
source venv/bin/activate
python manage.py test retirement_401k
'''