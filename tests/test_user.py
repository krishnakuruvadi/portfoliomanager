import pytest
import time
import datetime
from .utils import * 
from selenium.webdriver.common.by import By


def add_new_user(driver, name, short_name, dob):
    #driver.get(("%s%s" % (live_server.url, "/user/")))
    driver.find_element(By.XPATH, "//a[@href='create']").click()

    time.sleep(5)
    driver.find_element(By.ID, "name").click()
    driver.find_element(By.ID, "name").send_keys(name)
    driver.find_element(By.ID, "short-name").send_keys(short_name)
    
    driver.find_element(By.ID, "dob").send_keys(dob.strftime('%m/%d/%Y'))
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)


@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_User:
    def test_open_url(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'user-table')
        assert count == 0
    
    def test_add_new_user(self):
        add_new_user(self.driver,  "Andrew Kal", "Akal", datetime.date(day=2, month=10, year=1993))
        count, _ = get_rows_of_table(self.driver, 'user-table')
        assert count == 1
    
    def test_add_another_user(self):
        add_new_user(self.driver,  "Ching Hao", "Chao", datetime.date(day=2, month=10, year=1993))
        count, _ = get_rows_of_table(self.driver, 'user-table')
        assert count == 2

    def test_new_user_detail(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'user-table')
        assert count == expected_count
        cols = rows[0].find_elements(By.TAG_NAME, 'td')
        cols[0].find_element(By.TAG_NAME, "a").click()
        time.sleep(2)
        print(self.driver.current_url)
        crumb, parts = get_navigation_breadcrumb(self.driver)
        time.sleep(5)
        assert len(parts) == 2
        parts[0].click()
        time.sleep(2)

    def test_delete_users(self):
        expected_count = 2
        while True:
            count, rows = get_rows_of_table(self.driver, 'user-table')
            assert count == expected_count
            if count == 0:
                break
            
            cols = rows[0].find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='delete']").click()
            time.sleep(2)
            obj = self.driver.switch_to.alert

            #Retrieve the message on the Alert window
            msg=obj.text
            print ("Alert shows following message: "+ msg )

            time.sleep(2)

            #use the accept() method to accept the alert
            obj.accept()
            
            expected_count -= 1
            time.sleep(2)
