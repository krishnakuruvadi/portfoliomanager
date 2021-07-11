import os
import requests
import json
from django.conf import settings
from django.db import IntegrityError
from shared.utils import *
from .models import Dividendv2, Bonusv2, Splitv2, Stock
from .nse_bse import get_nse_bse
import traceback
from shares.models import Share

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
            if not os.path.isfile(processed_file) or '_' not in file_name or not file_name.endswith('.json'):
                print(f'ignoring {processed_file} to check for corporate actions')
                continue
            try:
                exchange = file_name[0:file_name.find('_')].replace('-','/')
                part = file_name[file_name.find('_')+1: file_name.find('.json')]
                data = None
                try:
                    with open(processed_file) as f:
                        data = json.load(f)
                except Exception as ex:
                    print(f'exception opening {processed_file}: {ex}')
                    continue
                stock = None
                try:
                    if exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        stock = Stock.objects.get(exchange=exchange, isin=part)
                    elif exchange in ['NASDAQ', 'NYSE']:
                        stock = Stock.objects.get(exchange=exchange, symbol=part)
                except Stock.DoesNotExist:
                    print(f'failed to find stock {exchange}, {part}')
                    continue
                if 'bonus' in data:
                    for item in data['bonus']:
                        try:
                            announcement_date = get_date_or_none_from_string(item['announcement_date'], format='%d-%m-%Y')
                            ex_date = get_date_or_none_from_string(item['ex_date'], format='%d-%m-%Y')
                            record_date = get_date_or_none_from_string(item['record_date'], format='%d-%m-%Y')
                            ratio = item['ratio']
                            num = int(ratio[0:ratio.find(':')])
                            denom = int(ratio[ratio.find(':')+1:])
                            Bonusv2.objects.create(
                                announcement_date=announcement_date,
                                record_date=record_date,
                                ex_date=ex_date,
                                stock=stock,
                                ratio_num=num,
                                ratio_denom=denom
                            )
                        except IntegrityError:
                            print('Bonus entry exists')
                        except Exception as ex:
                            print(f'error {ex} when processing {item}')
                if 'dividends' in data:
                    for item in data['dividends']:
                        try:
                            announcement_date = get_date_or_none_from_string(item['announcement_date'], format='%d-%m-%Y')
                            ex_date = get_date_or_none_from_string(item['ex_date'], format='%d-%m-%Y')
                            Dividendv2.objects.create(
                                stock=stock,
                                announcement_date=announcement_date,
                                ex_date=ex_date,
                                amount=item['amount']
                            )
                        except IntegrityError:
                            print('Dividend entry exists')
                        except Exception as ex:
                            print(f'error {ex} when processing {item}')
                if 'splits' in data:
                    for item in data['splits']:
                        try:
                            announcement_date = get_date_or_none_from_string(item['announcement_date'], format='%d-%m-%Y')
                            ex_date = get_date_or_none_from_string(item['ex_date'], format='%d-%m-%Y')
                            Splitv2.objects.create(
                                stock=stock,
                                announcement_date=announcement_date,
                                ex_date=ex_date,
                                old_fv=item['old_fv'],
                                new_fv=item['new_fv'],
                            )
                        except IntegrityError:
                            print('Split entry exists')
                        except Exception as ex:
                            print(f'error {ex} when processing {item}')
            except Exception as ex:
                print(f'exception while processing {file_name}: {ex}')
                traceback.print_exc()
    else:
        print(f'directory {dest_path} not present to process corporate actions')

def get_nse_bse_map_from_gist():
    url = b'\x03\x11\r\x07\x1cHKD\x02\x10\x04\x1b\\\x03\x02\x11\x11\x02\r\x07\x17\x0e\x17\x1a\x18\x01\x06\x01\x05\x11W\x14\x00\x1fK\x00\x17\x10\x04\x07\x1c\x05\x00\x10\x0b\x02\x19\x13\x00\x02JODWE\x05^]A@\\DV\tV@\x15\n\x14\x01^\x00A\x14VF\\\\]N\x11]EK\x19\x04\x0eX^\x14SZ\x07O\x11WG\x07X\x01A\x11V\x11\x06\x0eU\x1b\x16V\x11T[Q\x1dG^\x13\x00]RI@]EQSPV\x19\x1c\x17;\t\x16\x1cY\x05\x01\x0b\x05'
    url = k_decode(url)
    data = get_json_gist(url)
    return data

def get_usa_map_from_gist():
    url = b'\x03\x11\r\x07\x1cHKD\x02\x10\x04\x1b\\\x03\x02\x11\x11\x02\r\x07\x17\x0e\x17\x1a\x18\x01\x06\x01\x05\x11W\x14\x00\x1fK\x00\x17\x10\x04\x07\x1c\x05\x00\x10\x0b\x02\x19\x13\x00\x02J\x18FZB\x02\tW\x1bB\x0cDP\t\x00H\x15WE\x07\x0f\x03HN_\x17\\ZTLD\x0cGK\x19\x04\x0eX\x0bF]^\x00L\x15\x0c\x17Q_UHN]\x11\x06\rSOCZJPSVIBXKS\r\x00\x1cE\x0bK]\x0e\\V\x02\x1c\x13J\x01\x16\x16\x19'
    url = k_decode(url)
    data = get_json_gist(url)
    return data

