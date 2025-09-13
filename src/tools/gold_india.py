import datetime
import requests
import bs4
from shared.utils import get_float_or_none_from_string, get_date_or_none_from_string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService


def get_latest_physical_gold_price():
    url = 'https://www.gadgets360.com/finance/gold-rate-in-india'
    # Initialize the WebDriver
    chrome_options = webdriver.ChromeOptions()

    driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
    driver.get(url)
    # Wait for the page to load completely (you can adjust the wait time as needed)
    driver.implicitly_wait(10)  # Wait for up to 10 seconds for elements to be available
    # Find the element containing the gold price (you may need to adjust the selector)
    tables = driver.find_elements(By.TAG_NAME, 'table')
    res = dict()
    for table in tables:
        try:
            # get the heading of the table using thead tag
            thead = table.find_element(By.TAG_NAME, 'thead')
            # search for 'Date' and 'Pure Gold (24K)' in the rows of thead
            if 'Date' in thead.text and 'Pure Gold (24K)' in thead.text and '22K' in thead.text:
                rows = table.find_elements(By.TAG_NAME, 'tr')
                for i, row in enumerate(rows):
                    if i == 0:
                        continue
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    dt = get_date_or_none_from_string(cols[0].text.strip(), "%d %B %Y")
                    val24k = get_float_or_none_from_string(cols[1].text.replace('₹ ', '').replace(',',''))
                    val22k = get_float_or_none_from_string(cols[2].text.replace('₹ ', '').replace(',',''))
                    if dt and val22k and val24k:
                        res[dt] = {"24K": val24k/10, "22K":val22k/10}
        except NoSuchElementException:
            continue
    driver.quit()
    if res:
        return res
    # If the above method fails, fallback to requests and BeautifulSoup
    r = requests.get(url, timeout=15, allow_redirects=True)
    if r.status_code==200:
        print("Fetched page : "+url)
        # Creating a bs4 object to store the contents of the requested page
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        h2 = soup.find_all("h2")
        for item in h2:
            #print(item.text)
            if 'Daily Gold Rate In India' in item.text:
                print(item.parent.text)
                rows = item.parent.find_all('tr')
                for i, row in enumerate(rows):
                    print(row.text)
                    if i == 0:
                        continue
                    cols = row.find_all('td')
                    dt = get_date_or_none_from_string(cols[0].text.strip(), "%d %B %Y")
                    val24k = get_float_or_none_from_string(cols[1].text.replace('₹ ', '').replace(',',''))
                    val22k = get_float_or_none_from_string(cols[2].text.replace('₹ ', '').replace(',',''))
                    if dt and val22k and val24k:
                        res = {"date":dt, "24K": val24k/10, "22K":val22k/10}
                        break
        return res
    elif r.status_code==404:
        print("Page not found")
    else:
        print("A different status code received : "+str(r.status_code))
    print('failed to get any price for latest physical gold price')
    return None   

def get_last_close_digital_gold_price():
    url = 'https://www.gadgets360.com/finance/digital-gold-price-in-india'
    # Initialize the WebDriver
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
    driver.get(url)
    # Wait for the page to load completely (you can adjust the wait time as needed)
    driver.implicitly_wait(10)  # Wait for up to 10 seconds for elements to be available
    # Find the element containing the gold price (you may need to adjust the selector)
    tables = driver.find_elements(By.TAG_NAME, 'table')
    res = dict()
    for table in tables:
        # get the heading of the table using thead tag
        thead = table.find_element(By.TAG_NAME, 'thead')
        # search for 'Date' and 'Pure Gold (24K)' in the rows of thead
        if 'Date' in thead.text and 'Price' in thead.text and 'Close' in thead.text:
            rows = table.find_elements(By.TAG_NAME, 'tr')
            for i, row in enumerate(rows):
                if i == 0:
                    continue
                cols = row.find_elements(By.TAG_NAME, 'td')
                dt = get_date_or_none_from_string(cols[0].text.strip(), "%d %B %Y")
                val24k = get_float_or_none_from_string(cols[1].text.replace('₹ ', '').replace(',',''))
                if dt and val24k:
                    res[dt] = val24k
    driver.quit()
    if res:
        return res
    r = requests.get(url, timeout=15, allow_redirects=True)
    if r.status_code==200:
        print("Fetched page : "+url)
        # Creating a bs4 object to store the contents of the requested page
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        h2 = soup.find_all("h2")
        for item in h2:
            #print(item.text)
            if 'Digital Gold Price for Last ' in item.text:
                print(item.parent.text)
                rows = item.parent.find_all('tr')
                for i, row in enumerate(rows):
                    print(row.text)
                    if i == 0:
                        continue
                    cols = row.find_all('td')
                    dt = get_date_or_none_from_string(cols[0].text.strip(), "%d %B %Y")
                    val24k = get_float_or_none_from_string(cols[1].text.replace('₹ ', '').replace(',',''))
                    if dt and val24k:
                        res[dt] = val24k
                        return res
    elif r.status_code==404:
        print("Page not found")
    else:
        print("A different status code received : "+str(r.status_code))
    print('failed to get any price for digital gold price last close')
    return None

