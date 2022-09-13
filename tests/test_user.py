import pytest
import time
import datetime
from .utils import * 
from selenium.webdriver.common.by import By

def get_user(row_id):
    users = [{
        "row_id": 1,
        "name": "Andrew Kal",
        #"dob": datetime.date(day=2, month=10, year=1993),
        "short_name": "Akal",
        "email": "andrew@akal.com"
    },
    {
        "row_id": 2,
        "name": "Ching Hao",
        "short_name": "Chao",
        "dob": datetime.date(day=12, month=9, year=1994)
    }]
    for u in users:
        if u["row_id"] == row_id:
            return u
    return None
    

def add_new_user(driver, user):
    #driver.get(("%s%s" % (live_server.url, "/user/")))
    driver.find_element(By.XPATH, "//a[@href='create']").click()

    time.sleep(5)
    driver.find_element(By.ID, "name").click()
    driver.find_element(By.ID, "name").send_keys(user["name"])
    driver.find_element(By.ID, "short-name").send_keys(user["short_name"])
    
    if 'dob' in user:
        driver.find_element(By.ID, "dob").send_keys(user["dob"].strftime('%m/%d/%Y'))
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)

def delete_user(driver, row_id):
    count, rows = get_rows_of_table(driver, 'user-table')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        if th.text == str(row_id):
            cols = row.find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='delete']").click()
            time.sleep(2)
            obj = driver.switch_to.alert
            #Retrieve the message on the Alert window
            msg=obj.text
            print ("Alert shows following message: "+ msg )

            time.sleep(2)

            #use the accept() method to accept the alert
            obj.accept()
            break

@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_User:
    def test_open_url(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'user-table')
        assert count == 0
    
    def test_add_new_user(self):
        u = get_user(1)
        add_new_user(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'user-table')
        assert count == 1
    
    def test_add_another_user(self):
        u = get_user(2)
        add_new_user(self.driver,  u)
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
    
    def test_user_edit(self):
        count, rows = get_rows_of_table(self.driver, 'user-table')
        u = get_user(1)
        for row in rows:
            th = rows[0].find_element(By.TAG_NAME, 'th')
            if th.text == "1":
                cols = row.find_elements(By.TAG_NAME, 'td')
                cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='update']").click()
                time.sleep(2)
                self.driver.find_element(By.ID, "email").send_keys(u["email"])
                self.driver.find_element(By.NAME, "submit").click()
                time.sleep(5)
                self.driver.find_element(By.LINK_TEXT, "Cancel").click()
                break
        time.sleep(5)

    def test_delete_users(self):
        expected_count = 2
        while True:
            count, rows = get_rows_of_table(self.driver, 'user-table')
            assert count == expected_count
            if count == 0:
                break
            
            delete_user(self.driver, expected_count)
            
            expected_count -= 1
            time.sleep(2)
            print('deleted a user')
