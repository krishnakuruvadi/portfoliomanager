import requests
from os.path import isfile
import csv
#from shared.utils import *
import os
import pathlib
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from django.core.files.storage import FileSystemStorage
from .models import MutualFund
from alerts.alert_helper import create_alert, Severity


class BSEStar:
    
    def get_all_schemes(self, filename):
        schemes = dict()
        if isfile(filename):
            with open(filename, mode='r', encoding='utf-8-sig') as csv_file:
                print("opened file as csv:", filename)
                csv_reader = csv.DictReader(csv_file, delimiter="|")
                for row in csv_reader:
                    #print(row)
                    isin = row['ISIN']
                    scheme_name = row['Scheme Name']
                    #print('isin:', isin, ' scheme:', scheme_name)
                    schemes[isin] = scheme_name
        return schemes

def update_bsestar_schemes(schemes):
    mf_objs = MutualFund.objects.all()
    for mf_obj in mf_objs:
        mf_obj.bse_star_name = schemes.get(mf_obj.isin, None)
        mf_obj.save()

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ',path)
    return path

def get_path_to_media():
    path = pathlib.Path(__file__).parent.parent.absolute()
    path = os.path.join(path, 'media')
    print('path to media', path)
    return path

def download_bsestar_schemes():
    url = 'https://www.bsestarmf.in/RptSchemeMaster.aspx'
    chrome_options = webdriver.ChromeOptions()
    path_to_media = get_path_to_media()
    prefs = {'download.default_directory' : path_to_media}
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(),options=chrome_options)
    driver.get(url)
    timeout = 30
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, "btnText")))
        submit_element = driver.find_element_by_id("btnText")
        submit_element.click()
        time.sleep(10)
        driver.close()
    except TimeoutException:
        driver.quit()
    
    bse_star_file = None
    for file in os.listdir(path_to_media):
        if "schm" in file.lower():
            bse_star_file = os.path.join(path_to_media, file)
            break
    if bse_star_file:
        bse_star_obj = BSEStar()
        bse_schemes = bse_star_obj.get_all_schemes(bse_star_file)
        if len(bse_schemes) > 0:
            update_bsestar_schemes(bse_schemes)
            fs = FileSystemStorage()
            fs.delete(bse_star_file)
        else:
            create_alert(
                summary='Failure to update BSE StAR schemes',
                content='schemes parsed is 0',
                severity=Severity.error
            )
    else:
        print('no bse star file. not updating schemes')
        description = 'no bse star file. not updating schemes'
        create_alert(
            summary='Failure to update BSE StAR schemes',
            content= description,
            severity=Severity.error
        )

    '''
    headers ={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate, br'}

    data = {'ddlTypeOption': 'SCHEMEMASTER', 'btnText': 'Export+to+Text'}
    x = requests.post(url, data=data, headers=headers)
    print(x.text)
    '''


if __name__ == "__main__":
    bse_star = BSEStar()
    download_bsestar_schemes()
    #bse_star.get_all_schemes('/Users/kkuruvad/Downloads/SCHMSTRDET_04072020.txt')

