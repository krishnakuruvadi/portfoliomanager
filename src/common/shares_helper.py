import os
import requests
import json
from django.conf import settings
from django.db import IntegrityError
from shared.utils import *
from .models import Dividend, Bonus, Split
from .nse_bse import get_nse_bse
import traceback

def pull_corporate_actions(symbol, exchange, from_date, to_date):
    dest_path = os.path.join(settings.MEDIA_ROOT, 'corporateActions')
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    temp_path = os.path.join(dest_path, 'temp')
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    try:
        if exchange == 'NSE':
            headers = {
                "User-Agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'
            }
            page = requests.get('https://www.nseindia.com/', timeout=5, headers=headers)
            cookie = page.cookies
            fin_symbol = symbol.replace('&','%26')
            url = 'https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol=' + fin_symbol
            if from_date:
                url = url + '&from_date=' + from_date.strftime('%d-%m-%Y') + '&to_date=' + datetime.date.today().strftime('%d-%m-%Y') #01-01-2005&to_date=31-12-2020'
            r = requests.get(url, headers=headers, cookies=cookie, timeout=10)
            status = r.status_code
            if status != 200:
                print(f"An error has occured. [Status code {status} ]")
            else:
                dest_file = os.path.join(temp_path, exchange+'_'+symbol+'.json')
                with open(dest_file, 'w') as json_file:
                    json.dump(r.json(), json_file)
        else:
            print(f'not supported exchange {exchange}')
    except Exception as ex:
        print(f'exception getting corporate actions for {exchange} : {symbol} {ex}')


def process_corporate_actions():
    dest_path = os.path.join(settings.MEDIA_ROOT, 'corporateActions')
    temp_path = os.path.join(dest_path, 'temp')
    if os.path.exists(temp_path):
        for file_name in os.listdir(temp_path):
            try:
                exchange = file_name[0:file_name.find('_')]
                symbol = file_name[file_name.find('_')+1: file_name.find('.json')]
                processed_file = os.path.join(dest_path, exchange+'_'+symbol+'.json')
                existing_data = None
                if os.path.exists(processed_file):
                    try:
                        with open(processed_file) as f:
                            existing_data = json.load(f)
                    except Exception as ex:
                        print(f'exception opening {processed_file}: {ex}')
                if not existing_data:
                    existing_data = dict()
                data = None
                with open(os.path.join(temp_path, file_name)) as f:
                    data = json.load(f)
                if exchange == 'NSE':
                    print('-------------------------------------')
                    print(f'                 {symbol}')
                    print('-------------------------------------')
                    for entry in data:
                        dt = get_date_or_none_from_string(entry['recDate'], '%d-%b-%Y', False)
                        if not dt:
                            dt = get_date_or_none_from_string(entry['exDate'], '%d-%b-%Y', False)
                        if not dt:
                            print(f'failed to convert to date {entry}')
                            continue
                        sub = entry['subject']
                        if 'bonus' in sub.lower():
                            nums = find_numbers_in_string(sub)
                            if len(nums) > 0:
                                if not 'bonus' in existing_data:
                                    existing_data['bonus'] = list()
                                found = False
                                for item in existing_data['bonus']:
                                    if item['date'] == dt.strftime('%d-%b-%Y'):
                                        found = True
                                        break
                                if not found:
                                    bonus = dict()
                                    bonus['date'] = dt.strftime('%d-%b-%Y')
                                    bonus['from'] = int(nums[0])
                                    bonus['to'] = int(nums[1])
                                    bonus['subject'] = sub
                                    existing_data['bonus'].append(bonus)
                                print(f'{dt}: Bonus {int(nums[0])} to {int(nums[1])}')
                            else:
                                print(f'failed to find bonus ratio {sub}')
                        elif 'split' in sub.lower():
                            nums = find_numbers_in_string(sub)
                            if len(nums) > 0:
                                print(f'{dt}: Split {int(nums[0])} to {int(nums[1])}')
                                if not 'split' in existing_data:
                                    existing_data['split'] = list()
                                found = False
                                for item in existing_data['split']:
                                    if item['date'] == dt.strftime('%d-%b-%Y'):
                                        found = True
                                        break
                                if not found:
                                    split = dict()
                                    split['date'] = dt.strftime('%d-%b-%Y')
                                    split['from'] = int(nums[0])
                                    split['to'] = int(nums[1])
                                    split['subject'] = sub
                                    existing_data['split'].append(split)
                            else:
                                print(f'failed to find split ratio {sub}')

                        elif 'div' in sub.lower():
                            nums = find_numbers_in_string(sub)
                            if len(nums) > 0:
                                print(f'{dt}: Dividend {round(nums[0], 2)}')
                                if not 'dividend' in existing_data:
                                    existing_data['dividend'] = list()
                                found = False
                                for item in existing_data['dividend']:
                                    if item['date'] == dt.strftime('%d-%b-%Y'):
                                        found = True
                                        break
                                if not found:
                                    dividend = dict()
                                    dividend['date'] = dt.strftime('%d-%b-%Y')
                                    dividend['amount'] = round(nums[0], 2)
                                    dividend['subject'] = sub
                                    existing_data['dividend'].append(dividend)
                            else:
                                print(f'failed to find dividend {sub}')

                        else:
                            print(f'couldnt classify as dividend or split or bonus {entry}')
                    print('-------------------------------------')
                    if len(existing_data) > 0:
                        with open(processed_file, 'w') as f:
                            json.dump(existing_data, f, indent=4)
                else:
                    print(f'unsupported exchange {exchange}')
            except Exception as ex:
                print(f'exception processing file {os.path.join(temp_path, file_name)} {ex}')
    else:
        print(f'directory {temp_path} not present to process corporate actions')

