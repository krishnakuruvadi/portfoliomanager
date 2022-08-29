from .models import Share, Transactions
from django.db import IntegrityError
from shared.handle_real_time_data import get_in_preferred_currency, get_latest_vals, get_conversion_rate
from shared.utils import get_date_or_none_from_string, get_float_or_zero_from_string
import datetime
from dateutil.relativedelta import relativedelta
from alerts.alert_helper import create_alert, Severity
from common.nse_bse import get_nse_bse
from shared.handle_get import get_user_name_from_id
from common.nse import NSE
from common.nse_historical import NSEHistorical
from bs4 import BeautifulSoup as bs
import requests
from django.conf import settings
import os
import zipfile
import csv
import json
from shared.utils import *
from common.models import Bonusv2, Splitv2, Stock
from tools.stock_reconcile import reconcile_event_based



def shares_add_transactions(broker, user, full_file_path):
    from .zerodha import Zerodha
    if broker == 'ZERODHA':
        zerodha_helper = Zerodha(full_file_path)
        for trans in zerodha_helper.get_transactions():
            print("trans is", trans)
            insert_trans_entry(
                trans["exchange"], trans["symbol"], user, trans["type"], trans["quantity"], trans["price"], trans["date"], trans["notes"], 'ZERODHA')
    else:
        print(f'unsupported broker {broker}')

def check_nse_valid(symbol):
    nse = NSE(None)
    data = nse.get_quote(symbol)
    print(data)
    if not data:
        return False, None
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
    r = requests.get(url, headers=get_bse_headers(), stream=True, timeout=15)
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

    res = requests.get(url, headers=headers, timeout=15)
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
    print(f'adding transaction for exchange {exchange} symbol {symbol}')
    try:
        share_obj = None
        try:
            share_obj = Share.objects.get(exchange=exchange, symbol=symbol, user=user)
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
                if nse_bse_data and 'nse' in nse_bse_data:
                    print(f'checking if {symbol} with nse {nse_bse_data["nse"]} exists')
                    nse_objs = Share.objects.filter(exchange='NSE/BSE',
                                                    symbol=nse_bse_data['nse'],
                                                    user=user)
                    if len(nse_objs) == 1:
                        share_obj = nse_objs[0]
                    else:
                        nse_objs = Share.objects.filter(exchange='NSE',
                                                    symbol=nse_bse_data['nse'],
                                                    user=user)
                        if len(nse_objs) == 1:
                            share_obj = nse_objs[0]
                        else:
                            print(f'share with nse {nse_bse_data["nse"]} doesnt exist')

            if not share_obj:
                print(f'creating share object {exchange} {symbol} for user {user}')
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
            severity=Severity.warning,
            alert_type="Action"
        )

