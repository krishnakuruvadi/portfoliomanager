import requests

def supported_currencies_as_list():
    url = f'https://raw.githubusercontent.com/krishnakuruvadi/portfoliomanager-data/main/currencies.json'
    print(f'fetching from url {url}')
    r = requests.get(url, timeout=15)
    ret = list()
    if r.status_code == 200:
        for entry in r.json()['currencies']:
            ret.append(entry)
    else:
        ret.append('INR')
        ret.append('USD')
    return ret