def find_numbers_in_string(inp):
    nums = list()
    try:
        for i in inp.split():
            almost_num = False
            if i.lower().startswith('rs') and i.lower() != 'rs' and not i.lower().endswith('rs') and not i.lower().endswith('rs.'):
                almost_num = True
                temp = i.lower()
                temp = temp.replace('rs.', '')
                temp = temp.replace('rs', '')
                if temp.startswith('.'):
                    temp = temp[1:]
            elif 'rs' in i.lower() and i.lower() != 'rs' and not i.lower().endswith('rs') and not i.lower().endswith('rs.'):
                almost_num = True
                temp = i.lower()
                temp = temp[temp.find('rs')+2:]
                temp = temp[0:temp.find(' ')]
                if temp.startswith('.'):
                    temp = temp[1:]
            elif i.lower().startswith('re') and i.lower() != 're' and not i.lower().endswith('re') and not i.lower().endswith('re.'):
                almost_num = True
                temp = i.lower()
                temp = temp.replace('re.', '')
                temp = temp.replace('re', '')
                if temp.startswith('.'):
                    temp = temp[1:]
            elif 're' in i.lower() and i.lower() != 're' and not i.lower().endswith('re') and not i.lower().endswith('re.'):
                almost_num = True
                temp = i.lower()
                temp = temp[temp.find('re')+2:]
                temp = temp[0:temp.find(' ')]
                if temp.startswith('.'):
                    temp = temp[1:]
            else:
                temp = i

            temp = temp.replace('/-', '')
            temp = temp.replace('/', '')
            if ':' in temp:
                splits = temp.split(':')
                first_num = get_int_or_none_from_string(splits[0])
                if not first_num:
                    fn = splits[0]
                    n = 0
                    i = len(fn)-1
                    while i >= 0:
                        if fn[i] in ['0','1','2','3','4','5','6','7','8','9']:
                            n = n+int(fn[i])*pow(10,len(fn)-(i+1))
                        else:
                            break
                        i -= 1
                    if n > 0:
                        first_num=n
                if first_num:
                    second_num = get_int_or_none_from_string(splits[1])
                    if not second_num:
                        sn = splits[1]
                        n = 0
                        i = 0
                        while i < len(sn):
                            if sn[i] in ['0','1','2','3','4','5','6','7','8','9']:
                                n = n*10+int(sn[i])
                            else:
                                break
                            i+=1
                        if n > 0:
                            second_num=n
                    if first_num and second_num:
                        nums.append(first_num)
                        nums.append(second_num)

            res = get_float_or_none_from_string(temp, False)
            if res:
                if not res in nums:
                    nums.append(res)
            elif almost_num:
                print(f'looks like a number but couldnt convert {i}')
    except Exception as ex:
        print(f"Exception in finding numbers {ex}")
    return nums

