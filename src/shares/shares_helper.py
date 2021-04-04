from .models import Share, Transactions
from .zerodha import Zerodha
from django.db import IntegrityError
from shared.handle_real_time_data import get_latest_vals, get_forex_rate
from shared.utils import get_date_or_none_from_string, get_float_or_zero_from_string
import datetime
from dateutil.relativedelta import relativedelta
from alerts.alert_helper import create_alert, Severity
from common.nse_bse import get_nse_bse
from shared.handle_get import get_user_name_from_id
from nsetools import Nse
from bs4 import BeautifulSoup as bs
import requests
from django.conf import settings
import os
import zipfile
import csv
import json


def shares_add_transactions(broker, user, full_file_path):
    if broker == 'ZERODHA':
        zerodha_helper = Zerodha(full_file_path)
        for trans in zerodha_helper.get_transactions():
            print("trans is", trans)
            insert_trans_entry(
                trans["exchange"], trans["symbol"], user, trans["type"], trans["quantity"], trans["price"], trans["date"], trans["notes"], 'ZERODHA')
    else:
        print(f'unsupported broker {broker}')

def check_nse_valid(symbol):
    nse = Nse()
    data = nse.get_quote(symbol)
    print(data)
    if not data:
        return False
    return True, data['isinCode']

def clean_string(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

def get_bse_headers():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36 Edg/83.0.478.45'
    }
    return headers

def download_url(url, save_path, chunk_size=128):
    print(f'getting url {url}')
    r = requests.get(url, headers=get_bse_headers(), stream=True)
    if r.status_code == 200:
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)
        return True
    return False

def get_bhav_path():
    return os.path.join(settings.MEDIA_ROOT, 'bhav_copy')

def get_bhav_copy(date):
    if date > datetime.date(year=2007, month=1, day=2):
        csv_zip_file_name='eq'+date.strftime('%d%m%y')+'_csv.zip'
        bhav_copy_url = 'https://www.bseindia.com/download/BhavCopy/Equity/' + csv_zip_file_name
        bc_path = get_bhav_path()
        if not os.path.exists(bc_path):
            os.makedirs(bc_path)
        bc_zip_file = os.path.join(bc_path,csv_zip_file_name)
        bc_file = os.path.join(bc_path,'EQ'+date.strftime('%d%m%y')+'.CSV')
        if not os.path.exists(bc_zip_file):
            if download_url(bhav_copy_url, bc_zip_file):
                with zipfile.ZipFile(os.path.join(bc_path,bc_zip_file), 'r') as zip_ref:
                    zip_ref.extractall(bc_path)
                return bc_file
            else:
                print(f'failed to download bhav copy for date {date}')
        else:
            if os.path.exists(bc_file):
                return bc_file
            elif os.path.exists(bc_zip_file):
                with zipfile.ZipFile(os.path.join(bc_path,bc_zip_file), 'r') as zip_ref:
                    zip_ref.extractall(bc_path)
                return bc_file
    return None


def check_bse_valid(symbol, bse_code):
    headers = get_bse_headers()
    if symbol:
        url = 'https://api.bseindia.com/Msource/90D/getQouteSearch.aspx?Type=EQ&text=' + symbol + '&flag=gq'
    elif bse_code:
        url = 'https://api.bseindia.com/Msource/90D/getQouteSearch.aspx?Type=EQ&text=' + bse_code + '&flag=gq'
    else:
        return False, None, None

    res = requests.get(url, headers=headers)
    c = res.content
    soup = bs(c, "lxml")
    for span in soup('span'):
        decoded = span.decode_contents()
        decoded = decoded.replace('<strong>','').replace('</strong>','')
        decoded = clean_string(decoded)
        print(f'decoded {decoded}')
        splitcontent = decoded.split(' ')
        for s in splitcontent:
            print(s)
        isin = None
        if symbol:
            if splitcontent[0] == symbol:
                for sp in splitcontent:
                    if sp != '' and sp != symbol:
                        if not isin:
                            isin = sp
                        else:
                            bse_code = sp
                return True, isin, bse_code

        else:
            found = False
            for sp in splitcontent:
                if sp == bse_code:
                    found = True
            if found:
                for sp in splitcontent:
                    if sp != '' and sp != bse_code:
                        if not symbol:
                            symbol = sp
                        else:
                            isin = sp
                        
                return True, isin, bse_code

    return False, None, None

