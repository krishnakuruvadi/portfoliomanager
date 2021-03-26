from .models import Share, Transactions
from .zerodha import Zerodha
from django.db import IntegrityError
from shared.handle_real_time_data import get_latest_vals, get_forex_rate
import datetime
from dateutil.relativedelta import relativedelta
from alerts.alert_helper import create_alert, Severity
from common.nse_bse import get_nse_bse
from shared.handle_get import get_user_name_from_id


def shares_add_transactions(broker, user, full_file_path):
    if broker == 'ZERODHA':
        zerodha_helper = Zerodha(full_file_path)
        for trans in zerodha_helper.get_transactions():
            print("trans is", trans)
            insert_trans_entry(
                trans["exchange"], trans["symbol"], user, trans["type"], trans["quantity"], trans["price"], trans["date"], trans["notes"], 'ZERODHA')
    else:
        print(f'unsupported broker {broker}')

def insert_trans_entry(exchange, symbol, user, trans_type, quantity, price, date, notes, broker, conversion_rate=1, trans_price=None):
    try:
        share_obj = None
        try:
            share_obj = Share.objects.get(exchange=exchange, symbol=symbol)
        except Share.DoesNotExist:
            print("Couldnt find share object exchange:", exchange, " symbol:", symbol)
            nse_bse_data = None
            if exchange == 'NSE':
                nse_bse_data = get_nse_bse(symbol, None, None)
            else:
                nse_bse_data = get_nse_bse(None, symbol, None)
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
                                        notes=notes)
            '''
            if trans_type == 'Buy':
                new_qty = float(share_obj.quantity)+quantity
                new_buy_value = float(share_obj.buy_value) + trans_price
                share_obj.quantity = new_qty
                share_obj.buy_value = new_buy_value
                if new_qty > 0:
                    share_obj.buy_price = new_buy_value/float(new_qty)
                else:
                    share_obj.buy_price = 0
                share_obj.save()
            else:
                new_qty = float(share_obj.quantity)-quantity
                if new_qty:
                    new_buy_value = float(share_obj.buy_value) - trans_price
                    share_obj.quantity = new_qty
                    share_obj.buy_value = new_buy_value
                    if new_qty > 0:
                        share_obj.buy_price = new_buy_value/float(new_qty)
                    else:
                        share_obj.buy_price = 0
                    share_obj.save()
                else:
                    share_obj.quantity = 0
                    share_obj.buy_value = 0
                    share_obj.buy_price = 0
                    share_obj.save()
            '''
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
    share_objs = Share.objects.filter(exchange='BSE')
    for share_obj in share_objs:
        nse_bse_data = get_nse_bse(share_obj.symbol, None, None)
        if nse_bse_data:
            isin_shares = Share.objects.filter(exchange='NSE/BSE', symbol=nse_bse_data['bse'], user=share_obj.user)
            if isin_shares:
                merge_content = dict()
                merge_content['bse'] = share_obj.id
                merge_content['isin'] = isin_shares[0].id
                merge_data.append(merge_content)
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
    share_objs = Share.objects.all()
    for share_obj in share_objs:
        reconcile_share(share_obj)

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
                    share_obj.latest_price = float(latest_val)# * float(share_obj.conversion_rate)
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
