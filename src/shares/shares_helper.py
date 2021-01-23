from .models import Share, Transactions
from .zerodha import Zerodha
from django.db import IntegrityError
from shared.handle_real_time_data import get_latest_vals, get_forex_rate
import datetime
from dateutil.relativedelta import relativedelta

def add_transactions(broker, user, full_file_path):
    if broker == 'ZERODHA':
        zerodha_helper = Zerodha(full_file_path)
        for trans in zerodha_helper.get_transactions():
            print("trans is", trans)
            insert_trans_entry(
                trans["exchange"], trans["symbol"], user, trans["type"], trans["quantity"], trans["price"], trans["date"], trans["notes"], 'ZERODHA')


def insert_trans_entry(exchange, symbol, user, trans_type, quantity, price, date, notes, broker, conversion_rate=1, trans_price=None):
    share_obj = None
    try:
        share_obj = Share.objects.get(exchange=exchange, symbol=symbol)
    except Share.DoesNotExist:
        print("Couldnt find share object exchange:", exchange, " symbol:", symbol)
        share_obj = Share.objects.create(exchange=exchange,
                                             symbol=symbol,
                                             user=user,
                                             quantity=0,
                                             buy_price=0,
                                             buy_value=0,
                                             gain=0)
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
        if trans_type == 'Buy':
            new_qty = float(share_obj.quantity)+quantity
            new_buy_value = float(share_obj.buy_value) + trans_price
            share_obj.quantity = new_qty
            share_obj.buy_value = new_buy_value
            share_obj.buy_price = new_buy_value/float(new_qty)
            share_obj.save()
        else:
            new_qty = float(share_obj.quantity)-quantity
            if new_qty:
                new_buy_value = float(share_obj.buy_value) - trans_price
                share_obj.quantity = new_qty
                share_obj.buy_value = new_buy_value
                share_obj.buy_price = new_buy_value/float(new_qty)
                share_obj.save()
            else:
                share_obj.quantity = 0
                share_obj.buy_value = 0
                share_obj.buy_price = 0
                share_obj.save()
    except IntegrityError:
        print('Transaction exists')



def reconcile_share(share_obj):
    quantity = 0
    buy_value = 0
    buy_price = 0
    sell_quantity = 0
    sell_transactions = Transactions.objects.filter(share=share_obj, trans_type='Sell')
    for trans in sell_transactions:
        sell_quantity = sell_quantity + trans.quantity
    
    buy_transactions = Transactions.objects.filter(share=share_obj, trans_type='Buy').order_by('trans_date')
    for trans in buy_transactions:
        if sell_quantity > 0:
            if sell_quantity > trans.quantity:
                sell_quantity = sell_quantity - trans.quantity
            else:
                quantity = trans.quantity - sell_quantity
                buy_value = quantity*trans.trans_price*trans.conversion_rate
        else:
            quantity = quantity + trans.quantity
            buy_value = buy_value + trans.quantity*trans.trans_price*trans.conversion_rate
    buy_price = buy_value/quantity
    share_obj.quantity = quantity
    share_obj.buy_value = buy_value
    share_obj.buy_price = buy_price
    share_obj.save()

def update_shares_latest_val():
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()
    share_objs = Share.objects.all()
    for share_obj in share_objs:
        latest_date = None
        latest_val = None
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
            share_obj.latest_price = latest_val * float(share_obj.conversion_rate)
            share_obj.save()
        if share_obj.latest_value: 
            share_obj.gain=float(share_obj.latest_value)-float(share_obj.buy_value)
            share_obj.save()