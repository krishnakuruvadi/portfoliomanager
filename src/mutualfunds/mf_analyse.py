
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import pathlib
import time
import datetime
from common.models import MutualFund
import pprint
import json
import re

from alerts.alert_helper import create_alert, Severity


def obfuscate(byt):
    # Use same function in both directions.  Input and output are bytes
    # objects.
    mask = b'keyword'
    lmask = len(mask)
    return bytes(c ^ mask[i % lmask] for i, c in enumerate(byt))

def decode(data):
    return obfuscate(data).decode()

def test(s):
    data = obfuscate(s.encode())
    print(len(s), len(data), data)
    newdata = obfuscate(data).decode()
    print('obfuscated data', data)
    print('decoded data', newdata)
    print(newdata == s)

def get_path_to_chrome_driver():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    for file in os.listdir(path):
        if "chromedriver" in file.lower():
            path = os.path.join(path, file)
            break
    print('path to chrome driver ',path)
    return path

def process_browser_logs_for_network_events(logs):
    """
    Return only logs which have a method that start with "Network.response", "Network.request", or "Network.webSocket"
    since we're interested in the network events specifically.
    """
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if (
                "Network.response" in log["method"]
                or "Network.request" in log["method"]
                or "Network.webSocket" in log["method"]
        ):
            yield log

def write_logs(driver, att):
    logs = driver.get_log("performance")

    events = process_browser_logs_for_network_events(logs)
    with open(att+"_log_entries.txt", "wt") as out:
        for event in events:
            pprint.pprint(event, stream=out)

def get_token_and_ms_code(driver):
    logs = driver.get_log("performance")
    token = ''
    ms_code = ''
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if 'Network.requestWillBeSent' == log["method"] and 'documentURL' in log["params"] and 'access_token' in log["params"]['documentURL']:
            url = log["params"]['documentURL']
            token_search = re.search('.*access_token=(.*)&clientId.*', url, re.IGNORECASE)
            if token_search:
                token = token_search.group(1)
                print(f'token {token}')
            if 'v2/' in log["params"]['documentURL']:
                code_search = re.search('.*v2/(.*)/data.*', url, re.IGNORECASE)
                if code_search:
                    ms_code = code_search.group(1)
                    print(f'ms_code {ms_code}')
        if token != '' and ms_code != '':
            break
    print(f'get_token_and_ms_code: returning {token} and {ms_code}')
    return token, ms_code

def set_ms_code_for_fund(id, ms_code):
    try:
        fund = MutualFund.objects.get(id=id)
        fund.ms_id = ms_code
        fund.save()
        print(f'set ms_id to {ms_code} for mutualfund with id {id}')
    except MutualFund.DoesNotExist:
        print(f'mutualfund object with id {id} doesnt exist')

def form_space_separated_string(str_list, start, till, replace_and=False):
    ret = None
    for i in range(start, till+1):
        if not ret:
            ret = str_list[i]
        else:
            if str_list[i].strip():
                if str_list[i] == '&' and replace_and:
                    ret += ' &amp;'
                else:    
                    ret = ret + ' ' + str_list[i]
    print(f'  form_space_separated_string: ret{ret}')
    return ret

