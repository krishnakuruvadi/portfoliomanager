import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import datetime
import time
from .utils import *
from .test_user import get_user, add_new_user, delete_user
from .test_goals import get_goal, add_new_goal


def get_account(row_id):
    #user and goal are row_ids
    accounts = [{
        "row_id":1,
        "user": 1,
        "number": "00000123211",
        "acc_type": "Savings",
        "bank_name": "The .001 % Interest Bank",
        "start_dt": datetime.date(day=10, month=1, year=2022),
        "currency": 'USD',
        "goal": 1,
        "transactions": [
            {
                "transaction_date": datetime.date(day=19, month=1, year=2022),
                "transaction_type": "Credit",
                "sub_trans_type": "Salary/Payment",
                "transaction_amount": 1200.25,
                "description": "Peanuts post tax"
            },
            {
                "transaction_date": datetime.date(day=21, month=1, year=2021),
                "transaction_type": "Debit",
                "sub_trans_type": "Shopping",
                "transaction_amount": 130.5,
                "description": "ImmiCart (with inflated prices) delivery extra"
            },
            {
                "transaction_date": datetime.date(day=1, month=2, year=2022),
                "transaction_type": "Debit",
                "sub_trans_type": "Rent",
                "transaction_amount": 1100,
                "description": "Half your take home"
            }
        ]
    },
    {
        "row_id":2,
        "user": 2,
        "number": "00000123211",
        "acc_type": "Checking",
        "bank_name": "Taxpayers Will Bail Me Out Bank",
        "start_dt": datetime.date(day=1, month=1, year=2021),
        "currency": 'USD',
        "goal": 2,
        "transactions": [
            {
                "transaction_date": datetime.date(day=13, month=1, year=2021),
                "transaction_type": "Credit",
                "sub_trans_type": "Salary/Payment",
                "transaction_amount": 1300.5,
                "description": "Peanuts post tax"
            },
            {
                "transaction_date": datetime.date(day=21, month=1, year=2021),
                "transaction_type": "Debit",
                "sub_trans_type": "Shopping",
                "transaction_amount": 13.5,
                "description": "BullsEye Store"
            },
            {
                "transaction_date": datetime.date(day=25, month=1, year=2021),
                "transaction_type": "Debit",
                "sub_trans_type": "Utility",
                "transaction_amount": 15.5,
                "description": "Village by Coffee-Mobile"
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
    driver.find_element(By.XPATH, "//a[@href='/bankaccounts']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')

def delete_account_with_row_id(driver, id):
    count, rows = get_rows_of_table(driver, 'bank_accounts')
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

def add_account(driver, account):
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='add']").click()

    time.sleep(3)
    driver.find_element(By.ID, "bank_name").click()
    driver.find_element(By.ID, "bank_name").send_keys(account["bank_name"])
    driver.find_element(By.ID, "number").send_keys(account["number"])
    driver.find_element(By.ID, "start_date").send_keys(account["start_dt"].strftime('%m/%d/%Y'))
    
    select = Select(driver.find_element(By.ID, 'id_user'))
    # select by visible text
    u = get_user(account["user"])
    name = u.get("short_name", "")
    if name == "":
        name = u["name"]
    print(f'selecting user {name}')
    select.select_by_visible_text(name)

    select2 = Select(driver.find_element(By.ID, 'id_goal'))
    g = get_goal(account["goal"])
    print(f'selecting goal {g["name"]}')
    time.sleep(5)
    select2.select_by_visible_text(g["name"])

    select3 = Select(driver.find_element(By.ID, 'id_acc_type'))
    select3.select_by_visible_text(account["acc_type"])

    select4 = Select(driver.find_element(By.ID, 'id_currencies'))
    select4.select_by_visible_text(account["currency"])


    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)
    driver.find_element(By.LINK_TEXT, "Cancel").click()
    time.sleep(5)
    driver.maximize_window()
    count, rows = get_rows_of_table(driver, 'bank_accounts')
    for row in rows:
        th = row.find_element(By.TAG_NAME, 'th')
        print(f'text is {th.text}')
        if th.text == str(account["row_id"]):
            driver.maximize_window()
            cols = row.find_elements(By.TAG_NAME, 'td')
            cols[len(cols)-1].find_element(By.CSS_SELECTOR, "a[href*='transactions']").click()
            time.sleep(2)
            for trans in account["transactions"]:
                driver.find_element(By.XPATH,  "//a[contains(@href, 'add_transaction')]").click()

                time.sleep(2)
                driver.find_element(By.ID, "trans_date").send_keys(trans["transaction_date"].strftime('%m/%d/%Y'))
                driver.find_element(By.ID, "trans_amount").send_keys(trans["transaction_amount"])
                driver.find_element(By.NAME, "description").send_keys(trans["description"])

                select5 = Select(driver.find_element(By.ID, 'id_tran_type'))
                select5.select_by_visible_text(trans["transaction_type"])

                select6 = Select(driver.find_element(By.ID, 'id_tran_sub_type'))
                select6.select_by_visible_text(trans["sub_trans_type"])
                time.sleep(3)
                driver.find_element(By.NAME, "submit").click()
                time.sleep(3)
                driver.find_element(By.LINK_TEXT, "Cancel").click()
                time.sleep(3)
            count, rows = get_rows_of_table(driver, 'transactions-table')
            assert count == len(account["transactions"])
            driver.find_element(By.XPATH, "//a[@href='/bankaccounts']").click()
            time.sleep(3)
            break


@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_BankAccount:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/user/")))
        self.open_url()
        self.add_new_account()
        self.add_another_account()
        self.delete_accounts()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        count, _ = get_rows_of_table(self.driver, 'bank_accounts')
        assert count == 0
    
    def add_new_account(self):
        e = get_account(1)
        add_account(self.driver, e)
        count, _ = get_rows_of_table(self.driver, 'bank_accounts')
        assert count == 1
    
    def add_another_account(self):
        e = get_account(2)
        add_account(self.driver, e)
        count, _ = get_rows_of_table(self.driver, 'bank_accounts')
        assert count == 2
    
    def delete_accounts(self):
        expected_count = 2
        count, rows = get_rows_of_table(self.driver, 'bank_accounts')
        assert count == expected_count
        delete_account_with_row_id(self.driver, 1)
        count, rows = get_rows_of_table(self.driver, 'bank_accounts')
        assert count == expected_count-1
        # instead of deleting the remaining account, delete its user and make sure that the account is gone
        # when user is deleted
        remaining_acc = get_account(2)
        self.driver.find_element(By.XPATH, "//a[@href='/user']").click()
        time.sleep(3)
        delete_user(self.driver, remaining_acc['user'])
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//a[@href='/bankaccounts']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(self.driver, 'bank_accounts')
        assert count == 0
        