import requests
from shared.utils import k_decode, get_datetime_or_none_from_string, get_float_or_none_from_string, get_int_or_none_from_string
import bs4
import datetime


eurl=b'\x03\x11\r\x07\x1cHKD\x12\x0e\x00A\x04\x05\x07\x10\x1c\x05\n\x01\x01\n\x17\x1a\x1f\x00\x1c\x08\x02\x0b\x1cY\x0c\x1d\tD\x0c\x17\x13\x06\x11\x01\x18J'

def get_headers():

    return {'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0'
            }

def get_india_index_returns():
    url = k_decode(eurl)
    headers=get_headers()
    for retry in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                soup = bs4.BeautifulSoup(r.content, 'html.parser')

                content = dict()
                content['trailing_ret'] = list()
                tab = soup.find("table",{"class":"test-trailing-table"})
                tbody = tab.find("tbody")
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    entry = dict()
                    entry['name'] = cols[0].text
                    entry['1D'] = get_float_or_none_from_string(cols[1].text)
                    entry['1W'] = get_float_or_none_from_string(cols[3].text)
                    entry['1M'] = get_float_or_none_from_string(cols[4].text)
                    entry['3M'] = get_float_or_none_from_string(cols[5].text)
                    entry['1Y'] = get_float_or_none_from_string(cols[6].text)
                    entry['3Y'] = get_float_or_none_from_string(cols[7].text)
                    entry['5Y'] = get_float_or_none_from_string(cols[8].text)
                    entry['10Y'] = get_float_or_none_from_string(cols[9].text)
                    entry['YTD'] = get_float_or_none_from_string(cols[2].text)
                    entry['inception'] = None
                    entry['6M'] = None
                    entry['15Y'] = None
                    content['trailing_ret'].append(entry)
                
                content['yearly_ret'] = list()
                tab = soup.find("table",{"class":"test-annual-table"})
                thead = tab.find("thead")
                headers = thead.find_all('th')
                years = list()
                for h in range(0, len(headers)):
                    years.append(get_int_or_none_from_string(headers[h].text))
                tbody = tab.find("tbody")
                rows = tbody.find_all("tr")
                today = datetime.date.today()
                for row in rows:
                    cols = row.find_all("td")
                    entry = dict()
                    entry['name'] = cols[0].text
                    for yr in range(1,9):
                        entry[years[yr]] = get_float_or_none_from_string(cols[yr].text)
                    content['yearly_ret'].append(entry)
                
                content['quarterly_ret'] = list()
                tab = soup.find("table",{"class":"test-quarterly-table"})
                thead = tab.find("thead")
                headers = thead.find_all('th')
                qnames = list()
                for h in range(0, len(headers)):
                    qnames.append(headers[h].text)
                tbody = tab.find("tbody")
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    entry = dict()
                    entry['name'] = cols[0].text
                    for q in range(1,9):
                        entry[qnames[q]] = get_float_or_none_from_string(cols[q].text)

                    content['quarterly_ret'].append(entry)

                content['monthly_ret'] = list()
                tab = soup.find("table",{"class":"test-monthly-table"})
                thead = tab.find("thead")
                headers = thead.find_all('th')
                mnames = list()
                for h in range(0, len(headers)):
                    mnames.append(headers[h].text)
                tbody = tab.find("tbody")
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    entry = dict()
                    entry['name'] = cols[0].text
                    for m in range(1,9):
                        entry[mnames[m]] = get_float_or_none_from_string(cols[m].text)

                    content['monthly_ret'].append(entry)
                
                asonlist = soup.find_all("small")
                content['as_on'] = datetime.date.today()
                for ason in asonlist:
                    lo = ason.text.lower()
                    if 'as on' in lo:
                        print(f'trying to convert {ason.text} to datetime')
                        content['as_on'] = get_datetime_or_none_from_string(ason.text.replace('As on ',''),'%d-%b-%Y %H:%M')
                        if content['as_on']:
                            break
                        content['as_on'] = get_datetime_or_none_from_string(ason.text.replace('As on ',''),'%d-%b-%Y')
                        if content['as_on']:
                            break
                if not content['as_on']:
                    content['as_on'] = datetime.date.today()
                return content

            else:
                print(f'failed to retrieve with status code {r.status_code}')
        except Exception as ex:
            print(f'exception {ex} while getting index returns')
    return dict()

if __name__ == "__main__":
    print(get_india_index_returns())