def get_ms_code(mf_name, isin, isin2, ms_name, ignore_names=None, retry=0):
    url = decode(b'\x03\x11\r\x07\x1cHKD\x12\x0e\x00A\x1f\x0b\x19\x0b\x10\x19\x08\x01\x10\n\x17W\x1e\x01')
    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(),desired_capabilities=capabilities)
    driver.get(url)
    timeout = 30
    ms_code = None
    if not ignore_names:
        ignore_names = list()
    try:
        try:
            continue_elem = driver.find_element_by_xpath('/html/body/form/div[3]/div[2]/div[2]/div[1]/a')
            if continue_elem:
                print(continue_elem)
                continue_elem.click()
        except Exception:
            pass
        search_element_id = decode(b'\x08\x11\x15G_-\x11\x08-\x1c\x16\x0b\x17\x164\x11\x01\x03>\x07\x0b\x1f\x00&\x03\x17\x06%\x1e\x11\x164\x00\x1f\x14\x07\x00\r\x12')
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, search_element_id)))
        search_element = driver.find_element_by_id(search_element_id)
        mf_name_parts = mf_name.split(' ')
        i = 0
        while i< len(mf_name_parts):
            part = mf_name_parts[i]
            if not part.strip():
                i += 1
                continue
            if i == len(mf_name_parts)-1:
                print('sending ', part)
                search_element.send_keys(part)
            else:
                print(f'{i} sending {part} + <space>')
                search_element.send_keys(part + ' ')
            time.sleep(3)

            els = driver.find_elements_by_class_name('quote-list')
            if len(els) == 0:
                print(f'No results found for {form_space_separated_string(mf_name_parts, 0, i)}')
                return None     
            else:
                for el in els:
                    if el.tag_name == 'ul':
                        #print(el.id)
                        if 'more' in el.get_attribute('innerHTML'):
                            print('too many (more) results')
                            send_next_key = True
                            i += 1
                            break
                        li_elems = el.find_elements_by_xpath('.//li')
                        send_next_key = False
                        if len(li_elems)> 10:
                            print('too many results')
                            
                            #print(f"{li.get_attribute('innerHTML')}")
                            till_now = form_space_separated_string(mf_name_parts, 0, i, True)
                            qn_elems = el.find_elements_by_css_selector('div.quote-name')
                            if qn_elems:
                                if till_now.lower() in qn_elems[0].get_attribute('innerHTML').lower():
                                    i += 1
                                    send_next_key = True
                                    break
                                else:
                                    print(f"176:didnt find {till_now} in {qn_elems[0].get_attribute('innerHTML')}")
                            else:
                                print(f'FIX ME: No quote name elements')
                                return None
                            if part == '-':
                                till_now = form_space_separated_string(mf_name_parts, 0, i-1)
                                remaining = form_space_separated_string(mf_name_parts, i+1, len(mf_name_parts)-1)
                                new_string = till_now + ' ' + remaining
                                print(f'trying {new_string} instead')
                                driver.close()
                                return get_ms_code(new_string, isin, isin2, ms_name, ignore_names)
                            elif part == '&':
                                new_search = form_space_separated_string(mf_name_parts, 0, i-1) + ' </strong>and '
                                if new_search.lower() in qn_elems[0].get_attribute('innerHTML').lower():
                                    new_search = form_space_separated_string(mf_name_parts, 0, i-1) + ' and ' + form_space_separated_string(mf_name_parts, i+1, len(mf_name_parts)-1)
                                    print(f'trying {new_search} instead')
                                    driver.close()
                                    return get_ms_code(new_search, isin, isin2, ms_name, ignore_names)
                            elif part.lower() == 'and':
                                print('193')
                                new_search = form_space_separated_string(mf_name_parts, 0, i-1) + ' </strong>&'
                                if new_search.lower() in qn_elems[0].get_attribute('innerHTML').lower():
                                    new_search = form_space_separated_string(mf_name_parts, 0, i-1) + ' & ' + form_space_separated_string(mf_name_parts, i+1, len(mf_name_parts)-1)
                                    print(f'trying {new_search} instead')
                                    driver.close()
                                    return get_ms_code(new_search, isin, isin2, ms_name, ignore_names)
                                else:
                                    print(f'{new_search} not found in {qn_elems[0].get_attribute("innerHTML")}')
                            else:
                                print(f'part {part}')
                        print('200')
                        if len(li_elems) and not send_next_key:
                            qn_elems = el.find_elements_by_css_selector('div.quote-name')
                            if qn_elems:
                                map_elems = dict()
                                high_score = 0
                                high_element = -1
                                high_name = ''
                                for num, div in enumerate(qn_elems):
                                    print("innerHtml", div.get_attribute('innerHTML'))
                                    temp = div.get_attribute('innerHTML').replace('<strong>', '')
                                    temp = temp.replace('</strong>', '')
                                    temp = temp.replace('&amp;', '&')
                                    if temp not in ignore_names:
                                        map_elems[num] = match_score(mf_name, temp)
                                        if high_score<map_elems[num]:
                                            high_score = map_elems[num]
                                            high_element = num
                                            high_name = temp
                                
                                if high_element != -1:
                                    best_match_elem = qn_elems[high_element]
                                    print('high_element:', high_element, ' high_name:', high_name, ' high_element:', high_element)
                                    print('clicking')
                                    best_match_elem.click()
                                    print('done clicking')
                                    time.sleep(10)
                                    print('done sleeping')
                                    j = 0
                                    while not ms_code and j < 3:
                                        try:
                                            print(f'j {j}')
                                        
                                            isin_elems = driver.find_elements_by_class_name('sal-mip-quote__symbol')
                                            for isin_elem in isin_elems:
                                                if isin_elem.text == isin or (isin2 and isin_elem.text == isin2):
                                                    if isin2:
                                                        print(f'matching fund found for {isin} or {isin2}')
                                                    else:
                                                        print(f'matching fund found for {isin}')
                                                    _, ms_code = get_token_and_ms_code(driver)
                                                else:
                                                    print(f'{isin_elem.text} didnt match {isin} or {isin2}')
                                        except Exception as ex:
                                            print(f'Exception {ex} searching for isin, attempt({j})')
                                        j += 1
                                        time.sleep(2)
                                    if not ms_code:
                                        ignore_names.append(high_name)
                                        driver.close()
                                        return get_ms_code(mf_name, isin, isin2, ms_name, ignore_names)
                        if not len(li_elems):
                            print('no matching funds found')
                            return None
                        else:
                            print(f'len(li_elems) {len(li_elems)}')

        driver.close()
    except StaleElementReferenceException:
        print(f'StaleElementReferenceException')
        driver.close()
        if not ms_code:
            retry += 1
            return get_ms_code(mf_name, isin, isin2, ms_name, ignore_names, retry)
    except Exception as ex:
        print('Exception during processing', ex)
        driver.close()
    return ms_code