def merge_bse_nse():
    merge_data = list()
    #Filter NSE shares to be merged
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
                    print(f'merge candidate found {share_obj.symbol} {share_obj.id} and {bse_shares[0].symbol} {bse_shares[0].id}')
                    merge_data.append(merge_content)
            isin_shares = Share.objects.filter(exchange='NSE/BSE', symbol=nse_bse_data['nse'], user=share_obj.user)
            if isin_shares:
                merge_content = dict()
                merge_content['nse'] = share_obj.id
                merge_content['isin'] = isin_shares[0].id
                print(f'merge candidate found {share_obj.symbol} {share_obj.id} and {isin_shares[0].symbol} {isin_shares[0].id}')
                merge_data.append(merge_content)
        else:
            print(f'couldnt find data for nse symbol {share_obj.symbol}')

    # Filter BSE shares to be merged
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
            print(f'handling {merge_inst}')
            if 'nse' in merge_inst and 'bse' in merge_inst:
                try:
                    nse_share_obj = Share.objects.get(id=merge_inst['nse'])
                    if 'isin' in merge_inst and merge_inst['isin'] != '':
                        isin_obj = Share.objects.get(id=merge_inst['isin'])
                        print(f'moving transactions from NSE {nse_share_obj.id} to NSE/BSE {isin_obj.id}')
                        for trans in Transactions.objects.filter(share=nse_share_obj):
                            try:
                                trans.share=isin_obj
                                trans.save()
                            except IntegrityError:
                                print(f'Transaction exists.  Deleting instead')
                                trans.delete()
                        print(f"merge_bse_nse nse_share_obj deleting {nse_share_obj.exchange}: {nse_share_obj.symbol}")
                        nse_share_obj.delete()
                        try:
                            bse_share_obj = Share.objects.get(id=merge_inst['bse'])
                            bse_transactions = Transactions.objects.filter(share=bse_share_obj)
                            print(f'moving transactions from BSE {bse_share_obj.id} to NSE/BSE {isin_obj.id}')
                            for trans in bse_transactions:
                                try:
                                    trans.share=isin_obj
                                    trans.save()
                                    print('mapped bse transaction to NSE/BSE object')
                                except IntegrityError:
                                    print(f'Transaction exists.  Deleting instead')
                                    trans.delete()
                            print(f"merge_bse_nse: deleting bse_share_obj {bse_share_obj.exchange}: {bse_share_obj.symbol}")
                            bse_share_obj.delete()
                        except Share.DoesNotExist:
                            print(f"Might be already deleted BSE: {merge_inst['bse']}")

                    else:
                        print(f'{nse_share_obj.symbol} : merging {merge_inst["bse"]} into {merge_inst["nse"]}')
                        nse_share_obj.exchange = 'NSE/BSE'
                        nse_share_obj.save()
                        print('changed exchange to NSE/BSE')
                        bse_share_obj = Share.objects.get(id=merge_inst['bse'])
                        bse_transactions = Transactions.objects.filter(share=bse_share_obj)
                        for trans in bse_transactions:
                            try:
                                trans.share=nse_share_obj
                                trans.save()
                                print('mapped bse transaction to NSE/BSE object')
                            except IntegrityError:
                                print(f'Transaction exists.  Deleting instead')
                                trans.delete()
                        print(f"merge_bse_nse 351 deleting bse_share_obj {bse_share_obj.exchange}: {bse_share_obj.symbol}")
                        bse_share_obj.delete()
                except Share.DoesNotExist:
                    print(f"Might be already deleted NSE: {merge_inst['nse']}")
            elif 'nse' in merge_inst and 'isin' in merge_inst:
                try:
                    nse_share_obj = Share.objects.get(id=merge_inst['nse'])
                    isin_share_obj = Share.objects.get(id=merge_inst['isin'])
                    print(f'{nse_share_obj.symbol} : merging {merge_inst["nse"]} into {merge_inst["isin"]}')
                    nse_transactions = Transactions.objects.filter(share=nse_share_obj)
                    for trans in nse_transactions:
                        try:
                            trans.share=isin_share_obj
                            trans.save()
                            print('mapped nse transaction to NSE/BSE object')
                        except IntegrityError:
                            print(f'Transaction exists.  Deleting instead')
                            trans.delete()
                    print(f"merge_bse_nse 369 nse_share_obj deleting {nse_share_obj.exchange}: {nse_share_obj.symbol}")
                    nse_share_obj.delete()
                except Share.DoesNotExist:
                    print(f"Might be already deleted NSE: {merge_inst['nse']}")

            elif 'bse' in merge_inst and 'isin' in merge_inst:
                try:
                    bse_share_obj = Share.objects.get(id=merge_inst['bse'])
                    isin_share_obj = Share.objects.get(id=merge_inst['isin'])
                    print(f'{bse_share_obj.symbol} : merging {merge_inst["bse"]} into {merge_inst["isin"]}')
                    bse_transactions = Transactions.objects.filter(share=bse_share_obj)
                    for trans in bse_transactions:
                        try:
                            trans.share=isin_share_obj
                            trans.save()
                            print('mapped bse transaction to NSE/BSE object')
                        except IntegrityError:
                            print(f'Transaction exists.  Deleting instead')
                            trans.delete()
                    print(f"merge_bse_nse 388 bse_share_obj deleting {bse_share_obj.exchange}: {bse_share_obj.symbol}")
                    bse_share_obj.delete()
                except Share.DoesNotExist:
                    print(f"Might be already deleted BSE: {merge_inst['bse']}")
            else:
                print(f'ignoring {merge_inst}')
    else:
        print('nothing to merge')
    print('done with merging shares')


