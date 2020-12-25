from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

class BasePageElement(object):
    def __init__(self, typ, locator):
        self.typ = typ
        self.locator = locator

    def __set__(self, obj, value):
        print('inside set')
        driver = obj.driver
        WebDriverWait(driver, 100).until(
            lambda driver: driver.find_element(self.typ, self.locator))
        driver.find_element(self.typ, self.locator).clear()
        driver.find_element(self.typ, self.locator).send_keys(value)

    def __get__(self, obj, owner):
        print('inside get')
        driver = obj.driver
        WebDriverWait(driver, 100).until(
            lambda driver: driver.find_element(self.typ, self.locator))
        element = driver.find_element(self.typ, self.locator)
        return element.get_attribute("value")

class BasePageSelectElement(object):
    def __init__(self, typ, locator):
        self.typ = typ
        self.locator = locator

    def __set__(self, obj, value):
        print('inside set')
        driver = obj.driver
        WebDriverWait(driver, 100).until(
            lambda driver: driver.find_element(self.typ, self.locator))
        #driver.find_element(self.typ, self.locator).clear()
        #driver.find_element(self.typ, self.locator).send_keys(value)
        select = Select(driver.find_element(self.typ, self.locator))
        select.select_by_visible_text(value)
        #for option in :
        #    if option.text == value:
        #        option.click() # select() in earlier versions of webdriver
        #        break

    def __get__(self, obj, owner):
        print('inside get')
        driver = obj.driver
        WebDriverWait(driver, 100).until(
            lambda driver: driver.find_element(self.typ, self.locator))
        element = driver.find_element(self.typ, self.locator)
        return element.get_attribute("value")