def pull_ms(code, ignore_names, replaceAnd=False, token=None):
    fund = None
    try:
        fund = MutualFund.objects.get(code=code)
    except MutualFund.DoesNotExist:
        create_alert(
            summary='Code:' + code + ' Mutual fund not present',
            content= 'Not able to find a matching Mutual Fund with the code.',
            severity=Severity.error
        )
        return None, token
    mf_name = None
    if token and fund.ms_id:
        data = use_api_to_get_vals(token, fund.ms_id)
        if len(data.keys()):
            return data, token
        else:
            print(f'couldnt get data using token {token}')

    ms_code = fund.ms_id
    if fund.ms_name:
        mf_name = fund.ms_name
        mf_name = mf_name.replace('&amp;', '&')
    else:
        mf_name = fund.name
        mf_name = mf_name.replace('-', '')
        mf_name = mf_name.replace('  ', ' ')
        mf_name = mf_name.replace('&amp;', '&')
        if replaceAnd:
            if '&' in mf_name:
                mf_name = mf_name.replace('&', 'and')
            else:
                mf_name = mf_name.replace('and', '&')
                mf_name = mf_name.replace('And', '&')
    url = decode(b'\x03\x11\r\x07\x1cHKD\x12\x0e\x00A\x1f\x0b\x19\x0b\x10\x19\x08\x01\x10\n\x17W\x1e\x01')
    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver(),desired_capabilities=capabilities)
    driver.get(url)
    timeout = 30
    if not ignore_names:
        ignore_names = list()
    try:
        search_element_id = decode(b'\x08\x11\x15G_-\x11\x08-\x1c\x16\x0b\x17\x164\x11\x01\x03>\x07\x0b\x1f\x00&\x03\x17\x06%\x1e\x11\x164\x00\x1f\x14\x07\x00\r\x12')
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, search_element_id)))
        search_element = driver.find_element_by_id(search_element_id)
        mf_name_parts = mf_name.split(' ')
        for i, part in enumerate(mf_name_parts):
            if i == len(mf_name_parts)-1:
                print('sending ', part)
                search_element.send_keys(part)
            else:
                print('sending ', part + '<space>')
                search_element.send_keys(part + ' ')
            time.sleep(2)
            #els = driver.find_elements_by_xpath("//*[@class='ui-autocomplete' and @class='quote-list']")
            els = driver.find_elements_by_class_name('quote-list')
            if len(els) == 0:
                if not replaceAnd:
                    if mf_name_parts[i] == '&' or mf_name_parts[i].lower() == 'and':
                        driver.close()
                        return pull_ms(code, ignore_names, True)
                print('len(els) is 0. closing driver')
                driver.close()
                return None, token
            for el in els:
                if el.tag_name == 'ul':
                    #print(el.id)
                    if 'more' in el.get_attribute('innerHTML'):
                        continue
                    li_elems = el.find_elements_by_xpath('.//li')
                    if len(li_elems)> 10:
                        print(f'too many results {len(li_elems)}')
                        continue 
                    if len(li_elems):
                        qn_elems = el.find_elements_by_css_selector('div.quote-name')
                        if qn_elems:
                            map_elems = dict()
                            high_score = 0
                            high_element = -1
                            high_name = ''
                            for num, div in enumerate(qn_elems):
                                print("innerHtml", div.get_attribute('innerHTML'))
                                temp = div.get_attribute('innerHTML').replace('<strong>', '')
                                temp = temp.replace('</strong>', '')
                                temp = temp.replace('&amp;', '&')
                                if temp not in ignore_names:
                                    map_elems[num] = match_score(mf_name, temp)
                                    if high_score<map_elems[num]:
                                        high_score = map_elems[num]
                                        high_element = num
                                        high_name = temp
                            
                            if high_element != -1:
                                best_match_elem = qn_elems[high_element]
                                print('high_element:', high_element, ' high_name:', high_name, ' high_element:', high_element)
                                print('clicking')
                                best_match_elem.click()
                                print('done clicking')
                                time.sleep(5)
                                isin_elems = driver.find_elements_by_class_name('sal-mip-quote__symbol')
                                for isin_elem in isin_elems:
                                    if isin_elem.text == fund.isin or (fund.isin2 and isin_elem.text == fund.isin2):
                                        if fund.isin2:
                                            print(f'matching fund found for {fund.isin} or {fund.isin2}')
                                        else:
                                            print(f'matching fund found for {fund.isin}')
                                        data = dict()
                                        token, ms_code = get_token_and_ms_code(driver)
                                        if token != '' and ms_code != '':
                                            set_ms_code_for_fund(fund.id, ms_code)
                                            data = use_api_to_get_vals(token, ms_code)                                            
                                        else:
                                            print(f'not updated ms_code for {fund.name}')

                                        is_elems = driver.find_elements_by_class_name('investment-style')
                                        for is_elem in is_elems:
                                            if is_elem.tag_name == 'svg':
                                                print('is_elem', is_elem.get_attribute('innerHTML'))
                                                data['blend'] = is_elem.find_element_by_tag_name('title').text
                                        blend_xpath = decode(b'DJ\n\x16\x03_\x07\x04\x08\t\x18\x01\x17\n\x1f\x16T\x1a\x0b\x01I\x02\x06\x16\x1942\x05\x0f\x01\x10\x03\x06\x1d\n\n\tT\x14\x03\x13\x17\x18X[\x1e\x01\x04\x01\x18\x11\x14\x12\x01\x06I\x18\x11\x00\x1b\nP9')
                                        blend_elems = driver.find_elements_by_xpath(blend_xpath)
                                        if len(blend_elems) == 1:
                                            data['blend'] = blend_elems[0].get_attribute("title")
                                        '''
                                        cat_elems = driver.find_elements_by_xpath("//div[contains(text(),'Category')]")
                                        for cat_elem in cat_elems:
                                            print('cat_elem class:', cat_elem.get_attribute('class'))
                                            if 'sal-dp-name ng-binding' in cat_elem.get_attribute('class'):
                                                parent_cat_elem = cat_elem.find_element_by_xpath('./..')
                                                for elem in parent_cat_elem.find_elements_by_tag_name('div'):
                                                    if elem.text != 'Category':
                                                        data['categoryName'] = elem.text
                                        '''
                                        
                                        if data:
                                            driver.close()
                                            return data, token
                                        grab_details(driver, data)
                                        driver.close()
                                        if not fund.ms_name or fund.ms_name != high_name.replace('&amp;', '&'):
                                            fund.ms_name = high_name.replace('&amp;', '&')
                                            fund.save()
                                        return data, token
                                    else:
                                        print(isin_elem.text, ' not matched with isin:', fund.isin, ' or isin2:', fund.isin2)
                                time.sleep(10)
                                driver.close()
                                ignore_names.append(high_name)
                                return pull_ms(code, ignore_names)
                    else:
                        if not replaceAnd:
                            if mf_name_parts[i] == '&' or mf_name_parts[i].lower() == 'and':
                                driver.close()
                                return pull_ms(code, ignore_names, True)
                        #driver.close()
                        #return None
                else:
                    print('some other tag name', el.tag_name)
        #submit_element.click()
        driver.close()
        return None, token
    except TimeoutException:
        driver.quit()
    except ElementNotInteractableException:
        driver.close()
        return pull_ms(code, ignore_names, replaceAnd, token)
    except Exception as ex:
        print('Exception during processing', ex)
        driver.close()
        return None, token