'''
def get_latest_digital_gold_price():
    url = 'https://gadgets.ndtv.com/finance/digital-gold-price-in-india'
    r = requests.get(url, timeout=15)
    if r.status_code==200:
        print("Fetched page : "+url)
        # Creating a bs4 object to store the contents of the requested page
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        div = soup.find("div", {"class":"_gdptx _updt"})
        print(div.text)
        if not 'Last Updated' in div.text:
            print(f'parsing logic needs change.  unable to get last updated')
            return None, None
        last_updated = div.text.replace('Last Updated: ', '').replace(' IST', '')
        lu = get_datetime_or_none_from_string(last_updated)
        if not lu:
            print(f'failed to parse {last_updated} to datetime')
            return None, None
        pricediv = soup.find("div", {"class":"_gdtpw _flx"})
        print(pricediv)
        spans = pricediv.findChildren(['span'])
        for span in spans:
            print(f'{span}  {span.text}')
            if '₹' in span.text:
                val_str = span.text.replace('₹ ', '').replace('/g', '').replace(',','')
                val = get_float_or_none_from_string(val_str)
                if val:
                    return lu, val
    elif r.status_code==404:
        print("Page not found")
    else:
        print("A different status code received : "+str(r.status_code))
    return None, None
'''


'''

import os
import pathlib
from selenium import webdriver
import time
import datetime
from dateutil.relativedelta import relativedelta

def get_historical_price(dt):
    url = 'https://goldprice.org/gold-price-today/' + dt.strftime("%Y-%m-%d")
    print(f'fetching {url}')
    chrome_options = webdriver.ChromeOptions()

    #chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(), chrome_options=chrome_options)
    driver.get(url)
    time.sleep(5)
    val = 0
    for i in range(3):
        try:
            print(f'{i}: clicking on currency')
            sel_choice=driver.find_element(By.XPATH, "//select/option[@value='INR']")
            sel_choice.click()
            time.sleep(5)
            print(f'{i}: clicking on weight metric')
            sel_choice=driver.find_element(By.XPATH, "//select/option[@value='g']")
            sel_choice.click()
            time.sleep(5)
            print(f'{i}: checking for price')
            sp_element = driver.find_element(By.ID, 'gpxtickerLeft_price')
            print(sp_element)
            val = sp_element.text
            break
        except Exception as ex:
            print(f'attempt {i} exception {ex} when retrieving price for gold')

    driver.close()
    driver.quit()
    return float(val.replace(',', ''))

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ',path)
    return path

def get_using_api(dt):
    from_dt = dt + relativedelta(days=-5)
    to_dt = dt

    url = f'https://fsapi.gold.org/api/v11/charts/goldpriceref/main?startDate={from_dt.strftime("%Y-%m-%d")}&endDate={to_dt.strftime("%Y-%m-%d")}'
    headers = {'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Host': 'fsapi.gold.org',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
                'X-Requested-With': 'XMLHttpRequest',
                'origin':'https://www.gold.org',
                'Referer':'https://www.gold.org'
                }
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        print(r.json())
    else:
        print(f'unexpected response {r.status_code}')


def get_using_api_v2(dt):
     
    from_dt = datetime.datetime.combine(dt + relativedelta(days=-5), datetime.datetime.min.time())
    to_dt = datetime.datetime.combine(dt, datetime.datetime.min.time())

    epoch = datetime.datetime.utcfromtimestamp(0)

    fd = (from_dt - epoch).total_seconds() * 1000.0
    td = (to_dt - epoch).total_seconds() * 1000.0
    url = f'https://fsapi.gold.org/api/v11/charts/goldprice/inr/gm/{fd},{td}'
    headers = {'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Host': 'fsapi.gold.org',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
                'X-Requested-With': 'XMLHttpRequest',
                'origin':'https://www.gold.org',
                'Referer':'https://www.gold.org'
                }
    print(f'fetching {url}')
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        res = r.json()
        for curr, values in res['chartData'].items():
            print(f'{curr} {values}')
            if curr == 'INR':
                for dv in values:
                    print(f'{dv[0]}  {dv[1]}')
                    date_time = datetime.datetime.fromtimestamp(dv[0]/1000)
                    val = dv[1]/31.1035
                    print(f'{date_time}: {val}')

    else:
        print(f'unexpected response {r.status_code}')

'''