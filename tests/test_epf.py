import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_epf(row_id):
    #user and goal are row_ids
    epfs = [{
        "row_id":1,
        "user": 1,
        "number": "APL/35/2004/34",
        "start_dt": datetime.date(day=10, month=12, year=2021),
        "goal": 1,
        "company": "Apostle Ltd",
        "contributions": [
            {
                "fy": "2021-22",
                "month": "December",
                "employee": 880,
                "employer":800,
                "interest": 10
            },
            {
                "fy": "2021-22",
                "month": "January",
                "employee": 880,
                "employer":800,
                "interest": 10.1
            },
            {
                "fy": "2021-22",
                "month": "February",
                "employee": 880,
                "employer":800,
                "interest": 10.2
            },
            {
                "fy": "2021-22",
                "month": "March",
                "employee": 880,
                "employer":800,
                "interest": 10.3
            },
            {
                "fy": "2022-23",
                "month": "April",
                "employee": 880,
                "employer":800,
                "interest": 10.4
            }
        ]
    },
    {
        "row_id":2,
        "user": 2,
        "number": "TXN/3456/543/09865",
        "start_dt": datetime.date(day=13, month=1, year=2021),
        "goal": 2,
        "company": "Taxation Inc",
        "contributions": []
    }]
    for e in epfs:
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
    driver.find_element(By.XPATH, "//a[@href='/epf']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')

def delete_epf_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'epf-table')
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

def add_epf(driver, epf):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='create']").click()

    time.sleep(3)
    driver.find_element(By.ID, "number").click()
    driver.find_element(By.ID, "number").send_keys(epf["number"])
    driver.find_element(By.ID, "company").click()
    driver.find_element(By.ID, "company").send_keys(epf["company"])
    driver.find_element(By.ID, "start_date").send_keys(epf["start_dt"].strftime('%m/%d/%Y'))
    
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(epf["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]
    print(f'selecting user {name}')
    select.select_by_visible_text(name)
    # select by value 
    #select.select_by_value(str(epf["user"]))

    select2 = Select(driver.find_element(By.ID, 'id_goal'))
    g = get_goal(epf["goal"])
    print(f'selecting goal {g["name"]}')
    time.sleep(3)
    select2.select_by_visible_text(g["name"])

    # select by value 
    #select2.select_by_value(str(epf["goal"]))
    
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)
    if len(epf["contributions"]) > 0:
        for entry in epf["contributions"]:
            print(f'new entry {entry}')
            count, rows = get_rows_of_table(driver, 'epf-table')
            for row in rows:
                th = row.find_element(By.TAG_NAME, 'th')
                print(f'text is {th.text}')
                if th.text == str(epf["row_id"]):
                    driver.maximize_window()
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='transactions']").click()
                    time.sleep(2)
                    driver.find_element(By.CSS_SELECTOR, "a[href*='add-contribution']").click()
                    time.sleep(3)
                    sel = Select(driver.find_element(By.NAME, 'fy'))
                    sel.select_by_visible_text(entry["fy"])
                    driver.find_element(By.NAME, 'fetch').click()
                    time.sleep(5)
                    m = entry['month'].lower()[0:3]
                    print(f'sending {entry["employee"]} to {m}_em')
                    driver.find_element(By.ID, f"{m}_em").send_keys(entry["employee"])
                    driver.find_element(By.ID, f"{m}_er").send_keys(entry["employer"])
                    driver.find_element(By.ID, f"{m}_int").send_keys(entry["interest"])
                    driver.find_element(By.NAME, "submit").click()
                    time.sleep(15)
                    driver.find_element(By.LINK_TEXT, "Cancel").click()
                    time.sleep(5)
                    break
            driver.find_element(By.XPATH, "//a[@href='/epf']").click()
            time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='/epf']").click()
    time.sleep(3)

@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_Epf:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_epf()
        self.add_another_epf()
        self.check_home_view()
        self.delete_epfs()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'epf-table')
        assert count == 0
    
    def add_new_epf(self):
        e = get_epf(1)
        add_epf(self.driver, e)
        count, _ = get_rows_of_table(self.driver, 'epf-table')
        assert count == 1
    
    def add_another_epf(self):
        e = get_epf(2)
        add_epf(self.driver, e)
        count, _ = get_rows_of_table(self.driver, 'epf-table')
        assert count == 2
    
    def check_home_view(self):
        self.driver.find_element(By.XPATH, "//a[@href='/']").click()
        time.sleep(5)
        self.driver.find_element(By.XPATH, "//a[@href='/epf']").click()
        time.sleep(3)
        
    def delete_epfs(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'epf-table')
        assert count == expected_count
        delete_epf_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'epf-table')
        assert count == expected_count-1
        # instead of deleting the remaining epf, delete its user and make sure that the epf is gone
        # when user is deleted
        remaining_epf = get_epf(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_epf['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/epf']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'epf-table')
        assert count == 0
        