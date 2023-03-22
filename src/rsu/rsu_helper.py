from dateutil.relativedelta import relativedelta
import datetime
from shared.handle_real_time_data import get_in_preferred_currency, get_latest_vals
from .models import RSUAward, RestrictedStockUnits, RSUSellTransactions

def update_latest_vals(rsu_obj, latest_vals):
    rsu_award = rsu_obj.award
    rg = 0
    su = 0
    for st in RSUSellTransactions.objects.filter(rsu_vest=rsu_obj):
        su += float(st.units)
        st.trans_price = float(st.price)*float(st.units)*float(st.conversion_rate)
        st.realised_gain = float(st.trans_price) - float(rsu_obj.aquisition_price)*float(st.units)*float(rsu_obj.conversion_rate)
        rg += st.realised_gain
        st.save()
    rsu_obj.realised_gain = rg
    rsu_obj.unsold_shares = float(rsu_obj.shares_for_sale) - su
    rsu_obj.tax_at_vest = float(rsu_obj.shares_vested-rsu_obj.shares_for_sale)*float(rsu_obj.conversion_rate)*float(rsu_obj.aquisition_price)
    if rsu_obj.unsold_shares > 0:
        rsu_obj.as_on_date = latest_vals[rsu_award.exchange]['symbols'][rsu_award.symbol]['date']
        rsu_obj.latest_price = latest_vals[rsu_award.exchange]['symbols'][rsu_award.symbol]['value']
        rsu_obj.latest_conversion_rate = latest_vals[rsu_award.exchange]['latest_conversion_rate']
    rsu_obj.latest_value = float(rsu_obj.latest_price) * float(rsu_obj.latest_conversion_rate) * float(rsu_obj.unsold_shares)
    rsu_obj.unrealised_gain = rsu_obj.latest_value - float(rsu_obj.unsold_shares)*float(rsu_obj.conversion_rate)*float(rsu_obj.aquisition_price)
    rsu_obj.save()

def update_rsu_latest_vals():
    today = datetime.date.today()
    start = datetime.date.today()+relativedelta(days=-5)
    end = today
    latest_vals = dict()
    for rsu_award in RSUAward.objects.all():
        print(f'processing award {rsu_award.award_id}')
        if rsu_award.exchange not in latest_vals:
            print(f'not found {rsu_award.exchange} in  {latest_vals}')
            latest_vals[rsu_award.exchange] = dict()
            latest_vals[rsu_award.exchange]['symbols'] = dict()
            if rsu_award.exchange in ['NASDAQ', 'NYSE']:
                latest_vals[rsu_award.exchange]['latest_conversion_rate'] = get_in_preferred_currency(1, 'USD', today)
            elif rsu_award.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                latest_vals[rsu_award.exchange]['latest_conversion_rate'] = get_in_preferred_currency(1, 'INR', today)
            else:
                latest_vals[rsu_award.exchange]['latest_conversion_rate'] = 1
        if rsu_award.symbol not in latest_vals[rsu_award.exchange]['symbols']:
            print(f'not found {rsu_award.symbol} in  {latest_vals}')
            dt = None
            val = None
            vals = get_latest_vals(rsu_award.symbol, rsu_award.exchange, start, end)
            if vals:
                for k, v in vals.items():
                    if k and v:
                        if not dt or k>dt:
                            dt = k
                            val = v
            latest_vals[rsu_award.exchange]['symbols'][rsu_award.symbol]=dict()
            latest_vals[rsu_award.exchange]['symbols'][rsu_award.symbol]['date'] = dt
            latest_vals[rsu_award.exchange]['symbols'][rsu_award.symbol]['value'] = val 
        for rsu_obj in RestrictedStockUnits.objects.filter(award=rsu_award):
            print("looping through rsu " + str(rsu_obj.id))
            update_latest_vals(rsu_obj, latest_vals)

def get_rsu_award_latest_vals():
    ret = dict()
    for rsu_award in RSUAward.objects.all():
        as_on_date = None
        latest_conversion_rate = None
        latest_price = None
        shares_for_sale = None
        latest_value = None
        shares_vested = None
        aquisition_price = 0
        for rsu_obj in RestrictedStockUnits.objects.filter(award=rsu_award):
            if rsu_obj.as_on_date:
                as_on_date = rsu_obj.as_on_date
            latest_conversion_rate = rsu_obj.latest_conversion_rate
            if rsu_obj.latest_price:
                if not latest_price:
                    latest_price = rsu_obj.latest_price
                else:
                    latest_price += rsu_obj.latest_price
            if not shares_for_sale:
                shares_for_sale = rsu_obj.shares_for_sale
            else:
                shares_for_sale += rsu_obj.shares_for_sale
            if not shares_vested:
                shares_vested = rsu_obj.shares_vested
            else:
                shares_vested += rsu_obj.shares_vested
            if rsu_obj.latest_value:
                if not latest_value:
                    latest_value = rsu_obj.latest_value
                else:
                    latest_value += rsu_obj.latest_value
            aquisition_price += rsu_obj.total_aquisition_price
        if as_on_date:
            ret[rsu_award.id] = {'as_on_date':as_on_date, 'latest_conversion_rate':latest_conversion_rate, 'latest_price':latest_price}
            ret[rsu_award.id]['shares_for_sale'] = shares_for_sale
            ret[rsu_award.id]['latest_value'] = latest_value
            ret[rsu_award.id]['shares_vested'] = shares_vested
            ret[rsu_award.id]['aquisition_price'] = aquisition_price
    return ret

def handle_symbol_change(old_symbol, old_exchange, new_symbol, new_exchange):
    for old_rsu_award in RSUAward.objects.filter(exchange=old_exchange, symbol=old_symbol):
        try:
            new_award = RSUAward.objects.get(exchange=new_exchange, symbol=new_symbol, award_id=old_rsu_award.award_id, user=old_rsu_award.user)
            for old_rsu in RestrictedStockUnits.objects.filter(award=old_rsu_award):
                try:
                    new_rsu = RestrictedStockUnits.objects.get(award=new_award, vest_date=old_rsu.vest_date)
                    for old_rsu_sell_trans in RSUSellTransactions.objects.filter(rsu_vest=old_rsu):
                        try:
                            new_rsu_sell_trans = RSUSellTransactions.objects.filter(rsu_vest=new_rsu, trans_date=old_rsu_sell_trans.trans_date)
                            old_rsu_sell_trans.delete()
                        except RSUSellTransactions.DoesNotExist:
                            old_rsu_sell_trans.rsu_vest = new_rsu
                            old_rsu_sell_trans.save()
                except RestrictedStockUnits.DoesNotExist:
                    old_rsu.award = new_award
                    old_rsu.save()
            old_rsu_award.delete()

        except RSUAward.DoesNotExist:
            old_rsu_award.symbol = new_symbol
            old_rsu_award.exchange = new_exchange
            old_rsu_award.save()