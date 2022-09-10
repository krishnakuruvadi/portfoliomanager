import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_fd(row_id):
    fds = [{
        "row_id":1,
        "user": 1,
        "number": "35200434456",
        "start_dt": datetime.date(day=10, month=12, year=2021),
        "bank_name": "Arise Global",
        "principal": 5000,
        "roi": 5.3,
        "time_period": 560,
        "goal": 1
    },
    {
        "row_id":2,
        "user": 2,
        "number": "45654309865",
        "start_dt": datetime.date(day=13, month=1, year=2021),
        "bank_name": "GASP",
        "principal": 35000,
        "roi": 5.9,
        "time_period": 960,
        "goal": 2,
    }]
    for f in fds:
        if f["row_id"] == row_id:
            return f
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
    driver.find_element(By.XPATH, "//a[@href='/fixed-deposit']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')

def delete_fd_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'fixed_deposits')
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

def add_fd(driver, fd):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='create']").click()

    time.sleep(3)
    driver.find_element(By.ID, "number").click()
    driver.find_element(By.ID, "number").send_keys(fd["number"])
    driver.find_element(By.ID, "bank_name").click()
    driver.find_element(By.ID, "bank_name").send_keys(fd["bank_name"])
    driver.find_element(By.ID, "principal").click()
    driver.find_element(By.ID, "principal").send_keys(fd["principal"])
    driver.find_element(By.ID, "roi").click()
    driver.find_element(By.ID, "roi").send_keys(fd["roi"])
    driver.find_element(By.ID, "time_period_days").click()
    driver.find_element(By.ID, "time_period_days").send_keys(fd["time_period"])
    driver.find_element(By.ID, "start_date").send_keys(fd["start_dt"].strftime('%m/%d/%Y'))
    
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(fd["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]
    select.select_by_visible_text(name)
    # select by value 
    #select.select_by_value(str(fd["user"]))
    time.sleep(3)
    select2 = Select(driver.find_element(By.ID, 'id_goal'))
    g = get_goal(fd["goal"])
    select2.select_by_visible_text(g["name"])
    # select by value 
    #select2.select_by_value(str(fd["goal"]))
    driver.find_element(By.NAME, "calculate").click()
    time.sleep(5)

    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)

@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_Fd:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_fd()
        self.add_another_fd()
        self.delete_fds()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'fixed_deposits')
        assert count == 0
    
    def add_new_fd(self):
        e = get_fd(1)
        add_fd(self.driver,  e)
        count, _ = get_rows_of_table(self.driver, 'fixed_deposits')
        assert count == 1
    
    def add_another_fd(self):
        e = get_fd(2)
        add_fd(self.driver,  e)
        count, _ = get_rows_of_table(self.driver, 'fixed_deposits')
        assert count == 2
    
    def delete_fds(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'fixed_deposits')
        assert count == expected_count
        delete_fd_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'fixed_deposits')
        time.sleep(5)
        assert count == expected_count-1
        # instead of deleting the remaining fd, delete its user and make sure that the fd is gone
        # when user is deleted
        remaining_fd = get_fd(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_fd['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/fixed-deposit']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'fixed_deposits')
        time.sleep(5)
        assert count == 0
        