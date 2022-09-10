import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_shares(row_id):
    #user is row id
    shares = [{
        "row_id": 1,
        "user": 1,
        "goal": 1,
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "trans_date": datetime.date(day=31, month=12, year=2021),
        "trans_type": "Buy",
        "price": 162.96,
        "shares_purchased": 20,
        "broker": "Swab"
    },
    {
        "row_id": 2,
        "user": 2,
        "goal": 2,
        "exchange": "NASDAQ",
        "symbol": "CSCO",
        "trans_date": datetime.date(day=30, month=6, year=2021),
        "trans_type": "Buy",
        "price": 43.96,
        "shares_purchased": 36,
        "broker": "Socks"
    }]
    for g in shares:
        if g["row_id"] == row_id:
            return g
    return None

def update_shares(driver, shares):
    count, rows = get_rows_of_table(driver, 'shares-table')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        print(f'text is {th.text}')
        if th.text == str(shares["row_id"]):
            driver.maximize_window()
            cols = row.find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='update']").click()
            time.sleep(2)
            
            select3 = Select(driver.find_element(By.ID, 'id_goal'))
            g = get_goal(shares["goal"])
            print(f'selecting goal {g["name"]}')
            time.sleep(3)
            select3.select_by_visible_text(g["name"])
            time.sleep(5)
            driver.find_element(By.NAME, "submit").click()
            time.sleep(5)
            break

def add_new_shares(driver, shares):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='add']").click()

    time.sleep(3)
    select2 = Select(driver.find_element(By.ID, 'exchange'))
    # select by visible text
    select2.select_by_visible_text(shares["exchange"])
    driver.find_element(By.ID, "symbol").send_keys(shares["symbol"])
    select3 = Select(driver.find_element(By.ID, 'trans_type'))
    # select by visible text
    select3.select_by_visible_text(shares["trans_type"])
    driver.find_element(By.ID, "price").send_keys(shares["price"])

    driver.find_element(By.ID, "quantity").send_keys(shares["shares_purchased"])
    driver.find_element(By.ID, "broker").send_keys(shares["broker"])
    driver.find_element(By.ID, "trans_date").send_keys(shares["trans_date"].strftime('%m/%d/%Y'))
   
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(shares["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]

    select.select_by_visible_text(name)

    driver.find_element(By.ID, "fetch").click()
    time.sleep(5)
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)

def delete_shares_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'shares-table')
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
    driver.find_element(By.XPATH, "//a[@href='/shares']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')


@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_Shares:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_shares()
        self.add_another_shares()
        self.edit_shares()
        self.delete_shares()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'shares-table')
        assert count == 0
    
    def add_new_shares(self):
        u = get_shares(1)
        add_new_shares(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'shares-table')
        assert count == 1
    
    def add_another_shares(self):
        u = get_shares(2)
        add_new_shares(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'shares-table')
        assert count == 2
    
    def edit_shares(self):
        u = get_shares(1)
        update_shares(self.driver, u)
        count, _ = get_rows_of_table(self.driver, 'shares-table')
        assert count == 2

    def delete_shares(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'shares-table')
        assert count == expected_count
        delete_shares_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'shares-table')
        assert count == expected_count-1
        # instead of deleting the remaining shares, delete its user and make sure that the shares is gone
        # when user is deleted
        remaining_shares = get_shares(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_shares['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/shares']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'shares-table')
        assert count == 0
 