import requests
from dateutil.relativedelta import relativedelta
import datetime
import csv
import codecs
from contextlib import closing
from shared.handle_real_time_data import get_latest_vals, get_forex_rate
from .models import Espp, EsppSellTransactions
from common.models import Stock

def update_latest_vals(espp_obj):
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()
    sold_units = 0
    realised_gain = 0
    for sell_trans in EsppSellTransactions.objects.filter(espp=espp_obj):
        sold_units += sell_trans.units
        realised_gain += sell_trans.realised_gain
    try:
        _ = Stock.objects.get(exchange=espp_obj.exchange, symbol=espp_obj.symbol)
    except Stock.DoesNotExist:
        _ = Stock.objects.create(
                exchange = espp_obj.exchange,
                symbol=espp_obj.symbol,
                etf=False,
                collection_start_date=datetime.date.today()
            )
    remaining_units = espp_obj.shares_purchased - sold_units
    espp_obj.shares_avail_for_sale = remaining_units
    espp_obj.realised_gain = realised_gain
    if remaining_units > 0:
        vals = get_latest_vals(espp_obj.symbol, espp_obj.exchange, start, end)
        print('vals', vals)
        if vals:
            for k, v in vals.items():
                if k and v:
                    if not espp_obj.as_on_date or k > espp_obj.as_on_date:
                        espp_obj.as_on_date = k
                        espp_obj.latest_price = v
                        if espp_obj.exchange == 'NASDAQ':
                            espp_obj.latest_conversion_rate = get_forex_rate(k, 'USD', 'INR')
                        else:
                            espp_obj.latest_conversion_rate = 1
                        espp_obj.latest_value = float(espp_obj.latest_price) * float(espp_obj.latest_conversion_rate) * float(espp_obj.shares_avail_for_sale)
                        espp_obj.unrealised_gain = float(espp_obj.latest_value) - (float(espp_obj.purchase_price) * float(espp_obj.latest_conversion_rate) * float(espp_obj.shares_avail_for_sale))
    else:
        espp_obj.latest_value = 0
        
    espp_obj.save()
    print('done with update request')

