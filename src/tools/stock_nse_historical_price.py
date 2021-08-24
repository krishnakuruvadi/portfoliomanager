import codecs
import csv
import datetime
import requests

def get_float_or_zero_from_string(input):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            print(f'error converting {input} to float. returning 0')
    return 0

def pull_historical_values(symbol, from_date, to_date):
    headers = {
        "User-Agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'
    }
    cookie = None
    url = 'https://www.nseindia.com/'
    for i in range(3):
        try:
            page = requests.get(url, timeout=5, headers=headers)
            cookie = page.cookies
        except Exception as ex:
            pass
    if not cookie:
        print(f'attempt {i+1}: failed to get cookies from url {url}')
        return dict()

    fin_symbol = symbol.replace('&','%26')
    url = 'https://www.nseindia.com/api/historical/cm/equity?symbol=' + fin_symbol
    url = url + '&series=["EQ"]&from=' + from_date.strftime('%d-%m-%Y') + '&to=' + to_date.strftime('%d-%m-%Y')+'&csv=true'
    r = None
    for i in range(3):
        try:
            r = requests.get(url, headers=headers, cookies=cookie, timeout=15)
            
            if r.status_code == 200:
                break
        except Exception as ex:
            pass
    if not r or r.status_code != 200:
        print(f'failed to get proper response for {url}')
        return dict()

    try:
        text = r.iter_lines()
        reader = csv.DictReader(codecs.iterdecode(text, 'utf-8'), delimiter=',')
        response = dict()
        for row in reader:
            #print(row)
            date= None
            val = None
            for k,v in row.items():
                if "date" in k.lower():
                    date = datetime.datetime.strptime(v, "%d-%b-%Y").date()
                elif "close" == k.strip().lower():
                    val = v.strip()

                if date and val:
                    response[date] = get_float_or_zero_from_string(val.strip())
        print(f'done with request to get historical stock values for {symbol}, {from_date}, {to_date}')
        return response
    except Exception as ex:
        print(f'exception while getting historical value.{ex}')
        return dict()


if __name__ == "__main__":
    ret = pull_historical_values('GRUH', datetime.date(year=2019,month=1,day=1), datetime.date(year=2019,month=12,day=31))
    print(ret)