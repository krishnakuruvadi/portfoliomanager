import pytest
from selenium.webdriver.common.by import By

import datetime
import time
from .utils import *
from alerts.models import Alert

def get_alert(alert_type):
    alerts = [{
        "type": "Action",
        "alerts": [
            {
                "time": datetime.datetime(day=19, month=1, year=2022, minute=22, hour=12),
                "summary": "Missing transactions in account 401K since 2022-01-12",
                "severity": 2,
                "content": "Missing transactions in account 401K since 2022-01-12"
            },
            {
                "time": datetime.datetime(day=21, month=1, year=2021, minute=22, hour=12),
                "summary": "FD 123456 is maturing in 3 days.",
                "severity": 4,
                "content": "Your FD 123456 is maturing in 3 days.  Renew to keep your goals on track",
            },
            {
                "time": datetime.datetime(day=1, month=2, year=2022, minute=22, hour=12),
                "summary": "Unable to pull transactions from your broker account",
                "severity": 1,
                "content": "Unable to pull transactions from your broker account.  Please check and retry."
            }
        ]
    },
    {
        "type": "Notification",
        "alerts": [
            {
                "time": datetime.datetime(day=19, month=1, year=2022, minute=22, hour=12),
                "summary": "NASDAQ HL is up by 5.09 %",
                "severity": 4,
                "content": "NASDAQ HL is up by 5.09 %"
            },
            {
                "time": datetime.datetime(day=21, month=1, year=2021, minute=22, hour=12),
                "summary": "NASDAQ CRM hit 52 Week low of 150.48",
                "severity": 4,
                "content": "NASDAQ CRM hit 52 Week low of 150.48"
            },
            {
                "time": datetime.datetime(day=1, month=2, year=2022, minute=22, hour=12),
                "summary": "BSE ASALCBR hit 52 Week high of 449.1",
                "severity": 4,
                "content": "BSE ASALCBR hit 52 Week high of 449.1"
            }
        ]
    },
    {
        "type": "Application",
        "alerts": [
            {
                "time": datetime.datetime(day=19, month=1, year=2022, minute=22, hour=12),
                "content": "Not able to find a matching Mutual Fund with the code for analysis.",
                "severity": 2,
                "summary": "Code:118589 Mutual fund not analysed"
            },
            {
                "time": datetime.datetime(day=19, month=9, year=2022, minute=22, hour=12),
                "content": "Please follow upgrade instructions to update the application.",
                "severity": 2,
                "summary": "0.1.19 New version available for update"
            },
            {
                "time": datetime.datetime(day=19, month=9, year=2022, minute=22, hour=12),
                "content": "NASDAQ:FB - Failed to get latest value",
                "severity": 2,
                "summary": "NASDAQ:FB - Failed to get latest value"
            }
        ]
    }]
    for e in alerts:
        if e["type"] == alert_type:
            return e["alerts"]
    return None


def set_prerequisites(driver):
    time.sleep(5)
    driver.find_element(By.XPATH, "//*[@id='welcomeModal']/div/div/div[3]/button").click()
    time.sleep(5)
    driver.find_element(By.XPATH, "//a[@href='/alerts']").click()
    time.sleep(3)
    print(f'current url is {driver.current_url}')


def get_meta():
    return [
        {
            "href": "#actions",
            "table": "actions-table"
        },
        {
            "href": "#notifications",
            "table": "notifications-table"
        },
        {
            "href": "#application",
            "table": "application-table"
        }
    ]

def check_alert_count(driver, expected_count):
    driver.find_element(By.XPATH, "//a[@href='/goal']").click()
    time.sleep(3)
    driver.find_element(By.XPATH, "//a[@href='/alerts']").click()
    time.sleep(3)
    meta =get_meta()
    i = 0
    for alert_tab in meta:
        hr = alert_tab["href"]
        driver.find_element(By.XPATH, f"//a[@href='{hr}']").click()
        time.sleep(3)
        count, rows = get_rows_of_table(driver, alert_tab['table'])
        assert count == expected_count[i]
        i += 1
        

def delete_alert_with_row_id(driver, id):
    time.sleep(3)
    meta =get_meta()
    for alert_tab in meta:
        hr = alert_tab["href"]
        driver.find_element(By.XPATH, f"//a[@href='{hr}']").click()
        count, rows = get_rows_of_table(driver, alert_tab['table'])
        for row in rows:
            th = row.find_element(By.TAG_NAME, 'th')
            a = th.find_element(By.TAG_NAME, 'a')
            if a.get_attribute("innerHTML").strip() == str(id):
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
        time.sleep(3)

@pytest.mark.django_db
def add_alerts():
    c = 0
    for al_type in ['Application', 'Action', 'Notification']:
        alerts = get_alert(al_type)
        for alert in alerts:
            Alert.objects.create(alert_type=al_type,
                                severity=alert["severity"],
                                 summary=alert['summary'],
                                 time=alert["time"])
            c += 1
        als = Alert.objects.count()
        assert als == c


@pytest.mark.usefixtures("driver_init")
@pytest.mark.django_db
class Test_Bankalert:
    def test_flow(self, live_server):
        self.driver.get(("%s%s" % (live_server.url, "/")))
        self.open_url()
        add_alerts()
        self.delete_alerts()

    def open_url(self):
        set_prerequisites(self.driver)
        time.sleep(5)
        check_alert_count(self.driver, [0,0,0])
    
    def delete_alerts(self):
        expected_count = 3
        while expected_count >= 0:
            check_alert_count(self.driver, [expected_count,expected_count,expected_count])
            if expected_count > 0:
                delete_alert_with_row_id(self.driver, expected_count)
            expected_count -= 1

        