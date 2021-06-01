import csv
from os.path import isfile
from shared.utils import *
from common.nse_bse import get_nse_bse
from shares.shares_helper import get_isin_from_bhav_copy
from common.nse_historical import NSEHistorical

class Zerodha:
    def __init__(self, filename):
        self.filename = filename
        self.broker = 'ZERODHA'
    
    def get_transactions(self):
        isin_cache = dict()
        if isfile(self.filename):
            trans = dict()
            with open(self.filename, mode='r', encoding='utf-8-sig') as csv_file:
                print("opened file as csv:", self.filename)
                csv_reader = csv.DictReader(csv_file, delimiter=",")
                for row in csv_reader:
                    debug=False
                    #if row['symbol'] == 'VAKRANGEE':
                    #    debug=True
                    if 'order_id' not in row:
                        break
                    print(row)
                    quote = None
                    tran_date = get_datetime_or_none_from_string(row['trade_date'])
                    if not tran_date:
                        print(f'failed to convert {row["trade_date"]} to date')
                        continue
                    tran_date = tran_date.date()
                    key = row['exchange'] + "_" + row['symbol']
                    if debug:
                        print(f'Key before checking for isin {key}')
                    if key not in isin_cache:
                        if debug:
                            print(f'ISIN not yet in cache')
                        if row['exchange'] == 'NSE':
                            quote = get_nse_bse(row['symbol'], None, None)
                        elif row['exchange'] == 'BSE':
                            quote = get_nse_bse(None, row['symbol'], None)
                    
                        if not quote:
                            print(f"failed to get isin for {row['exchange']} {row['symbol']} for current date.  checking old bhav copy")
                            if row['exchange'] == 'BSE':
                                isin = get_isin_from_bhav_copy(row['symbol'], tran_date)
                                if isin:
                                    quote = get_nse_bse(None, None, isin)
                                    isin_cache[key] = quote['isin']
                                    key = quote['isin']
                                    print(f"Found isin from bhav copy {row['symbol']} {row['symbol']} {key}")
                                else:
                                    print(f"isin not found from bhav copy {row['exchange']} {row['symbol']} {key}")
                            else:
                                n = NSEHistorical(row['symbol'], tran_date)
                                isin_n = n.get_isin_from_bhav_copy()
                                if isin_n:
                                    key = isin_n
                                else:
                                    print(f"failed to get isin from bhav copy {row['exchange']} {row['symbol']}")
                        else:
                            isin_cache[key] = quote['isin']
                            key = quote['isin']
                            if debug:
                                print(f'{row["exchange"]} {row["symbol"]} isin {key}')
                    else:
                        key = isin_cache[key]
                    if debug:
                        print(f'Key after checking for isin {key}')
                    if key not in trans:
                        if debug:
                            print(f'first transaction for {row["exchange"]} {row["symbol"]} .  Adding to dict')
                        trans[key] = dict()
                        trans[key]['exchange'] = row['exchange']
                        symbol = row['symbol']
                        symbol = symbol[0:None if -1==symbol.find('-') else symbol.find('-')]
                        trans[key]['symbol'] = symbol
                        trans[key]['trades'] = dict()
                    else:
                        if row['exchange'] != trans[key]['exchange']:
                            trans[key]['exchange'] = 'NSE/BSE'
                        if row['exchange'] == 'NSE':
                            trans[key]['symbol'] = row['symbol']

                    trans_type = 'Sell' if row['trade_type']=='sell' else 'Buy'
                    if not tran_date in trans[key]['trades']:
                        if debug:
                            print(f'first transaction for date {tran_date} for {row["exchange"]} {row["symbol"]} ')
                        trans[key]['trades'][tran_date] = dict()
                    if trans_type not in trans[key]['trades'][tran_date]:
                        if debug:
                            print(f'first transaction for date {tran_date} for {row["exchange"]} {row["symbol"]} type {trans_type}')

                        trans[key]['trades'][tran_date][trans_type] = dict()
                        trans[key]['trades'][tran_date][trans_type]["quantity"] = int(get_float_or_none_from_string(row['quantity']))
                        trans[key]['trades'][tran_date][trans_type]["price"] = get_float_or_none_from_string(row['price'])
                        trans[key]['trades'][tran_date][trans_type]["notes"] = 'order id:'+row['order_id']
                    else:
                        if debug:
                            print(f'new transaction for existing date {tran_date} for {row["exchange"]} {row["symbol"]} type {trans_type}')

                        new_qty = int(get_float_or_none_from_string(row['quantity'])) + trans[key]['trades'][tran_date][trans_type]["quantity"]
                        total_price = trans[key]['trades'][tran_date][trans_type]["price"] * trans[key]['trades'][tran_date][trans_type]["quantity"]
                        total_price += int(get_float_or_none_from_string(row['quantity'])) * get_float_or_none_from_string(row['price'])
                        trans[key]['trades'][tran_date][trans_type]["quantity"] = new_qty
                        trans[key]['trades'][tran_date][trans_type]["price"] = total_price/new_qty
                        if row['order_id'] not in trans[key]['trades'][tran_date][trans_type]["notes"]:
                            trans[key]['trades'][tran_date][trans_type]["notes"] += "," + row['order_id']
                        if debug:
                            print(f'new quantity after transaction for existing date {new_qty} {tran_date} for {row["exchange"]} {row["symbol"]} type {trans_type}')

            #print('Exchange Symbol Trans_type Quantity Price Tran_date Notes')
            for _,v in trans.items():
                exchange = v['exchange']
                symbol = v['symbol']
                for dt, trade in v['trades'].items():
                    tran_date = dt
                    for trans_type, trans_details in trade.items():
                        qty = trans_details['quantity']
                        price = trans_details['price']
                        notes = trans_details['notes']

                        trans = dict()
                        trans["exchange"] = exchange
                        trans["symbol"] = symbol
                        trans["type"] = trans_type
                        trans["quantity"] = qty
                        trans["price"] = price
                        trans["date"] = tran_date
                        trans["notes"] = notes
                        #print(f'{exchange} {symbol} {trans_type} {qty} {price} {tran_date} {notes}')
                        yield trans
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

'''
from shares.zerodha import Zerodha
file_path = '<<<fill here>>>'
z = Zerodha(file_path)
for trans in z.get_transactions():
    print(trans)
'''