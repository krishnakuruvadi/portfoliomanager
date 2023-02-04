import pytest

from pytest_factoryboy import register
from tests.factories import UserFactory
from selenium import webdriver
import pathlib
import os

register(UserFactory)


@pytest.fixture
def new_user1(db, user_factory):
    user = user_factory.create()
    return user


def get_path_to_driver(driver):
    path = pathlib.Path(__file__).parent.absolute()
    avail_options = list()
    for file in os.listdir(path):
        if driver == "firefox":
            if "geckodriver" in file.lower():
                avail_options.append(file)
        else:
            if "chromedriver" in file.lower():
                avail_options.append(file)
    if len(avail_options) == 1:
        path = os.path.join(path, avail_options[0])
    else:
        found = False
        for ao in avail_options:
            print(f'ao')
            if ao == "geckodriver" and driver == "firefox":
                path = os.path.join(path, ao)
                found = True
                break
            elif ao == "chromedriver" and driver != "firefox":
                found = True
                path = os.path.join(path, ao)
                break
        if not found:
            path = os.path.join(path, avail_options[0])
    print('path to {driver} driver ',path)
    return path

#@pytest.fixture(params=["chrome", "firefox"], scope="class")

@pytest.fixture(params=["chrome"], scope="class")

def driver_init(request):
    path = get_path_to_driver(request.param)
    if request.param == "chrome":
        options = webdriver.ChromeOptions()
        #options.add_argument("--headless")
        web_driver = webdriver.Chrome(executable_path=path, options=options)
    if request.param == "firefox":
        options = webdriver.FirefoxOptions()
        #options.add_argument("--headless")
        web_driver = webdriver.Firefox(executable_path=path, options=options)
    request.cls.driver = web_driver
    yield
    web_driver.close()