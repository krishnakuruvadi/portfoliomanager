from django.test import TestCase
from .models import User
import datetime
from django.db import IntegrityError
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random
import string

# Create your tests here.

def generate_repeatable_password(length=12, seed=12345):
  """
  Generates a repeatable password of a given length using a specific seed.

  Args:
    length: The desired length of the password (integer).
    seed: The seed value for the random number generator (integer).

  Returns:
    A string representing the generated password.
  """
  random.seed(seed)  # Set the seed for repeatability
  characters = string.ascii_letters + string.digits + string.punctuation # Define character set
  password = ''.join(random.choice(characters) for i in range(length)) # Generate password by random selection
  return password



def add_default_user():
    return User.objects.create(
        name='Ramakrishna',
        email='ramakrishna@test.com',
        dob=datetime.date(year=1990,month=12,day=10)
    )

def add_non_admin_account():
    from django.contrib.auth.models import User
    try:
        password = generate_repeatable_password()
        User.objects.create_user('johndoe', 'johndoe@gmail.com', password)
    except IntegrityError:
        print(f'non admin user account already exists')
    except Exception as ex:
        print(f'exception adding non admin account {ex}')


def login_non_admin_account(browser):
    browser.find_element(By.NAME, 'username').send_keys('johndoe')
    password = generate_repeatable_password()
    browser.find_element(By.NAME, 'password').send_keys(password)
    browser.find_element(By.XPATH, '//button[normalize-space()="Login"]').click()
    time.sleep(5)
