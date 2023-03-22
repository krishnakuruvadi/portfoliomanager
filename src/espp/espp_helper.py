from dateutil.relativedelta import relativedelta
import datetime
from shared.handle_real_time_data import get_latest_vals, get_conversion_rate, get_in_preferred_currency
from .models import Espp, EsppSellTransactions
from common.models import Stock
from shared.financial import xirr

def update_latest_vals(espp_obj):
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()
    sold_units = 0
    realised_gain = 0
    cash_flows = list()
    cash_flows.append((espp_obj.purchase_date, -1*float(espp_obj.total_purchase_price)))
    for sell_trans in EsppSellTransactions.objects.filter(espp=espp_obj):
        sold_units += sell_trans.units
        realised_gain += sell_trans.realised_gain
        cash_flows.append((sell_trans.trans_date, float(sell_trans.trans_price)))
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
                        if espp_obj.exchange in ['NASDAQ', 'NYSE']:
                            espp_obj.latest_conversion_rate = get_in_preferred_currency(1, 'USD', k)
                        elif espp_obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                            espp_obj.latest_conversion_rate = get_in_preferred_currency(1, 'INR', k)
                        else:
                            espp_obj.latest_conversion_rate = 1
                        espp_obj.latest_value = float(espp_obj.latest_price) * float(espp_obj.latest_conversion_rate) * float(espp_obj.shares_avail_for_sale)
                        espp_obj.unrealised_gain = float(espp_obj.latest_value) - (float(espp_obj.purchase_price) * float(espp_obj.purchase_conversion_rate) * float(espp_obj.shares_avail_for_sale))
        if espp_obj.latest_value and espp_obj.latest_value > 0:
            cash_flows.append((datetime.date.today(), float(espp_obj.latest_value)))
            x = xirr(cash_flows, 0.1)*100
            espp_obj.xirr = x
    else:
        espp_obj.latest_value = 0
        espp_obj.xirr = 0
        
    espp_obj.save()
    print('done with update request')

def handle_symbol_change(old_symbol, old_exchange, new_symbol, new_exchange):
    for old_espp in Espp.objects.filter(exchange=old_exchange, symbol=old_symbol):
        try:
            new_espp = Espp.objects.get(exchange=new_exchange, symbol=new_symbol, purchase_date=old_espp.purchase_date, user=old_espp.user)
            for old_espp_sell_trans in EsppSellTransactions.objects.filter(espp=old_espp):
                try:
                    new_espp_sell_trans = EsppSellTransactions.objects.filter(espp=new_espp, trans_date=old_espp_sell_trans.trans_date)
                    old_espp_sell_trans.delete()
                except EsppSellTransactions.DoesNotExist:
                    old_espp_sell_trans.espp = new_espp
                    old_espp_sell_trans.save()
            old_espp.delete()
        except Espp.DoesNotExist:
            old_espp.symbol = new_symbol
            old_espp.exchange = new_exchange
            old_espp.save()