def reconcile_shares(log_calc=False):
    merge_bse_nse()
    share_objs = Share.objects.all()
    for share_obj in share_objs:
        reconcile_share(share_obj)

    check_discrepancies()


def reconcile_share(share_obj):
    transactions = Transactions.objects.filter(share=share_obj).order_by('trans_date')
    try:
        stock = Stock.objects.get(exchange=share_obj.exchange, symbol=share_obj.symbol)
    except Stock.DoesNotExist:
        from common.shares_helper import update_tracked_stocks
        update_tracked_stocks()
        update_share_latest_val(share_obj)
    try:
        stock = Stock.objects.get(exchange=share_obj.exchange, symbol=share_obj.symbol)
        bonuses = Bonusv2.objects.filter(stock=stock)
        splits = Splitv2.objects.filter(stock=stock)
        round_qty_to_int = True if share_obj.exchange in ['NSE', 'BSE', 'NSE/BSE'] else False
        qty, buy_value, buy_price, realised_gain, unrealised_gain = reconcile_event_based(transactions, bonuses, splits, round_qty_to_int=round_qty_to_int, latest_price=share_obj.latest_price, latest_conversion_rate=share_obj.conversion_rate)
        share_obj.quantity = qty
        share_obj.buy_value = buy_value
        share_obj.buy_price = buy_price
        share_obj.realised_gain = realised_gain
        share_obj.gain = unrealised_gain
        if qty > 0:
            share_obj.latest_value = share_obj.latest_price * share_obj.quantity*share_obj.conversion_rate
        else:
            share_obj.latest_value = 0
            share_obj.conversion_rate = 0
        share_obj.save()
        roi = 0
        if qty > 0:
            roi = get_roi(transactions, share_obj.latest_value)
        share_obj.roi = roi
        share_obj.save()
    except Stock.DoesNotExist:
        description='Stock not found in db. No splits/bonuses data available.  This affects other calculations.'
        create_alert(
            summary=f'{share_obj.exchange} {share_obj.symbol}  not found in db.',
            content=description,
            severity=Severity.warning,
            alert_type="Application"
        )
    except Exception as ex:
        print(f'exception {ex} when reconciling {share_obj.exchange} {share_obj.symbol}')

def get_roi(transactions, latest_value):
    from shared.financial import xirr
    roi = 0
    try:
        cash_flows = list()
        for t in transactions:
            if t.trans_type == 'Buy':
                cash_flows.append((t.trans_date, -1*float(t.trans_price)))
            else:
                cash_flows.append((t.trans_date, float(t.trans_price)))
        if latest_value > 0:
            cash_flows.append((datetime.date.today(), float(latest_value)))
        roi = xirr(cash_flows, 0.1)*100
        roi = round(roi, 2)
    except Exception as ex:
        print(f'exception {ex} when getting roi {roi} with cash flows {cash_flows}')
        roi = 0
    return roi

