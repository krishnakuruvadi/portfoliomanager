import csv
from os.path import isfile
from shared.utils import *

class Zerodha:
    def __init__(self, filename):
        self.filename = filename
        self.broker = 'ZERODHA'
    
    def get_transactions(self):
        if isfile(self.filename):
            with open(self.filename, mode='r', encoding='utf-8-sig') as csv_file:
                print("opened file as csv:", self.filename)
                csv_reader = csv.DictReader(csv_file, delimiter=",")
                last_order = ''
                symbol=''
                exchange=''
                trans_type=''
                qty = 0
                price=0
                tran_date=None
                for row in csv_reader:
                    if 'order_id' not in row:
                        break
                    print(row)
                    if last_order == row['order_id']:
                        new_qty = int(get_float_or_none_from_string(row['quantity']))
                        new_price = get_float_or_none_from_string(row['price'])
                        new_total = new_qty*new_price
                        old_total = qty*price
                        price = (old_total+new_total)/float(new_qty+qty)
                        qty = new_qty+qty
                    else:
                        if last_order != '':
                            trans = dict()
                            trans["exchange"] = exchange
                            trans["symbol"] = symbol
                            trans["type"] = trans_type
                            trans["quantity"] = qty
                            trans["price"] = price
                            trans["date"] = tran_date
                            trans["notes"] = 'order id:'+last_order
                            yield trans

                        tran_date = get_datetime_or_none_from_string(row['trade_date'])
                        exchange = row['exchange']
                        trans_type = 'Sell' if row['trade_type']=='sell' else 'Buy'
                        last_order = row['order_id']
                        symbol = row['symbol']
                        symbol = symbol[0:None if -1==symbol.find('-') else symbol.find('-')]
                        qty = int(get_float_or_none_from_string(row['quantity']))
                        price = get_float_or_none_from_string(row['price'])
                if last_order != '':
                    trans = dict()
                    trans["exchange"] = exchange
                    trans["symbol"] = symbol
                    trans["type"] = trans_type
                    trans["quantity"] = qty
                    trans["price"] = price
                    trans["date"] = tran_date
                    trans["notes"] = 'order id:'+last_order
                    yield trans
                    #for k, v in row.items():
                    #    print(k,":",v)
        else:
            print("Invalid file:", self.filename)
        return None

'''
trade_date : 2019-06-25
tradingsymbol : DAAWAT
exchange : NSE
segment : EQ
trade_type : sell
quantity : 39.0
price : 22.2
order_id : 1000000001972846
trade_id : 448584
order_execution_time : 2019-06-25T10:03:53
'''