def get_lower_case_splits(st):
    ret = list()
    for part in st.split(' '):
        ret.append(part.lower())
    return ret

def match_score(base, comp):
    base_parts = get_lower_case_splits(base)
    comp_parts = get_lower_case_splits(comp)
    score = 0
    for part in base_parts:
        if part == '-' or part == ' ':
            continue
        if part in comp_parts:
            score = score+1
            #print(f'found {part}, score: {score}')
        else:
            if part == 'and' or part == '&':
                if 'and' in comp_parts or '&' in comp_parts:
                    score = score + 1
                    #print(f'found {part}, score: {score}')
    #print('score:', score, ' ', base, ' ', comp)
    return score

def grab_details(driver, data):
    tab_elems = driver.find_elements_by_class_name('tabon')
    for te in tab_elems:
        for anchor in te.parent.find_elements_by_tag_name('a'):
            #print('a href', anchor.get_attribute('href'))
            if 'performance' in anchor.get_attribute('href').lower() or 'performance' in anchor.text.lower():
                anchor.click()
                time.sleep(5)
                tables = driver.find_elements_by_xpath("//table[@class='total-table']")
                print('len of total tables', len(tables))
                for table in tables:
                    #print('inside table:', table.get_attribute('innerHTML'))
                    if 'Since Inception' not in table.get_attribute('innerHTML'):
                        rows = table.find_elements_by_tag_name("tr")
                        if len(rows)>2:
                            data['performance'] = dict()
                            cur_yr = datetime.datetime.today().year
                            cols = rows[1].find_elements_by_tag_name("td")
                            for i,col in enumerate(cols):
                                txt = col.find_element_by_tag_name('span').text
                                print('returns col value', txt)
                                if i == 10:
                                    data['performance']['YTD'] = txt 
                                else:
                                    data['performance'][str(cur_yr-10+i)] = txt
                    else:
                        rows = table.find_elements_by_tag_name("tr")
                        if len(rows)>2:
                            if not 'performance' in data:
                                data['performance'] = dict()
                            cur_yr = datetime.datetime.today().year
                            cols = rows[1].find_elements_by_tag_name("td")
                            perfs = ['1D','1W','1M','3M','YTD','1Y','3Y','5Y','10Y','15Y','INCEPTION']
                            for i,col in enumerate(cols):
                                data['performance'][perfs[i]] = col.text
                                #print('col innerHTML', col.get_attribute('innerHTML'))
                
                tables = driver.find_elements_by_xpath("//table[@class='total-table no-return-rank']")
                print('len of total tables', len(tables))
                for table in tables:
                    rows = table.find_elements_by_tag_name("tr")
                    if len(rows)>2:
                        if not 'performance' in data:
                            data['performance'] = dict()
                        cur_yr = datetime.datetime.today().year
                        cols = rows[1].find_elements_by_tag_name("td")
                        perfs = ['1D','1W','1M','3M','YTD','1Y','3Y','5Y','10Y','15Y','INCEPTION']
                        for i,col in enumerate(cols):
                            data['performance'][perfs[i]] = col.text
                            #print('col innerHTML', col.get_attribute('innerHTML'))
                break