def store_corporate_actions():
    dest_path = os.path.join(settings.MEDIA_ROOT, 'corporateActions')
    if os.path.exists(dest_path):
        for file_name in os.listdir(dest_path):
            processed_file = os.path.join(dest_path, file_name)
            if not os.path.isfile(processed_file):
                continue
            try:
                exchange = file_name[0:file_name.find('_')]
                symbol = file_name[file_name.find('_')+1: file_name.find('.json')]
                isin = None
                if exchange == 'NSE':
                    res = get_nse_bse(symbol, None, None)
                    isin = res['isin']
                elif exchange == 'BSE':
                    res = get_nse_bse(None, symbol, None)
                    isin = res['isin']
                elif exchange == 'NSE/BSE':
                    isin = symbol
                existing_data = None
                try:
                    with open(processed_file) as f:
                        existing_data = json.load(f)
                except Exception as ex:
                        print(f'exception opening {processed_file}: {ex}')
                if not existing_data:
                    continue
                if 'bonus' in existing_data:
                    for item in existing_data['bonus']:
                        try:
                            date = get_date_or_none_from_string(item['date'], format='%d-%b-%Y')
                            exists = False
                            if isin:
                                bonus_items = Bonus.objects.filter(date=date, isin=isin)
                                if len(bonus_items) > 0:
                                    exists = True
                            if not exists:
                                Bonus.objects.create(
                                    exchange=exchange,
                                    symbol=symbol,
                                    isin=isin,
                                    ratio_num=item['from'],
                                    ratio_denom=item['to'],
                                    subject=item['subject'],
                                    date=date
                                )
                        except IntegrityError:
                            print('Bonus entry exists')
                if 'dividend' in existing_data:
                    for item in existing_data['dividend']:
                        try:
                            date = get_date_or_none_from_string(item['date'], format='%d-%b-%Y')
                            exists = False
                            if isin:
                                dividend_items = Dividend.objects.filter(date=date, isin=isin)
                                if len(dividend_items) > 0:
                                    exists = True
                            if not exists:
                                Dividend.objects.create(
                                    exchange=exchange,
                                    symbol=symbol,
                                    isin=isin,
                                    amount=item['amount'],
                                    subject=item['subject'],
                                    date=date
                                )
                        except IntegrityError:
                            print('Dividend entry exists')
                if 'split' in existing_data:
                    for item in existing_data['split']:
                        try:
                            date = get_date_or_none_from_string(item['date'], format='%d-%b-%Y')
                            exists = False
                            if isin:
                                split_items = Split.objects.filter(date=date, isin=isin)
                                if len(split_items) > 0:
                                    exists = True
                            if not exists:
                                Split.objects.create(
                                    exchange=exchange,
                                    symbol=symbol,
                                    isin=isin,
                                    ratio_num=item['from'],
                                    ratio_denom=item['to'],
                                    subject=item['subject'],
                                    date=date
                                )
                        except IntegrityError:
                            print('Split entry exists')
            except Exception as ex:
                print(f'exception while processing {file_name}: {ex}')
                traceback.print_exc()
    else:
        print(f'directory {dest_path} not present to process corporate actions')
