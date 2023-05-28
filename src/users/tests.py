from django.test import TestCase
from .models import User
import datetime
from django.db import IntegrityError
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Create your tests here.

def add_default_user():
    return User.objects.create(
        name='Ramakrishna',
        email='ramakrishna@test.com',
        dob=datetime.date(year=1990,month=12,day=10)
    )

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