'''
def reconcile_share(share_obj, log_calc=False):
    quantity = 0
    buy_value = 0
    buy_price = 0
    realised_gain = 0
    transactions = Transactions.objects.filter(share=share_obj).order_by('trans_date')
    last_trans = None
    if log_calc:
        print('***********************************************************************************')
        print(f'    {share_obj.exchange} {share_obj.symbol}')
        print('***********************************************************************************')
    try:
        stock = Stock.objects.get(exchange=share_obj.exchange, symbol=share_obj.symbol)
        for trans in transactions:
            #print(f"start at {str(quantity)}")
            if last_trans and quantity>0:
                #https://www.chittorgarh.com/faq/what_is_bonus_share_and_its_record_date/95/
                bonus = Bonusv2.objects.filter(stock=stock, record_date__lte=trans.trans_date, record_date__gte=last_trans.trans_date)
                for b in bonus:
                    quantity = quantity + (quantity*b.ratio_num)/b.ratio_denom
                    if share_obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        quantity = int(quantity)
                    if log_calc:
                        print(f'{b.date}: {quantity}')
                split = Splitv2.objects.filter(stock=stock, ex_date__lte=trans.trans_date, ex_date__gte=last_trans.trans_date)
                for s in split:
                    quantity = (quantity*s.old_fv)/s.new_fv
                    if share_obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        quantity = int(quantity)
                    if log_calc:
                        print(f'{s.date}: {quantity}')
                #print(f"After bonus and split at {str(quantity)}")
            if trans.trans_type == 'Buy':
                quantity += trans.quantity
                buy_value += trans.trans_price
            else:
                if quantity != 0:
                    realised_gain += trans.trans_price - ((buy_value*trans.quantity)/quantity)
                else:
                    realised_gain += trans.trans_price
                quantity -= trans.quantity
            if log_calc:
                print(f'{trans.trans_date}: {trans.trans_type} {trans.quantity}, {quantity}')
            #print(f"After transaction {trans.trans_type} on {trans.trans_date} at {str(quantity)}")
            last_trans = trans
        
        if quantity > 0:
            sqty = quantity
            if last_trans:
                bonus = Bonusv2.objects.filter(stock=stock, record_date__lte=datetime.date.today(), record_date__gte=last_trans.trans_date)
                for b in bonus:
                    quantity = quantity + (quantity*b.ratio_num)/b.ratio_denom
                    if share_obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        quantity = int(quantity)
                    if log_calc:
                        print(f'{b.date}: {quantity}')
                split = Splitv2.objects.filter(stock=stock, ex_date__lte=datetime.date.today(), ex_date__gte=last_trans.trans_date)
                for s in split:
                    quantity = (quantity*s.old_fv)/s.new_fv
                    if share_obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        quantity = int(quantity)
                    if log_calc:
                        print(f'{s.date}: {quantity}')
            if quantity > 0:
                buy_price = buy_value/quantity
            else:
                print(f"weird that we started at {str(sqty)} and ended up with {str(quantity)} after bonus and split for {share_obj.symbol}")
        elif quantity < 0:
            description='Selling more than available. This affects other calculations. Please correct'
            create_alert(
                summary=share_obj.symbol + ' Quantity adding up to ' + str(quantity) + '. This affects other calculations.',
                content=description,
                severity=Severity.warning
            )
            quantity = 0
        else:
            buy_price = 0
        if log_calc:
            print('***********************************************************************************')
            print(f'    {quantity}')
            print('***********************************************************************************')
        #print(f'ended up with {str(quantity)}')
        share_obj.quantity = quantity
        share_obj.buy_value = buy_value
        share_obj.buy_price = buy_price
        share_obj.realised_gain = realised_gain
        if share_obj.latest_price and share_obj.conversion_rate:
            share_obj.latest_value = share_obj.quantity*share_obj.latest_price*share_obj.conversion_rate
            share_obj.gain = share_obj.latest_value-share_obj.buy_value
        share_obj.save()
    except Stock.DoesNotExist:
        print(f'no stock found {share_obj.exchange} {share_obj.symbol}')
'''

def check_discrepancies():
    share_objs = Share.objects.all()
    '''
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
    '''

