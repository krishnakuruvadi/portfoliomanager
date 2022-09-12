import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_crypto(row_id):
    #user is row id
    cryptos = [{
        "row_id": 1,
        "user": 1,
        "goal": 1,
        "symbol": "btc",
        "currency": "USD",
        "transactions": [{
            "trans_date": datetime.date(day=8, month=2, year=2022),
            "trans_type": "Buy",
            "price": 162.96,
            "quantity": 20,
            "broker": "CoinFoundation",
            "fees":2.99
        },
        {
            "trans_date": datetime.date(day=9, month=2, year=2022),
            "trans_type": "Receive",
            "price": 44077.378,
            "quantity": 0.00011321,
            "broker": "CoinFoundation",
            "fees": 0
        }
        ]
    },
    {
        "row_id": 2,
        "user": 2,
        "goal": 2,
        "symbol": "grt",
        "currency": "USD",
        "transactions": [{
            "trans_date": datetime.date(day=30, month=6, year=2021),
            "trans_type": "Receive",
            "price": 43.96,
            "quantity": 36,
            "broker": "Batmanhood",
            "fees": 0
        },
        {
            "trans_date": datetime.date(day=30, month=6, year=2021),
            "trans_type": "Receive",
            "price": 43.96,
            "quantity": 2.76893257,
            "broker": "Batmanhood",
            "fees": 0
        }]
    }]
    for g in cryptos:
        if g["row_id"] == row_id:
            return g
    return None

def update_crypto(driver, cryptos):
    count, rows = get_rows_of_table(driver, 'crypto-table')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        print(f'text is {th.text}')
        if th.text == str(cryptos["row_id"]):
            driver.maximize_window()
            cols = row.find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='update']").click()
            time.sleep(2)
            
            select3 = Select(driver.find_element(By.ID, 'id_goal'))
            g = get_goal(cryptos["goal"])
            print(f'selecting goal {g["name"]}')
            time.sleep(3)
            select3.select_by_visible_text(g["name"])
            time.sleep(5)
            driver.find_element(By.NAME, "submit").click()
            time.sleep(5)
            break

def add_new_crypto(driver, crypto):
    for trans in crypto["transactions"]:
        time.sleep(3)
        driver.find_element(By.XPATH, "//a[@href='add']").click()

        time.sleep(3)
        # select by visible text
        driver.find_element(By.ID, "symbol").send_keys(crypto["symbol"])
        select3 = Select(driver.find_element(By.ID, 'trans_type'))
        # select by visible text
        select3.select_by_visible_text(trans["trans_type"])
        driver.find_element(By.ID, "price").send_keys(trans["price"])

        driver.find_element(By.ID, "charges").send_keys(trans["fees"])
        driver.find_element(By.ID, "quantity").send_keys(trans["quantity"])
        driver.find_element(By.ID, "broker").send_keys(trans["broker"])
        driver.find_element(By.ID, "trans_date").send_keys(trans["trans_date"].strftime('%m/%d/%Y'))
    
        select = Select(driver.find_element(By.ID, 'id_user'))
        # select by visible text
        u = get_user(crypto["user"])
        name = u.get("short_name", "")
        if name == "":
            name = u["name"]

        select.select_by_visible_text(name)

        select2 = Select(driver.find_element(By.ID, 'id_currencies'))
        select2.select_by_visible_text(crypto["currency"])
        time.sleep(5)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(5)
        driver.find_element(By.LINK_TEXT, "Cancel").click()
        time.sleep(5)

def delete_crypto_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'crypto-table')
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
    driver.find_element(By.XPATH, "//a[@href='/crypto']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')


@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_cryptos:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_crypto()
        self.add_another_crypto()
        self.edit_cryptos()
        self.delete_cryptos()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'crypto-table')
        assert count == 0
    
    def add_new_crypto(self):
        u = get_crypto(1)
        add_new_crypto(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'crypto-table')
        assert count == 1
    
    def add_another_crypto(self):
        u = get_crypto(2)
        add_new_crypto(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'crypto-table')
        assert count == 2
    
    def edit_cryptos(self):
        u = get_crypto(1)
        update_crypto(self.driver, u)
        count, _ = get_rows_of_table(self.driver, 'crypto-table')
        assert count == 2

    def delete_cryptos(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'crypto-table')
        assert count == expected_count
        delete_crypto_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'crypto-table')
        assert count == expected_count-1
        # instead of deleting the remaining cryptos, delete its user and make sure that the cryptos is gone
        # when user is deleted
        remaining_cryptos = get_crypto(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_cryptos['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/crypto']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'crypto-table')
        assert count == 0
 