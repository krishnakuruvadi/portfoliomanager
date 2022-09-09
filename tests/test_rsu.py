import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_rsu(row_id):
    #user and goal are row_ids
    rsus = [{
        "row_id":1,
        "user": 1,
        "id": "35200434",
        "award_dt": datetime.date(day=10, month=12, year=2021),
        "goal": 1,
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "awarded": 50
    },
    {
        "row_id":2,
        "user": 2,
        "id": "54309865",
        "award_dt": datetime.date(day=13, month=1, year=2021),
        "goal": 2,
        "exchange": "NASDAQ",
        "symbol": "CSCO",
        "awarded": 45
    }]
    for e in rsus:
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
    driver.find_element(By.XPATH, "//a[@href='/rsu']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')

def delete_rsu_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'rsu-table')
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

def add_rsu(driver, rsu):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='create']").click()

    time.sleep(3)
    driver.find_element(By.ID, "id_award_id").click()
    driver.find_element(By.ID, "id_award_id").send_keys(rsu["id"])
    driver.find_element(By.ID, "id_shares_awarded").click()
    driver.find_element(By.ID, "id_shares_awarded").send_keys(rsu["awarded"])
    driver.find_element(By.ID, "id_symbol").click()
    driver.find_element(By.ID, "id_symbol").send_keys(rsu["symbol"])
    driver.find_element(By.ID, "id_award_date").send_keys(rsu["award_dt"].strftime('%m/%d/%Y'))
    
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(rsu["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]
    print(f'selecting user {name}')
    select.select_by_visible_text(name)

    select2 = Select(driver.find_element(By.ID, 'id_goal'))
    g = get_goal(rsu["goal"])
    print(f'selecting goal {g["name"]}')
    time.sleep(5)
    select2.select_by_visible_text(g["name"])

    select3 = Select(driver.find_element(By.ID, 'id_exchange'))
    print(f'selecting exchange {rsu["exchange"]}')
    select3.select_by_visible_text(rsu["exchange"])

    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)

@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_Rsu:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_rsu()
        self.add_another_rsu()
        self.delete_rsus()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'rsu-table')
        assert count == 0
    
    def add_new_rsu(self):
        e = get_rsu(1)
        add_rsu(self.driver, e)
        count, _ = get_rows_of_table(self.driver, 'rsu-table')
        assert count == 1
    
    def add_another_rsu(self):
        e = get_rsu(2)
        add_rsu(self.driver, e)
        count, _ = get_rows_of_table(self.driver, 'rsu-table')
        assert count == 2
    
    def delete_rsus(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'rsu-table')
        assert count == expected_count
        delete_rsu_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'rsu-table')
        assert count == expected_count-1
        # instead of deleting the remaining rsu, delete its user and make sure that the rsu is gone
        # when user is deleted
        remaining_rsu = get_rsu(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_rsu['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/rsu']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'rsu-table')
        assert count == 0
        