def move_trans(from_share_obj, to_share_obj, delete_from_share_obj=False):
    print(f'moving transactions from {from_share_obj.exchange}:{from_share_obj.symbol} to {to_share_obj.exchange}:{to_share_obj.symbol}')
    for trans in Transactions.objects.filter(share=from_share_obj):
        trans.share = to_share_obj
        try:
            trans.save()
        except IntegrityError:
            trans.delete()
    if delete_from_share_obj:
        print(f'move_trans: deleting {from_share_obj.exchange}:{from_share_obj.symbol}')
        try:
            from_share_obj.delete()
        except Exception as ex:
            print(f'failed to delete object {ex}')


def update_shares_latest_val():
    share_objs = Share.objects.all()
    for share_obj in share_objs:
        if share_obj.quantity > 0:
            update_share_latest_val(share_obj)
        elif share_obj.quantity == 0:
            share_obj.latest_value = 0
            share_obj.latest_price = 0
            share_obj.gain= 0
            share_obj.roi = 0
            share_obj.as_on_date = datetime.date.today()
            share_obj.save()
        else:
            print(f'ignoring {share_obj.symbol} with -ve quantity')

def update_share_latest_val(share_obj):
    try:
        start = datetime.date.today()+relativedelta(days=-5)
        end = datetime.date.today()
        latest_date = None
        latest_val = None
        if (share_obj.as_on_date and share_obj.as_on_date < datetime.date.today()) or not share_obj.as_on_date:
            vals = get_latest_vals(share_obj.symbol, share_obj.exchange, start, end, share_obj.etf)
            if vals:
                for k, v in vals.items():
                    if k and v:
                        if not latest_date or k > latest_date:
                            latest_date = k
                            latest_val = v
            else:
                print(f'Couldnt get latest value for {share_obj.symbol} {share_obj.exchange}')
                if share_obj.exchange == 'BSE':
                    isin = None
                    for trans in Transactions.objects.filter(share=share_obj):
                        isin = get_isin_from_bhav_copy(share_obj.symbol, trans.trans_date)
                        if isin:
                            break
                    if isin:
                        nse_bse_data = get_nse_bse(None, None, isin)
                        if nse_bse_data and 'nse' in nse_bse_data:
                            print(f'checking if share with symbol {nse_bse_data["nse"]} exists')
                            isin_objs = Share.objects.filter(exchange='NSE/BSE',
                                                    symbol=nse_bse_data['nse'])
                            if len(isin_objs) == 1:
                                move_trans(share_obj, isin_objs[0], True)
                                return

                            else:
                                nse_objs = Share.objects.filter(exchange='NSE', symbol=nse_bse_data['nse'])
                                if len(nse_objs) == 1:
                                    move_trans(share_obj, nse_objs[0], True)
                                    nse_objs[0].exchange = 'NSE/BSE'
                                    nse_objs[0].save()
                                    return

                        if 'bse' in nse_bse_data:
                            try:
                                bse_obj = Share.objects.get(exchange='BSE', symbol=nse_bse_data['bse'])
                                move_trans(share_obj, bse_obj, True)
                            except Share.DoesNotExist:
                                share_obj.symbol = nse_bse_data['bse']
                                share_obj.save()
                            return
                    else:
                        print(f'couldnt find isin for {share_obj.symbol} {share_obj.exchange} using transaction date bhav copy')
                elif share_obj.exchange == 'NSE':
                    valid, _ = check_nse_valid(share_obj.symbol)
                    if not valid:
                        trans = Transactions.objects.filter(share=share_obj).order_by('-trans_date')
                        if len(trans) > 0:
                            bhavcopy_symbol = share_obj.symbol
                            while True:
                                nh = NSEHistorical(bhavcopy_symbol, trans[0].trans_date, True)
                                isin = nh.get_isin_from_bhav_copy()
                                if isin:
                                    n = NSE('')
                                    symbol = n.get_symbol(isin)
                                    if symbol:
                                        nse_objs = Share.objects.filter(exchange='NSE', symbol=symbol)
                                        if len(nse_objs) == 1:
                                            move_trans(share_obj, nse_objs[0], True)
                                        else:
                                            nse_objs = Share.objects.filter(exchange='NSE/BSE', symbol=symbol)
                                            if len(nse_objs) == 1:
                                                move_trans(share_obj, nse_objs[0], True)
                                            else:
                                                share_obj.symbol = symbol
                                                share_obj.save()
                                                break
                                    else:
                                        print(f'Failed to get symbol from isin {isin}')
                                else:
                                    print(f'couldnt find isin for {share_obj.symbol} {share_obj.exchange} using transaction date bhav copy')
                                    if '-' in bhavcopy_symbol:
                                        bhavcopy_symbol = bhavcopy_symbol[0:bhavcopy_symbol.rfind('-')]
                                    else:
                                        break
            if latest_date and latest_val:
                share_obj.as_on_date = latest_date
                if share_obj.exchange in ['NASDAQ', 'NYSE']:
                    share_obj.conversion_rate = get_in_preferred_currency(1, 'USD', k)
                elif share_obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                    share_obj.conversion_rate = get_in_preferred_currency(1, 'INR', k)
                else:
                    share_obj.conversion_rate = 1
                share_obj.latest_value = float(latest_val) * float(share_obj.conversion_rate) * float(share_obj.quantity)
                share_obj.latest_price = float(latest_val)
                share_obj.save()
            else:
                create_alert(
                    summary=share_obj.exchange + ':' + share_obj.symbol + ' - Failed to get latest value',
                    content=share_obj.exchange + ':' + share_obj.symbol + ' - Failed to get latest value',
                    severity=Severity.warning,
                    alert_type="Action"
                )
            if share_obj.latest_value:
                share_obj.gain=float(share_obj.latest_value)-float(share_obj.buy_value)
                share_obj.save()

    except Exception as ex:
        print(f'exception updating latest value for {share_obj.symbol} {share_obj.exchange} {ex}')

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
                            trans_type = 'Buy' if trans_type.lower()=='buy' else 'Sell'
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
                                
                            if exchange in ['NSE', 'BSE', 'NSE/BSE']:
                                conversion_rate = get_in_preferred_currency(1, 'INR', date)
                            elif exchange in ['NASDAQ', 'NYSE']:
                                conversion_rate = get_in_preferred_currency(1, 'USD', date)
                            else:
                                raise Exception('unsupported exchange %s' %exchange)
                            insert_trans_entry(exchange, symbol, user, trans_type, quantity, price, date, notes, broker, conversion_rate)
                        except Exception as ex:
                            print(f'Exception adding transaction {ex}')
        else:
            print(f'untracked shares transactions file not present')
    else:
        print(f'untracked shares transactions folder not present')