def use_api_to_get_vals(token, ms_code):
    data = dict()
    url = decode(b'\x03\x11\r\x07\x1cHKD\x04\t\x1eB\x15\x08\x04\x07\x18\x1bA\x1f\x0b\x19\x0b\x10\x19\x08\x01\x10\n\x17W\x14\x00\x1fK\x18\x04\x15Z\x1c\x17\x16\x1d\x0c\x1a\x12@\x04UD\x03\x0c\x19\x0b]\x10\x19\x04\x10\x1b\x06\x1c\x039\x00\r\x02\x1d\x1cK\x1dTV\x0cKC\x19D\x01\x18\x03\x0eM\x08\x04\x06\x18\x1b\nO\x01\x05C\x18\x14\x0c\x17\x17\x18:\r\x18\x04\x17\nV\x1e]E\x12T\x07\x07\x0c\x1c\x19\x1b;\x00V7*>!-7*)_\x15\n\x1c\x07\x03\x08\x18\x05\x04;\x00V\x06\x18\x03\n\x15\x0b\x19\x1c')
    url = url.replace('{$1}', ms_code)
    url = url.replace('{$2}', token)
    jsonResponse = get_json_response(url)
    if jsonResponse:
        data['performance'] = dict()
        data['categoryName'] = jsonResponse['categoryName']
        returns = jsonResponse['totalReturnNAV']
        perfs = ['1D','1W','1M','3M','YTD','1Y','3Y','5Y','10Y','15Y','INCEPTION']
        for i,ret in enumerate(returns):
            data['performance'][perfs[i]] = ret
        
    perf_url = decode(b'\x03\x11\r\x07\x1cHKD\x04\t\x1eB\x15\x08\x04\x07\x18\x1bA\x1f\x0b\x19\x0b\x10\x19\x08\x01\x10\n\x17W\x14\x00\x1fK\x18\x04\x15Z\x1c\x17\x16\x1d\x0c\x1a\x12@\x04UD\x03\x0c\x19\x0b]\x14\x0e\x17\x1f\x18\x1d\x1f\x05\x05\x06\x1cX\x19@K\x10AH\nP\x01\x01\x08 \x01\x14\x07\x13\n\x0c\x005\x1e\x1c\x06YM\t\x16\x14\x0e\x1e\x01V\x00\x17Q\x0e\x11\x07\x0e\x16\n(\x1b\x1d\x0f\x0e\x0bD\x0cK@\x19M\x06\x15\x1e\n\x1c\x10"\x01D%<;*468;I\x10\x01\x05\x06\x11\x1a\x0e\x00\x0f"\x01D\x14\x0e\x06\x01\x0c\n\x0b\x0e')
    perf_url = perf_url.replace('{$1}', ms_code)
    perf_url = perf_url.replace('{$2}', token)
    jsonResponse = get_json_response(perf_url)
    if jsonResponse:
        yrs = jsonResponse['table']['columnDefs']
        for l in jsonResponse['table']['growth10KReturnData']:
            data[l['label']] = dict()
            for i,ret in enumerate(l['datum']):
                data[l['label']][yrs[i]] = ret
    return data


