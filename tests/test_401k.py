import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_401k(row_id):
    #user and goal are row_ids
    accounts = [{
        "row_id":1,
        "user": 1,
        "company": "Apostle Ltd",
        "start_dt": datetime.date(day=10, month=12, year=2021),
        "goal": 1,
        "transactions": [
            {
                "transaction_date": datetime.date(day=21, month=12, year=2021),
                "employee": 23.5,
                "employer":23.5,
                "units":12.34
            },
            {
                "transaction_date": datetime.date(day=5, month=1, year=2022),
                "employee": 23.5,
                "employer":23.5,
                "units":12.8
            }
        ]
    },
    {
        "row_id":2,
        "user": 2,
        "start_dt": datetime.date(day=13, month=1, year=2021),
        "goal": 2,
        "company": "Taxation Inc",
        "transactions": [
            {
                "transaction_date": datetime.date(day=21, month=1, year=2021),
                "employee": 13.5,
                "employer":13.5,
                "units":6.34
            },
            {
                "transaction_date": datetime.date(day=5, month=2, year=2021),
                "employee": 13.5,
                "employer":13.5,
                "units":6.12
            }
        ]
    }]
    for e in accounts:
        if e["row_id"] == row_id:
            return e
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
    driver.find_element(By.XPATH, "//a[@href='/retirement_401k']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')

def delete_401k_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'accounts-table')
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

def add_401k(driver, a401k):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='create']").click()

    time.sleep(3)
    driver.find_element(By.ID, "company").click()
    driver.find_element(By.ID, "company").send_keys(a401k["company"])
    driver.find_element(By.ID, "start_date").send_keys(a401k["start_dt"].strftime('%m/%d/%Y'))
    
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(a401k["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]
    print(f'selecting user {name}')
    select.select_by_visible_text(name)

    select2 = Select(driver.find_element(By.ID, 'id_goal'))
    g = get_goal(a401k["goal"])
    print(f'selecting goal {g["name"]}')
    time.sleep(5)
    select2.select_by_visible_text(g["name"])

    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)
    driver.maximize_window()
    count, rows = get_rows_of_table(driver, 'accounts-table')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        print(f'text is {th.text}')
        if th.text == str(a401k["row_id"]):
            driver.maximize_window()
            cols = row.find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='transactions']").click()
            time.sleep(2)
            for trans in a401k["transactions"]:
                #driver.find_element(By.XPATH, "//a[href*='add-transaction']").click()
                #driver.find_element(By.PARTIAL_LINK_TEXT, "add-transaction").click()
                driver.find_element(By.XPATH,  "//a[contains(@href, 'add-transaction')]").click()

                time.sleep(2)
                driver.find_element(By.ID, "trans_date").send_keys(trans["transaction_date"].strftime('%m/%d/%Y'))
                driver.find_element(By.ID, "employee_contribution").send_keys(trans["employee"])
                driver.find_element(By.ID, "employer_contribution").send_keys(trans["employer"])
                driver.find_element(By.ID, "units").send_keys(trans["units"])
                driver.find_element(By.NAME, "submit").click()
                time.sleep(3)
                driver.find_element(By.LINK_TEXT, "Cancel").click()
                time.sleep(3)
            count, rows = get_rows_of_table(driver, 'trans-table')
            assert count == len(a401k["transactions"])
            driver.find_element(By.XPATH, "//a[@href='/retirement_401k']").click()
            time.sleep(3)
            break


@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_401k:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_401k()
        self.add_another_401k()
        self.delete_401ks()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'accounts-table')
        assert count == 0
    
    def add_new_401k(self):
        e = get_401k(1)
        add_401k(self.driver, e)
        count, _ = get_rows_of_table(self.driver, 'accounts-table')
        assert count == 1
    
    def add_another_401k(self):
        e = get_401k(2)
        add_401k(self.driver, e)
        count, _ = get_rows_of_table(self.driver, 'accounts-table')
        assert count == 2
    
    def delete_401ks(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'accounts-table')
        assert count == expected_count
        delete_401k_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'accounts-table')
        assert count == expected_count-1
        # instead of deleting the remaining 401k, delete its user and make sure that the 401k is gone
        # when user is deleted
        remaining_acc = get_401k(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_acc['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/retirement_401k']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'accounts-table')
        assert count == 0
        