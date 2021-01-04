
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import os
import pathlib
import time
import datetime
from common.models import MutualFund

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

def pull_ms(code, ignore_names, replaceAnd=False):
    fund = None
    try:
        fund = MutualFund.objects.get(code=code)
    except MutualFund.DoesNotExist:
        return None
    mf_name = None
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
    driver = webdriver.Chrome(executable_path=get_path_to_chrome_driver())
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
            time.sleep(5)
            #els = driver.find_elements_by_xpath("//*[@class='ui-autocomplete' and @class='quote-list']")
            els = driver.find_elements_by_class_name('quote-list')
            if len(els) == 0:
                if not replaceAnd:
                    if mf_name_parts[i] == '&' or mf_name_parts[i].lower() == 'and':
                        driver.close()
                        return pull_ms(code, ignore_names, True)
                print('len(els) is 0. closing driver')
                driver.close()
                return None
            for el in els:
                if el.tag_name == 'ul':
                    #print(el.id)
                    if 'more' in el.get_attribute('innerHTML'):
                        continue
                    '''
                    for li in el.find_elements_by_xpath('.//li'):
                        aTagsInLi = el.find_elements_by_css_selector('li a')
                        for a in aTagsInLi:
                            print('href', a.get_attribute('href'))
                        try:
                            st = li.find_element_by_xpath(".//a/div/div/strong")
                            print('st', st.text)
                        except Exception as ex:
                            pass
                    '''
                    '''
                    <li class="ui-menu-item" role="presentation"><a class="anchor ui-corner-all" id="ui-id-101" tabindex="-1"><div class="row quote-item"><div class="col-xs-12 quote-name"><strong>PGIM India Global Equity Opportunities </strong>Fund Direct Plan Dividend Payout</div></div></a></li><li class="ui-menu-item" role="presentation"><a class="anchor ui-corner-all" id="ui-id-102" tabindex="-1"><div class="row quote-item"><div class="col-xs-12 quote-name"><strong>PGIM India Global Equity Opportunities </strong>Fund Direct Plan Dividend Reinvestment</div></div></a></li><li class="ui-menu-item" role="presentation"><a class="anchor ui-corner-all" id="ui-id-103" tabindex="-1"><div class="row quote-item"><div class="col-xs-12 quote-name"><strong>PGIM India Global Equity Opportunities </strong>Fund Direct Plan Growth</div></div></a></li><li class="ui-menu-item" role="presentation"><a class="anchor ui-corner-all" id="ui-id-104" tabindex="-1"><div class="row quote-item"><div class="col-xs-12 quote-name"><strong>PGIM India Global Equity Opportunities </strong>Fund Dividend Payout</div></div></a></li><li class="ui-menu-item" role="presentation"><a class="anchor ui-corner-all" id="ui-id-105" tabindex="-1"><div class="row quote-item"><div class="col-xs-12 quote-name"><strong>PGIM India Global Equity Opportunities </strong>Fund Dividend Reinvestment</div></div></a></li><li class="ui-menu-item" role="presentation"><a class="anchor ui-corner-all" id="ui-id-106" tabindex="-1"><div class="row quote-item"><div class="col-xs-12 quote-name"><strong>PGIM India Global Equity Opportunities </strong>Fund Growth</div></div></a></li>
                    '''
                    li_elems = el.find_elements_by_xpath('.//li')
                    if len(li_elems)> 10:
                        print('too many results')
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
                                        data = grab_details(driver)
                                        driver.close()
                                        if not fund.ms_name or fund.ms_name != high_name:
                                            fund.ms_name = high_name
                                            fund.save()
                                        return data
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
        return None
    except TimeoutException:
        driver.quit()
    except ElementNotInteractableException:
        driver.close()
        pull_ms(code, ignore_names, replaceAnd)
    except Exception as ex:
        print('Exception during processing', ex)
        driver.close()
        return None


def match_score(base, comp):
    base_parts = base.split(' ')
    comp_parts = comp.split(' ')
    score = 0
    for part in base_parts:
        if part in comp_parts:
            score = score+1
        else:
            if part == 'and' or part == '&':
                if 'and' in comp_parts or '&' in comp_parts:
                    score = score + 1
    print('score:', score, ' ', base, ' ', comp)
    return score

def grab_details(driver):
    data = dict()
    is_elems = driver.find_elements_by_class_name('investment-style')
    for is_elem in is_elems:
        if is_elem.tag_name == 'svg':
            print('is_elem', is_elem.get_attribute('innerHTML'))
            data['blend'] = is_elem.find_element_by_tag_name('title').text
    cat_elems = driver.find_elements_by_xpath("//div[contains(text(),'Category')]")
    for cat_elem in cat_elems:
        print('cat_elem class:', cat_elem.get_attribute('class'))
        if 'sal-dp-name ng-binding' in cat_elem.get_attribute('class'):
            parent_cat_elem = cat_elem.find_element_by_xpath('./..')
            for elem in parent_cat_elem.find_elements_by_tag_name('div'):
                if elem.text != 'Category':
                    data['category'] = elem.text
    tab_elems = driver.find_elements_by_class_name('tabon')
    for te in tab_elems:
        for anchor in te.parent.find_elements_by_tag_name('a'):
            print('a href', anchor.get_attribute('href'))
            if 'performance' in anchor.get_attribute('href').lower() or 'performance' in anchor.text.lower():
                anchor.click()
                time.sleep(5)
                tables = driver.find_elements_by_xpath("//table[@class='total-table']")
                print('len of total tables', len(tables))
                for table in tables:
                    print('inside table:', table.get_attribute('innerHTML'))
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
                                print('col innerHTML', col.get_attribute('innerHTML'))
                
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
                            print('col innerHTML', col.get_attribute('innerHTML'))
                break
    return data