def get_invested_shares():
    ret = list()
    for share in Share.objects.all():
        s = dict()
        s['exchange'] = share.exchange
        s['symbol'] = share.symbol
        ret.append(s)
    return ret

def pull_and_store_corporate_actions():
    from common.shares_helper import pull_corporate_actions, process_corporate_actions, store_corporate_actions
    for share in Share.objects.all():
        transactions = Transactions.objects.filter(share=share).order_by('trans_date')
        from_date = transactions[0].trans_date
        if share.exchange == 'NSE/BSE':
            pull_corporate_actions(share.symbol, 'NSE', from_date, datetime.date.today())
        elif share.exchange == 'NSE':
            pull_corporate_actions(share.symbol, share.exchange, from_date, datetime.date.today())
        elif share.exchange == 'BSE':
            print(f'not supported exchange BSE')
        else:
            print(f'not supported exchange {share.exchange}')
    process_corporate_actions()
    store_corporate_actions()

def handle_symbol_change(old_symbol, old_exchange, new_symbol, new_exchange):
    for share in Share.objects.filter(exchange=old_exchange, symbol=old_symbol):
        try:
            new_share = Share.objects.get(exchange=new_exchange, symbol=new_symbol, user=share.user)
            move_trans(share, new_share, True)
        except Share.DoesNotExist:
            share.exchange = new_exchange
            share.symbol = new_symbol
            share.save()