def check_valid(exchange, symbol, date):
    if exchange == 'NSE':
        valid, isin = check_nse_valid(symbol)
    elif exchange == 'BSE':
        valid, isin, bse_code = check_bse_valid(symbol, None)
        if not valid:
            get_isin_from_bhav_copy(symbol, date)
    elif exchange == 'NASDAQ':
        return symbol
    return None

def get_isin_from_bhav_copy(symbol, date):
    isin_file = os.path.join(get_bhav_path(), 'bse_isin.json')
    if os.path.exists(isin_file):
        with open(isin_file) as f:
            data = json.load(f)
            if symbol in data:
                return data[symbol]['isin']
    bc = get_bhav_copy(date)
    try:
        if bc:
            with open(bc, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    if row['SC_NAME'] == symbol or row['SC_NAME'].replace(' ','').replace('.','') == symbol.replace(' ','').replace('.',''):
                        valid, isin, bse_code = check_bse_valid(None, row['SC_CODE'])
                        if valid:
                            data = None
                            if os.path.exists(isin_file):
                                with open(isin_file) as f:
                                    data = json.load(f)
                            else:
                                data = dict()
                            if not symbol in data:
                                data[symbol] = dict()
                            data[symbol]['isin'] = isin
                            with open(isin_file, 'w') as json_file:
                                json.dump(data, json_file)
                            return isin
    except Exception as ex:
        print(f'Exception opening {bc} : {ex}')

    print(f'No isin for {symbol} on {date}')
    return None

def insert_trans_entry(exchange, symbol, user, trans_type, quantity, price, date, notes, broker, conversion_rate=1, trans_price=None, div_reinv=False):
    try:
        share_obj = None
        try:
            share_obj = Share.objects.get(exchange=exchange, symbol=symbol)
        except Share.DoesNotExist:
            if exchange == 'NSE' or exchange == 'BSE':
                print("Couldnt find share object exchange:", exchange, " symbol:", symbol)
                nse_bse_data = None
                if exchange == 'NSE':
                    nse_bse_data = get_nse_bse(symbol, None, None)
                else:
                    nse_bse_data = get_nse_bse(None, symbol, None)
                    if not nse_bse_data:
                        isin = get_isin_from_bhav_copy(symbol, date)
                        if isin:
                            nse_bse_data = get_nse_bse(None, None, isin)
                if nse_bse_data and 'isin' in nse_bse_data:
                    print(f'checking if {symbol} with isin exists {nse_bse_data["isin"]}')
                    isin_objs = Share.objects.filter(exchange='NSE/BSE',
                                                    symbol=nse_bse_data['isin'])
                    if len(isin_objs) == 1:
                        share_obj = isin_objs[0]
                    else:
                        print(f'share with isin {nse_bse_data["isin"]} doesnt exist')

            if not share_obj:
                share_obj = Share.objects.create(exchange=exchange,
                                                symbol=symbol,
                                                user=user,
                                                quantity=0,
                                                buy_price=0,
                                                buy_value=0,
                                                gain=0,
                                                realised_gain=0
                                                )
        if not trans_price:
            trans_price = price*quantity*conversion_rate
        try:
            Transactions.objects.create(share=share_obj,
                                        trans_date=date,
                                        trans_type=trans_type,
                                        price=price,
                                        quantity=quantity,
                                        conversion_rate=conversion_rate,
                                        trans_price=trans_price,
                                        broker=broker,
                                        notes=notes,
                                        div_reinv=div_reinv)
            reconcile_share(share_obj)
        except IntegrityError:
            print('Transaction exists')
    except Exception as ex:
        print(f'failed to add transaction {exchange}, {symbol}, {user}, {trans_type}, {quantity}, {price}, {date}, {notes}, {broker}')
        print(ex)
        description = 'failed to add transaction for ' + exchange + ':' + symbol + ' for user ' + get_user_name_from_id(user)
        create_alert(
                summary=exchange + ':' + symbol + ' - Failed to add transaction',
                content=description,
                severity=Severity.warning
        )

def merge_bse_nse():
    merge_data = list()
    share_objs = Share.objects.filter(exchange='NSE')
    for share_obj in share_objs:
        nse_bse_data = get_nse_bse(share_obj.symbol, None, None)
        if nse_bse_data:
            if 'bse' in nse_bse_data and nse_bse_data['bse']:
                bse_shares = Share.objects.filter(exchange='BSE', symbol=nse_bse_data['bse'], user=share_obj.user)
                if bse_shares:
                    merge_content = dict()
                    merge_content['nse'] = share_obj.id
                    merge_content['bse'] = bse_shares[0].id
                    merge_data.append(merge_content)
            isin_shares = Share.objects.filter(exchange='NSE/BSE', symbol=nse_bse_data['nse'], user=share_obj.user)
            if isin_shares:
                merge_content = dict()
                merge_content['nse'] = share_obj.id
                merge_content['isin'] = isin_shares[0].id
                merge_data.append(merge_content)
        else:
            print(f'couldnt find data for nse symbol {share_obj.symbol}')
    share_objs = Share.objects.filter(exchange='BSE')
    for share_obj in share_objs:
        nse_bse_data = get_nse_bse(None, share_obj.symbol, None)
        if not nse_bse_data:
            trans = Transactions.objects.filter(share=share_obj)
            if len(trans) > 0:
                isin = get_isin_from_bhav_copy(share_obj.symbol, trans[0].trans_date)
                if isin:
                    nse_bse_data = get_nse_bse(None, None, isin)
        if nse_bse_data:
            isin_shares = Share.objects.filter(exchange='NSE/BSE', symbol=nse_bse_data['bse'], user=share_obj.user)
            if isin_shares:
                merge_content = dict()
                merge_content['bse'] = share_obj.id
                merge_content['isin'] = isin_shares[0].id
                merge_data.append(merge_content)
            if 'nse' in nse_bse_data:
                nse_shares = Share.objects.filter(exchange='NSE', symbol=nse_bse_data['nse'], user=share_obj.user)
                if nse_shares:
                    merge_content = dict()
                    merge_content['bse'] = share_obj.id
                    merge_content['nse'] = nse_shares[0].id
                    merge_data.append(merge_content)
        else:
            print(f'couldnt find data for bse symbol {share_obj.symbol}')
    if len(merge_data) > 0:
        print(f'Merge data {merge_data}')
        for merge_inst in merge_data:
            if 'nse' in merge_inst and 'bse' in merge_inst:
                nse_share_obj = Share.objects.get(id=merge_inst['nse'])
                print(f'{nse_share_obj.symbol} : merging {merge_inst["bse"]} into {merge_inst["nse"]}')
                nse_share_obj.exchange = 'NSE/BSE'
                nse_share_obj.save()
                print('changed exchange to NSE/BSE')
                bse_share_obj = Share.objects.get(id=merge_inst['bse'])
                bse_transactions = Transactions.objects.filter(share=bse_share_obj)
                for trans in bse_transactions:
                    trans.share=nse_share_obj
                    trans.save()
                    print('mapped bse transaction to NSE/BSE object')
                bse_share_obj.delete()
            elif 'nse' in merge_inst:
                nse_share_obj = Share.objects.get(id=merge_inst['nse'])
                isin_share_obj = Share.objects.get(id=merge_inst['isin'])
                print(f'{nse_share_obj.symbol} : merging {merge_inst["nse"]} into {merge_inst["isin"]}')
                nse_transactions = Transactions.objects.filter(share=nse_share_obj)
                for trans in nse_transactions:
                    trans.share=isin_share_obj
                    trans.save()
                    print('mapped nse transaction to NSE/BSE object')
                nse_share_obj.delete()
            else:
                bse_share_obj = Share.objects.get(id=merge_inst['bse'])
                isin_share_obj = Share.objects.get(id=merge_inst['isin'])
                print(f'{bse_share_obj.symbol} : merging {merge_inst["bse"]} into {merge_inst["isin"]}')
                bse_transactions = Transactions.objects.filter(share=bse_share_obj)
                for trans in bse_transactions:
                    trans.share=isin_share_obj
                    trans.save()
                    print('mapped bse transaction to NSE/BSE object')
                bse_share_obj.delete()
    else:
        print('nothing to merge')


def reconcile_shares():
    merge_bse_nse()
    share_objs = Share.objects.all()
    for share_obj in share_objs:
        reconcile_share(share_obj)
    check_discrepancies()

def reconcile_share(share_obj):
    quantity = 0
    buy_value = 0
    buy_price = 0
    sell_quantity = 0
    realised_gain = 0
    sell_transactions = Transactions.objects.filter(share=share_obj, trans_type='Sell')
    for trans in sell_transactions:
        sell_quantity = sell_quantity + trans.quantity
        realised_gain = realised_gain + trans.trans_price
    
    buy_transactions = Transactions.objects.filter(share=share_obj, trans_type='Buy').order_by('trans_date')
    for trans in buy_transactions:
        if sell_quantity > 0:
            if sell_quantity > trans.quantity:
                sell_quantity = sell_quantity - trans.quantity
                realised_gain = realised_gain - trans.trans_price
            else:
                quantity = trans.quantity - sell_quantity
                realised_gain = realised_gain - (trans.trans_price*sell_quantity/trans.quantity)
                sell_quantity = 0
                buy_value = quantity*trans.price*trans.conversion_rate
        else:
            quantity = quantity + trans.quantity
            buy_value = buy_value + trans.trans_price
    if quantity > 0:
        buy_price = buy_value/quantity
    else:
        buy_price = 0
    share_obj.quantity = quantity
    share_obj.buy_value = buy_value
    share_obj.buy_price = buy_price
    share_obj.realised_gain = realised_gain
    share_obj.save()        

def check_discrepancies():
    share_objs = Share.objects.all()
    for share_obj in share_objs:
        total_shares = 0
        for trans in Transactions.objects.filter(share=share_obj):
            if trans.trans_type=='Buy':
                total_shares += trans.quantity
            else:
                total_shares -= trans.quantity
        if total_shares < 0:
            description='Selling more than available. This affects other calculations. Please correct'
            create_alert(
                summary=share_obj.symbol + ' Quantity adding up to ' + str(total_shares) + '. This affects other calculations.',
                content=description,
                severity=Severity.warning
            )

def update_shares_latest_val():
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()
    share_objs = Share.objects.all()
    for share_obj in share_objs:
        if share_obj.quantity > 0:
            latest_date = None
            latest_val = None
            if (share_obj.as_on_date and share_obj.as_on_date < datetime.date.today()) or not share_obj.as_on_date:
                vals = get_latest_vals(share_obj.symbol, share_obj.exchange, start, end)
                if vals:
                    for k, v in vals.items():
                        if k and v:
                            if not latest_date or k > latest_date:
                                latest_date = k
                                latest_val = v
                if latest_date and latest_val:
                    share_obj.as_on_date = latest_date
                    if share_obj.exchange == 'NASDAQ':
                        share_obj.conversion_rate = get_forex_rate(k, 'USD', 'INR')
                    else:
                        share_obj.conversion_rate = 1
                    share_obj.latest_value = float(latest_val) * float(share_obj.conversion_rate) * float(share_obj.quantity)
                    share_obj.latest_price = float(latest_val)
                    share_obj.save()
                if share_obj.latest_value: 
                    share_obj.gain=float(share_obj.latest_value)-float(share_obj.buy_value)
                    share_obj.save()
        elif share_obj.quantity == 0:
            share_obj.latest_value = 0
            share_obj.latest_price = 0
            share_obj.gain= 0
            share_obj.as_on_date = datetime.date.today()
            share_obj.save()
        else:
            print(f'ignoring {share_obj.symbol} with -ve quantity')

def add_untracked_transactions():
    trans_path = os.path.join(settings.MEDIA_ROOT,'untracked_shares_transactions')
    if os.path.exists(trans_path):
        trans_file = os.path.join(trans_path, 'transactions.csv')
        if os.path.exists(trans_file):
            with open(trans_file, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    if row['trading_symbol'] != 'IGNORETRANS':
                        print(row)
                        #user,exchange,trade_date,trading_symbol,segment,trade_type,quantity,price,order_id,notes,broker
                        try:
                            exchange = row['exchange']
                            symbol = row['trading_symbol']
                            trans_type = row['trade_type']
                            user = int(row['user'])
                            user_name = get_user_name_from_id(user)
                            if not user_name:
                                raise Exception('User %s doesnt exist' %str(user))
                            broker = row['broker']
                            notes = row['notes']
                            date = get_date_or_none_from_string(row['trade_date'],format='%d/%m/%Y')
                            quantity = get_float_or_zero_from_string(row['quantity'])
                            price = get_float_or_zero_from_string(row['price'])
                            if row['order_id'] and row['order_id'] != '':
                                if not notes or notes == '':
                                    notes = 'order id:' + row['order_id']
                                else:
                                    notes = notes + '. order id:' + row['order_id'] 
                                
                            if exchange == 'NSE' or exchange == 'BSE':
                                conversion_rate = 1
                            elif exchange == 'NASDAQ' or exchange == 'NYSE':
                                conversion_rate = get_forex_rate(date, 'USD', 'INR')
                            else:
                                raise Exception('unsupported exchange %s' %exchange)
                            insert_trans_entry(exchange, symbol, user, trans_type, quantity, price, date, notes, broker, conversion_rate)
                        except Exception as ex:
                            print(f'Exception adding transaction {ex}')
        else:
            print(f'untracked shares transactions file not present')
    else:
        print(f'untracked shares transactions folder not present')