def get_json_response(url):
    import requests
    from requests.exceptions import HTTPError
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        # access JSON content
        jsonResponse = response.json()
        print("Entire JSON response")
        print(jsonResponse)
        return jsonResponse
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        print(f'Other error occurred: {err}')
        return None

def pull_category_returns():
    url = decode(b'\x03\x11\r\x07\x1cHKD\x07\n\x12\x06\x1c\x00\x02\x04W\x1a\x00\x00\n\x02\x0b\x1e\x04\x1b\x13\x16E\x0c\x17X\t\x07\n\x0f\x16V\x14\x0e\x06\x01\x0c\n\x0b\x0e\x1f\x17\x16\r\n\x0b\x1a\x0e\x1c\x07\x0eK\x18\x04\x1f\n')
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver())
    driver.get(url)
    timeout = 30

    opt_element_id = decode(b"\x08\x11\x15G_-'\x04\x0b\r\x12\x01\x064\x07\x04\x1a\x12'\x1d\x08\x0f\x00\x0bF0\x16\x08;\x00\x0b\x1e\x00\x16")
    WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, opt_element_id)))
    ret = dict()
    val_opts = ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y', '3Y', '4Y','5Y','6Y','7Y','8Y','9Y', '10Y', 'YTD', 'Inception']
    for i, opt in enumerate(['1 Day', '1 Week', '1 Month', '3 Months', '6 Months', '1 Year', '2 Years', '3 Years', '4 Years','5 Years','6 Years','7 Years','8 Years','9 Years', '10 Years', 'YTD', 'Since Inception']):
        sel_choice=driver.find_element_by_xpath("//select/option[@value='" + opt + "']")
        sel_choice.click()
        time.sleep(5)
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, opt_element_id)))
        rows = driver.find_elements_by_xpath("//table/tbody/tr")
        as_on = None
        
        for row in rows:
            #print(row.text)
            cols = row.find_elements_by_tag_name("td")
            '''
            for col in cols:
                print('col text', col.text)
                if 'As on' in col.text:
                    as_on = col.text
            '''
            if len(cols) == 4 and 'h3' in cols[0].get_attribute('innerHTML'):
                #print('------------------------------------------------------------------')
                #print(cols[0].text,'\t', cols[1].text, '\t', cols[2].text, '\t', cols[3].text)
                #print('------------------------------------------------------------------')
                if cols[0].text not in ret.keys():
                    ret[cols[0].text] = dict()
                ret[cols[0].text][val_opts[i]] = dict()
                ret[cols[0].text][val_opts[i]]['avg'] = cols[1].text
                ret[cols[0].text][val_opts[i]]['top'] = cols[2].text
                ret[cols[0].text][val_opts[i]]['bottom'] = cols[3].text
    driver.close()
    return ret

