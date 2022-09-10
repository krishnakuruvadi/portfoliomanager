import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_mf(row_id):
    #user is row id
    mf = [{
        "row_id": 1,
        "user": 1,
        "goal": 1,
        "folio": "23456543/12",
        "fund_house": "quant Mutual Fund",
        "fund": "quant Small Cap Fund - Growth Option - Direct Plan",
        "transactions": [
            {
                "trans_date": datetime.date(day=1, month=2, year=2022),
                "trans_type": "Buy",
                "price": 143.6817,
                "units": 13.9190,
                "broker": "Bill"
            }
        ]
    },
    {
        "row_id": 2,
        "user": 2,
        "goal": 2,
        "folio": "23443543/12",
        "fund_house": "UTI Mutual Fund",
        "fund": "UTI-Transpotation and Logistics  Fund-Growth Option",
        "transactions": [
            {
                "trans_date": datetime.date(day=15, month=6, year=2020),
                "trans_type": "Buy",
                "price": 79.0765,
                "units": 63.2300,
                "broker": "Enlarrge"
            }
        ]
    }]
    for g in mf:
        if g["row_id"] == row_id:
            return g
    return None

def update_mf(driver, mf):
    click_if_unchecked(driver, "show_zero_val")
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    count, rows = get_rows_of_table(driver, 'folio-table')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        print(f'text is {th.text}')
        if th.text == str(mf["row_id"]):
            driver.maximize_window()
            cols = row.find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='update']").click()
            time.sleep(2)
            
            select3 = Select(driver.find_element(By.ID, 'id_goal'))
            g = get_goal(mf["goal"])
            print(f'selecting goal {g["name"]}')
            time.sleep(3)
            select3.select_by_visible_text(g["name"])
            time.sleep(5)
            driver.find_element(By.NAME, "submit").click()
            time.sleep(5)
            driver.find_element(By.LINK_TEXT, "Cancel").click()
            time.sleep(5)
            break
    driver.find_element(By.ID, "show_zero_val").click()
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)

def add_transactions(driver, id):
    click_if_unchecked(driver, "show_zero_val")
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    count, rows = get_rows_of_table(driver, 'folio-table')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        print(f'text is {th.text}')
        if th.text == str(id):
            driver.maximize_window()
            cols = row.find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='transactions']").click()
            time.sleep(5)
            mf = get_mf(id)
            for tran in mf["transactions"]:
                driver.find_element(By.XPATH, "//a[contains(@href, 'add')]").click()
                time.sleep(3)
                select3 = Select(driver.find_element(By.ID, 'trans_type'))
                # select by visible text
                select3.select_by_visible_text(tran["trans_type"])
                driver.find_element(By.ID, "price").send_keys(tran["price"])

                driver.find_element(By.ID, "units").send_keys(tran["units"])
                driver.find_element(By.ID, "broker").send_keys(tran["broker"])
                driver.find_element(By.ID, "trans_date").send_keys(tran["trans_date"].strftime('%m/%d/%Y'))
                time.sleep(3)
                driver.find_element(By.NAME, "submit").click()
                time.sleep(5)
                driver.find_element(By.LINK_TEXT, "Cancel").click()
                time.sleep(5)
            break
    driver.find_element(By.XPATH, "//a[@href='/mutualfunds']").click()
    time.sleep(3)

def add_new_mf(driver, mf):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='add']").click()

    time.sleep(3)
    driver.find_element(By.ID, "id_folio").send_keys(mf["folio"])
    select2 = Select(driver.find_element(By.ID, 'id_fund_house'))
    # select by visible text
    select2.select_by_visible_text(mf["fund_house"])
    driver.find_element(By.ID, "id_fund").send_keys(mf["fund"])
    time.sleep(15)

    ul = driver.find_element(By.ID, "ui-id-1")
    for li in ul.find_elements(By.TAG_NAME, "li"):
        div = li.find_element(By.TAG_NAME, "div")
        if div.text == mf["fund"].replace("  ", " "):
            li.click()
            break
   
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(mf["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]

    select.select_by_visible_text(name)

    select3 = Select(driver.find_element(By.ID, 'id_goal'))
    g = get_goal(mf["goal"])
    print(f'selecting goal {g["name"]}')
    time.sleep(3)
    select3.select_by_visible_text(g["name"])

    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)
    click_if_unchecked(driver, "show_zero_val")
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)


def delete_mf_with_row_id(driver, id):
    click_if_unchecked(driver, "show_zero_val")
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    count, rows = get_rows_of_table(driver, 'folio-table')
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
    click_if_unchecked(driver, "show_zero_val")
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)

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
    driver.find_element(By.XPATH, "//a[@href='/mutualfunds']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')


@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_Mf:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_mf()
        self.add_another_mf()
        self.add_transactions()
        self.edit_mf()
        self.delete_mf()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'folio-table')
        assert count == 0
    
    def add_new_mf(self):
        u = get_mf(1)
        add_new_mf(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'folio-table')
        assert count == 1
    
    def add_another_mf(self):
        u = get_mf(2)
        add_new_mf(self.driver,  u)
        count, _ = get_rows_of_table(self.driver, 'folio-table')
        assert count == 2
    
    def edit_mf(self):
        u = get_mf(1)
        update_mf(self.driver, u)
        count, _ = get_rows_of_table(self.driver, 'folio-table')
        assert count == 2

    def delete_mf(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'folio-table')
        assert count == expected_count
        delete_mf_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'folio-table')
        assert count == expected_count-1
        # instead of deleting the remaining mf, delete its user and make sure that the mf is gone
        # when user is deleted
        remaining_mf = get_mf(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_mf['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/mutualfunds']").click()
        time.sleep(3)
        click_if_unchecked(self.driver, "show_zero_val")
        self.driver.find_element(By.NAME, "submit").click()
        time.sleep(5)
        count, rows = get_rows_of_table(self.driver, 'folio-table')
        assert count == 0
 
    def add_transactions(self):
        i = 1
        while True:
            try:
                g = get_mf(i)
                if not g:
                    break
                print(f'processing {i} add transactions')
                add_transactions(self.driver, i)
                i += 1
            except IndexError:
                break