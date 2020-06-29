import requests
from dateutil.relativedelta import relativedelta
import datetime
import csv
import codecs
from contextlib import closing
from shared.handle_real_time_data import get_latest_vals, get_forex_rate

def update_latest_vals(espp_obj):
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()

    vals = get_latest_vals(espp_obj.symbol, espp_obj.exchange, start, end)
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
                    espp_obj.latest_value = float(espp_obj.latest_price) * float(espp_obj.latest_conversion_rate) * float(espp_obj.shares_purchased)
                    espp_obj.gain = float(espp_obj.latest_value) - float(espp_obj.total_purchase_price)
                    espp_obj.save()
    print('done with request')