def pull_blend(codes):
    ret = dict()
    if len(codes) == 0:
        return ret
    
    url = decode(b'\x03\x11\r\x07\x1cHKD\t\rY\x02\x1d\x16\x05\x0c\x17\x10\x1c\x06\x05\x19K\x1a\x18\x02]\x00\x00R\t\x1c\x0e\x17S\x00\tV\x11\x1a\x1c\x00\x18\x06\x0b\x12\n\x1c\x01\x19J\x0b\x12\x1c\x07\x08\x1f\x16W\x16\x1c\x02\x1cT)\x18\x19\x08\x07\x05\x0c\x000\x13R\x17\nF";Q:\x1c\r\x1d\x00\x0b\x04\nO"$,73KV%\')_2\x1e\x07\r\x1f\x1c*\x03\x16\x1e\x01VT\x05G\x13B\x18[\x19I\x0b_\x0eT\x17U\x05GI1\x11\x19\x17\x1c\x19\x0c\x0b-\x0fX09=T19)2\x12\x16O\x00\x00R\t\x1c\x0e\x17S\x00\t')
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver())
    blendsFirst = ['Large', 'Mid', 'Small']
    blendsSecond = ['Value', 'Blend', 'Growth']
    count = 1
    for i in range(9):
        if len(codes) == len(ret):
            break
        bin = ''
        for j in range (9):
            if i == j:
                bin = bin + '1'
            else:
                bin = bin + '0'
            if j != 8:
                bin = bin + '|'
        cur_url = url.replace('1|0|0|0|0|0|0|0|0',bin)
        print(f'getting {cur_url}')
        driver.get(cur_url)
        time.sleep(10)
        while(True):
            rows = driver.find_elements(By.TAG_NAME, "tr") # get all of the rows in the table
            for row in rows:
                # Get the columns (all the column 2)        
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) > 2:
                    #print(cols[2].text)
                    #cels = cols[2].find_elements_by_css_selector("*")
                    #for cel in cels:
                    #    print (cel.tag_name)
                    #    print (cel.text)
                    #print(cols[2].innerHTML)
                    a_elements = cols[2].find_elements(By.TAG_NAME, "a")
                    #print(len(a_elements))
                    if len(a_elements) == 1:
                        href=a_elements[0].get_attribute('href')
                        id = href[href.find('id=')+3:href.find('id=')+13]
                        mf_blend = blendsFirst[int(i/3)] + ' ' + blendsSecond[int(i%3)]
                        print(f'{count} : {id} {cols[2].text} is of type {mf_blend}')
                        count = count+1
                        if id in codes:
                            ret[id] = mf_blend
            next_elem = driver.find_element_by_xpath("//a[text()='Next']")
            class_exists = next_elem.get_attribute('class')
            if next_elem.is_enabled and not class_exists:
                next_elem.click()
                time.sleep(5)
            else:
                break
    driver.close()
    return ret