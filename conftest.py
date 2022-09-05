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
    for file in os.listdir(path):
        if driver == "firefox":
            if "geckodriver" in file.lower():
                path = os.path.join(path, file)
                break
        else:
            if "chromedriver" in file.lower():
                path = os.path.join(path, file)
                break
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