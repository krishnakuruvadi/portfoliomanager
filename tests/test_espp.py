import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_espp(row_id):
    #user is row id
    espps = [{
        "row_id": 1,
        "user": 1,
        "goal": 1,
        "exchange": "NASDAQ",
        "symbol":"AAPL",
        "purchase_dt": datetime.date(day=31, month=12, year=2021),
        "subscription_fmv": 162.96,
        "purchase_fmv": 179.37,
        "purchase_price": 152.15,
        "shares_purchased": 20
    },
    {
        "row_id": 2,
        "user": 2,
        "goal": 2,
        "exchange": "NASDAQ",
        "symbol":"CSCO",
        "purchase_dt": datetime.date(day=30, month=6, year=2021),
        "subscription_fmv": 43.96,
        "purchase_fmv": 53.00,
        "purchase_price": 37.36,
        "shares_purchased": 36
    }]
    for g in espps:
        if g["row_id"] == row_id:
            return g
    return None

def update_espp(driver, espp):
    count, rows = get_rows_of_table(driver, 'espp-table')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        print(f'text is {th.text}')
        if th.text == str(espp["row_id"]):
            driver.maximize_window()
            cols = row.find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='update']").click()
            time.sleep(2)
            driver.find_element(By.ID, "id_subscription_fmv").clear()
            f = round(espp["subscription_fmv"]+0.4, 2)
            driver.find_element(By.ID, "id_subscription_fmv").send_keys(f)
            driver.find_element(By.ID, "id_purchase_fmv").clear()
            pf = round(espp["purchase_fmv"]+0.3, 2)
            driver.find_element(By.ID, "id_purchase_fmv").send_keys(pf)
            driver.find_element(By.ID, "id_purchase_price").clear()
            pp = round(espp["purchase_price"]+0.05, 2)
            driver.find_element(By.ID, "id_purchase_price").send_keys(pp)
            time.sleep(5)
            driver.find_element(By.NAME, "submit").click()
            time.sleep(5)
            driver.find_element(By.LINK_TEXT, "Cancel").click()
            time.sleep(5)
            driver.find_element(By.XPATH, "//a[@href='/espp']").click()
            time.sleep(5)
            print(f'current url is {driver.current_url}')
            break

def add_new_espp(driver, espp):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='create']").click()

    time.sleep(3)
    driver.find_element(By.ID, "id_symbol").click()
    driver.find_element(By.ID, "id_symbol").send_keys(espp["symbol"])
    driver.find_element(By.ID, "id_subscription_fmv").click()
    driver.find_element(By.ID, "id_subscription_fmv").send_keys(espp["subscription_fmv"])
    driver.find_element(By.ID, "id_purchase_fmv").click()
    driver.find_element(By.ID, "id_purchase_fmv").send_keys(espp["purchase_fmv"])
    driver.find_element(By.ID, "id_purchase_price").click()
    driver.find_element(By.ID, "id_purchase_price").send_keys(espp["purchase_price"])
    driver.find_element(By.ID, "id_shares_purchased").click()
    driver.find_element(By.ID, "id_shares_purchased").send_keys(espp["shares_purchased"])
    driver.find_element(By.ID, "id_purchase_date").send_keys(espp["purchase_dt"].strftime('%m/%d/%Y'))
   
    
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(espp["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]
    select.select_by_visible_text(name)
    select2 = Select(driver.find_element(By.ID, 'id_exchange'))
    # select by visible text
    select2.select_by_visible_text(espp["exchange"])

    select3 = Select(driver.find_element(By.ID, 'id_goal'))
    g = get_goal(espp["goal"])
    print(f'selecting goal {g["name"]}')
    time.sleep(3)
    select3.select_by_visible_text(g["name"])

    # select by value 
    #select.select_by_value(str(espp["user"]))
    driver.find_element(By.ID, "id_forex_fetch").click()
    time.sleep(5)
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)

def delete_espp_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'espp-table')
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
    driver.find_element(By.XPATH, "//a[@href='/espp']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')


@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_Espp:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_espp()
        self.add_another_espp()
        self.edit_espp()
        self.delete_espps()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'espp-table')
        assert count == 0
    
    def add_new_espp(self):
        u = get_espp(1)
        add_new_espp(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'espp-table')
        assert count == 1
    
    def add_another_espp(self):
        u = get_espp(2)
        add_new_espp(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'espp-table')
        assert count == 2
    
    def edit_espp(self):
        u = get_espp(1)
        update_espp(self.driver, u)
        count, _ = get_rows_of_table(self.driver, 'espp-table')
        assert count == 2

    def delete_espps(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'espp-table')
        assert count == expected_count
        delete_espp_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'espp-table')
        assert count == expected_count-1
        # instead of deleting the remaining espp, delete its user and make sure that the espp is gone
        # when user is deleted
        remaining_espp = get_espp(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_espp['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/espp']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'espp-table')
        assert count == 0
 