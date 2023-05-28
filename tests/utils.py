from selenium.webdriver.common.by import By
from django.db import IntegrityError
from selenium.webdriver.common.by import By
import time

def get_rows_of_table(driver, table_id):
    path = f"//table[@id='{table_id}']/tbody/tr"
    rows = driver.find_elements(By.XPATH, path)
    if len(rows) == 1:
        cols = rows[0].find_elements(By.TAG_NAME, 'td')
        if len(cols) == 1:
            if cols[0].text == 'No data available in table':
                return 0, None

    return len(rows), rows


def get_navigation_breadcrumb(driver):
    crumb = driver.find_element(By.CLASS_NAME, "breadcrumb")
    parts = crumb.find_elements(By.TAG_NAME, "li")
    return crumb, parts


def click_if_unchecked(driver, id):
    if not driver.find_element(By.ID, id).is_selected():
        driver.find_element(By.ID, id).click()


def add_non_admin_account():
    from django.contrib.auth.models import User
    try:
        User.objects.create_user('johndoe', 'johndoe@gmail.com', 'johnpassword')
    except IntegrityError:
        print(f'non admin user account already exists')
    except Exception as ex:
        print(f'exception adding non admin account {ex}')


def login_non_admin_account(browser):
    browser.find_element(By.NAME, 'username').send_keys('johndoe')
    browser.find_element(By.NAME, 'password').send_keys('johnpassword')
    browser.find_element(By.XPATH, '//button[normalize-space()="Login"]').click()
    time.sleep(5)
    