def get_json_gist(url):
    r = requests.get(url, timeout=15)
    if r.status_code==200:
        decoded_content = r.content.decode('utf-8')
        #print(decoded_content)
        s = json.loads(decoded_content)
        #print(s)
        return s
    else:
        print(f'failed to get data from gist {r.status_code}')
        return None

def update_stocks():
    ret_nse_bse = get_nse_bse_map_from_gist()
    ret_usa = get_usa_map_from_gist()
    for obj in Stock.objects.all():
        if obj.exchange == 'BSE':
            if ret_nse_bse:
                found = False
                for k,v in ret_nse_bse.items():
                    if v['bse_security_id'] == obj.symbol:
                        found = True
                        if v.get('cap', '') != '':
                            obj.capitalisation = v['cap']
                            obj.save()
                        if v.get('mc_code', '') != '':
                            from tools.stock_mc import get_splits, get_bonus, get_dividends
                            try:
                                dest_path = os.path.join(settings.MEDIA_ROOT, 'corporateActions', obj.exchange+'_'+k+'.json')
                                get_splits(v['mc_code'], dest_path)
                                get_bonus(v['mc_code'], dest_path)
                                get_dividends(v['mc_code'], dest_path)
                            except Exception as ex:
                                print(f'exception {ex} when getting splits for {obj.symbol}')
                        break
                if not found:
                    print(f'unable to process {obj.symbol} due to lack of symbol data')
            else:
                print(f'unable to process {obj.symbol} due to lack of exchange {obj.exchange} data')
        elif obj.exchange in ['NSE', 'NSE/BSE']:
            if ret_nse_bse:
                found = False
                for k,v in ret_nse_bse.items():
                    if v['nse_symbol'] == obj.symbol:
                        found = True
                        if v.get('cap', '') != '':
                            obj.capitalisation = v['cap']
                            obj.save()
                        if v.get('mc_code', '') != '':
                            from tools.stock_mc import get_splits, get_bonus, get_dividends
                            try:
                                dest_path = os.path.join(settings.MEDIA_ROOT, 'corporateActions', obj.exchange.replace('/','-')+'_'+k+'.json')
                                get_splits(v['mc_code'], dest_path)
                                get_bonus(v['mc_code'], dest_path)
                                get_dividends(v['mc_code'], dest_path)
                            except Exception as ex:
                                print(f'exception {ex} when getting splits for {obj.symbol}')
                        break
                if not found:
                    print(f'unable to process {obj.symbol} due to lack of symbol data')
            else:
                print(f'unable to process {obj.symbol} due to lack of exchange {obj.exchange} data')
        elif obj.exchange in ['NASDAQ', 'NYSE'] and not obj.etf:
            mCap, industry = get_usa_details(obj.symbol)
            if mCap:
                if mCap > 1:
                    if obj.symbol in ret_usa['stocks'].keys():
                        obj.capitalisation = ret_usa['stocks'][obj.symbol]['cap']
                        obj.save()
            else:
                print(f'unable to process mCap data for {obj.symbol} {obj.exchange}')
            if industry:
                obj.industry = industry
                obj.save()
            else:
                print(f'unable to process industry data for {obj.symbol} {obj.exchange}')

    update_tracked_stocks()
    store_corporate_actions()

def get_usa_details(symbol):
    mCap = None
    industry = None
    user_agent_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    try:
        summaryDetail = requests.get(f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?formatted=true&crumb=8ldhetOu7RJ&lang=en-US&region=US&modules=summaryDetail&corsDomain=finance.yahoo.com', timeout=15, headers=user_agent_headers)
        summaryDetail = summaryDetail.json()
        print(summaryDetail)
        mCap = summaryDetail['quoteSummary']['result'][0]['summaryDetail']['marketCap']['raw']
    except Exception as ex:
        print(f'Exception {ex} while trying to find market cap for {symbol}')
    try:
        profile = requests.get(f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=assetProfile', timeout=15, headers=user_agent_headers)
        profile = profile.json()
        #print(profile)
        industry = profile['quoteSummary']['result'][0]['assetProfile']['industry']
    except Exception as ex:
        print(f'Exception {ex} while trying to find industry for {symbol}')
    return mCap, industry

def update_tracked_stocks():
    print(f'Updating stocks that need tracking')
    id = list()
    ret_nse_bse = get_nse_bse_map_from_gist()
    added = 0
    removed = 0
    for share in Share.objects.all():
        try:
            s = Stock.objects.get(exchange=share.exchange, symbol=share.symbol)
            id.append(s.id)
        except Stock.DoesNotExist:
            s = Stock.objects.create(
                exchange = share.exchange,
                symbol=share.symbol,
                etf=share.etf,
                collection_start_date=datetime.date.today()
            )
            added += 1
            id.append(s.id)
        if share.exchange in ['NSE','BSE','NSE/BSE']:
            found = False
            for k,v in ret_nse_bse.items():
                if share.exchange=='BSE' and v['bse_security_id'] == share.symbol:
                    found = True
                elif share.exchange in ['NSE', 'NSE/BSE'] and v['nse_symbol'] == share.symbol:
                    found = True
                if found:
                    if v.get('cap', '') != '':
                        s.capitalisation = v['cap']
                    s.isin=k
                    s.save()
                    break
            if not found:
                print(f'failed to find {share.exchange} {share.symbol} in gist')
    for st in Stock.objects.all():
        if st.id not in id:
            st.delete()
            removed += 1
    print(f'summary: added {added} removed {removed}')
