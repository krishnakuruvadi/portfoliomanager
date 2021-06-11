import requests
from dateutil.relativedelta import relativedelta
import datetime
import csv
import codecs
from contextlib import closing
from shared.handle_real_time_data import get_latest_vals, get_forex_rate
from .models import RSUAward, RestrictedStockUnits, RSUSellTransactions

def update_latest_vals(rsu_obj):
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()
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
        vals = get_latest_vals(rsu_award.symbol, rsu_award.exchange, start, end)
        if vals:
            for k, v in vals.items():
                if k and v:
                    if not rsu_obj.as_on_date or k > rsu_obj.as_on_date:
                        rsu_obj.as_on_date = k
                        rsu_obj.latest_price = v
                        if rsu_award.exchange == 'NASDAQ':
                            rsu_obj.latest_conversion_rate = get_forex_rate(k, 'USD', 'INR')
                        else:
                            rsu_obj.latest_conversion_rate = 1
    rsu_obj.latest_value = float(rsu_obj.latest_price) * float(rsu_obj.latest_conversion_rate) * float(rsu_obj.unsold_shares)
    rsu_obj.unrealised_gain = rsu_obj.latest_value - float(rsu_obj.unsold_shares)*float(rsu_obj.conversion_rate)*float(rsu_obj.aquisition_price)
    rsu_obj.save()

def update_rsu_latest_vals():
    for rsu_award in RSUAward.objects.all():
        for rsu_obj in RestrictedStockUnits.objects.filter(award=rsu_award):
            print("looping through rsu " + str(rsu_obj.id))
            update_latest_vals(rsu_obj)

def get_rsu_award_latest_vals():
    ret = dict()
    for rsu_award in RSUAward.objects.all():
        as_on_date = None
        latest_conversion_rate = None
        latest_price = None
        shares_for_sale = None
        latest_value = None
        shares_vested = None
        for rsu_obj in RestrictedStockUnits.objects.filter(award=rsu_award):
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
        if as_on_date:
            ret[rsu_award.id] = {'as_on_date':as_on_date, 'latest_conversion_rate':latest_conversion_rate, 'latest_price':latest_price}
            ret[rsu_award.id]['shares_for_sale'] = shares_for_sale
            ret[rsu_award.id]['latest_value'] = latest_value
            ret[rsu_award.id]['shares_vested'] = shares_vested
    return ret

def get_no_goal_amount():
    amt = 0
    for obj in RSUAward.objects.all():
        if not obj.goal:
            for rsu_obj in RestrictedStockUnits.objects.filter(award=obj):
                amt += 0 if not rsu_obj.latest_value else rsu_obj.latest_value
    return amt