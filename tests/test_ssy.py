import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_ssy(row_id):
    ssys = [{
        "row_id":1,
        "user": 1,
        "number": "35200434",
        "start_dt": datetime.date(day=10, month=12, year=2021),
        "goal": 1
    },
    {
        "row_id":2,
        "user": 2,
        "number": "345654309865",
        "start_dt": datetime.date(day=13, month=1, year=2021),
        "goal": 2,
    }]
    for p in ssys:
        if p["row_id"] == row_id:
            return p
    return None


def set_prerequisites(driver):
    driver.find_element(By.XPATH, "//a[@href='/user']").click()
    i = 1
    while True:
        try:
            u = get_user(i)
            if not u:
                break
            add_new_user(driver, u)
            i += 1
        except IndexError:
            break
    driver.find_element(By.XPATH, "//a[@href='/goal']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')
    i = 1
    while True:
        try:
            g = get_goal(i)
            if not g:
                break
            add_new_goal(driver, g)
            i += 1
        except IndexError:
            break
    driver.find_element(By.XPATH, "//a[@href='/ssy']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')

def delete_ssy_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'ssy-table')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        print(f'text is {th.text}')
        if th.text == str(id):
            driver.maximize_window()
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

def add_ssy(driver, ssy):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='create']").click()

    time.sleep(3)
    driver.find_element(By.ID, "number").click()
    driver.find_element(By.ID, "number").send_keys(ssy["number"])
    driver.find_element(By.ID, "start_date").send_keys(ssy["start_dt"].strftime('%m/%d/%Y'))
    
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(ssy["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]
    select.select_by_visible_text(name)
    # select by value 
    #select.select_by_value(str(ssy["user"]))
    time.sleep(3)
    select2 = Select(driver.find_element(By.ID, 'id_goal'))
    g = get_goal(ssy["goal"])
    select2.select_by_visible_text(g["name"])
    # select by value 
    #select2.select_by_value(str(ssy["goal"]))
    
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)

@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_Ssy:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_ssy()
        self.add_another_ssy()
        self.delete_ssys()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'ssy-table')
        assert count == 0
    
    def add_new_ssy(self):
        e = get_ssy(1)
        add_ssy(self.driver,  e)
        count, _ = get_rows_of_table(self.driver, 'ssy-table')
        assert count == 1
    
    def add_another_ssy(self):
        e = get_ssy(2)
        add_ssy(self.driver,  e)
        count, _ = get_rows_of_table(self.driver, 'ssy-table')
        assert count == 2
    
    def delete_ssys(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'ssy-table')
        assert count == expected_count
        delete_ssy_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'ssy-table')
        assert count == expected_count-1
        # instead of deleting the remaining ssy, delete its user and make sure that the ssy is gone
        # when user is deleted
        remaining_ssy = get_ssy(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_ssy['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/ssy']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'ssy-table')
        assert count == 0
        