from .models import Espp, EsppSellTransactions
import datetime
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price_based_on_symbol, get_in_preferred_currency
from dateutil.relativedelta import relativedelta

class EsppInterface:
    @classmethod
    def get_chart_name(self):
        return 'ESPP'

    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Espp.objects.filter(user=user_id)
            else:
                objs = Espp.objects.all()
            
            for obj in objs:
                if not start_day:
                    start_day = obj.purchase_date
                else:
                    start_day = start_day if start_day < obj.purchase_date else obj.purchase_date
        except Exception as ex:
            print(f'exception finding start day for espp {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Espp.objects.filter(goal=goal_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.purchase_date
                else:
                    start_day = start_day if start_day < obj.purchase_date else obj.purchase_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} ppf {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = Espp.objects.filter(user=user_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.purchase_date
                else:
                    start_day = start_day if start_day < obj.purchase_date else obj.purchase_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} ppf {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Espp.objects.filter(user=user_id)
        else:
            objs = Espp.objects.all()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.latest_value else obj.latest_value
        return amt

    @classmethod
    def get_goal_yearly_contrib(self, goal_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        if end_date > datetime.date.today():
            end_date = datetime.date.today()
        contrib = 0
        deduct = 0
        total = 0
        cash_flows = list()
        
        for espp_obj in Espp.objects.filter(goal=goal_id, purchase_date__lte=end_date):
            units = espp_obj.shares_purchased
            if espp_obj.purchase_date >= st_date:
                contrib += float(espp_obj.total_purchase_price)
                cash_flows.append((espp_obj.purchase_date, -1*float(espp_obj.total_purchase_price)))
            for st in EsppSellTransactions.objects.filter(espp=espp_obj, trans_date__lte=end_date):
                if st.trans_date >= st_date:
                    cash_flows.append((st.trans_date, float(st.trans_price)))
                    deduct += -1*float(st.trans_price)
                units -= st.units
                
            if units > 0:
                year_end_value_vals = get_historical_stock_price_based_on_symbol(espp_obj.symbol, espp_obj.exchange, end_date+relativedelta(days=-5), end_date)
                if year_end_value_vals:
                    conv_rate = 1
                    if espp_obj.exchange in ['NASDAQ', 'NYSE']:
                        conv_val = get_in_preferred_currency(1, 'USD', end_date)
                        if conv_val:
                            conv_rate = conv_val
                    elif espp_obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        conv_val = get_in_preferred_currency(1, 'INR', end_date)
                        if conv_val:
                            conv_rate = conv_val
                    for k,v in year_end_value_vals.items():
                        total += float(v)*float(conv_rate)*float(units)
                        break
                else:
                    print(f'failed to get year end values for {espp_obj.exchange} {espp_obj.symbol} {end_date}')
        return cash_flows, contrib, deduct, total

    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for espp_obj in Espp.objects.filter(user=user_id, purchase_date__lte=end_date):
            if espp_obj.purchase_date >= st_date:
                contrib += float(espp_obj.total_purchase_price)
            for st in EsppSellTransactions.objects.filter(espp=espp_obj, trans_date__lte=end_date):
                if st.trans_date >= st_date:
                    deduct += -1*float(st.trans_price)
        return contrib, deduct
    
    @classmethod
    def get_user_monthly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        contrib = [0]*12
        deduct = [0]*12
        for espp_obj in Espp.objects.filter(user=user_id, purchase_date__lte=end_date):
            if espp_obj.purchase_date >= st_date:
                contrib[espp_obj.purchase_date.month-1] += float(espp_obj.total_purchase_price)
            for st in EsppSellTransactions.objects.filter(espp=espp_obj, trans_date__lte=end_date):
                if st.trans_date >= st_date:
                    deduct[espp_obj.purchase_date.month-1] += -1*float(st.trans_price)
        return contrib, deduct

    @classmethod
    def get_amount_for_user(self, user_id):
        espp_objs = Espp.objects.filter(user=user_id)
        total_espp = 0
        for espp_obj in espp_objs:
            if espp_obj.latest_value:
                total_espp += espp_obj.latest_value
        return total_espp
    
    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt

    @classmethod
    def get_export_name(self):
        return 'espp'
    
    @classmethod
    def get_current_version(self):
        return 'v1'

    @classmethod
    def export(self, user_id):
        from shared.handle_get import get_goal_name_from_id

        ret = {
            self.get_export_name(): {
                'version':self.get_current_version()
            }
        }
        data = list()
        for eo in Espp.objects.filter(user=user_id):
            eod = {
                'exchange': eo.exchange,
                'symbol': eo.symbol,
                'purchase_date': eo.purchase_date,
                'subscription_fmv': eo.subscription_fmv, 
                'purchase_fmv':eo.purchase_fmv,
                'purchase_price': eo.purchase_price,
                'shares_purchased':eo.shares_purchased,
                'purchase_conversion_rate':eo.purchase_conversion_rate,
                'total_purchase_price':eo.total_purchase_price,
                'shares_avail_for_sale':eo.shares_avail_for_sale,
                'purchase_conversion_rate':eo.purchase_conversion_rate,
                'purchase_conversion_rate':eo.purchase_conversion_rate,
                'goal_name':''
            }
            if eo.goal:
                eod['goal_name'] = get_goal_name_from_id(eo.goal)
            t = list()
            for trans in EsppSellTransactions.objects.filter(espp=eo):
                t.append({
                    'trans_date':trans.trans_date,
                    'price':trans.price,
                    'units': trans.units,
                    'conversion_rate':trans.conversion_rate,
                    'trans_price':trans.trans_price,
                    'realised_gain':trans.realised_gain,
                    'notes':trans.notes
                })
            eod['transactions'] = t
            data.append(eod)
        
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret
    
    @classmethod
    def updates_summary(self, ext_user, start_date, end_date):
        from users.user_interface import get_users
        from shared.financial import xirr, calc_simple_roi

        diff_days = (end_date - start_date).days

        ret = dict()
        ret['details'] = list()
        ids = list()
        for u in get_users(ext_user):
            ids.append(u.id)
        objs = Espp.objects.filter(user__in=ids)
        start = 0
        bought = 0
        sold = 0
        e = dict()
        amt = 0
        for obj in objs:
            start_units = 0
            end_units = float(obj.shares_purchased)
            if obj.purchase_date >= start_date:
                bought += float(obj.total_purchase_price)
            else:
                start_units += float(obj.shares_purchased)

            for st in EsppSellTransactions.objects.filter(espp=obj):
                end_units -= float(st.units)
                if st.trans_date >= start_date:
                    sold += float(st.trans_price)
                else:
                    start_units -= float(st.units)

            if start_units > 0:
                vals = get_historical_stock_price_based_on_symbol(obj.symbol, obj.exchange, start_date+relativedelta(days=-5), start_date)
                if vals:
                    conv_rate = 1
                    if obj.exchange in ['NASDAQ', 'NYSE']:
                        conv_val = get_in_preferred_currency(1, 'USD', start_date)
                        if conv_val:
                            conv_rate = conv_val
                    elif obj.exchange in ['BSE', 'NSE', 'NSE/BSE']:
                        conv_val = get_in_preferred_currency(1, 'INR', start_date)
                        if conv_val:
                            conv_rate = conv_val
                    for k,v in vals.items():
                        start += float(v)*float(conv_rate)*float(start_units)
                        break
                else:
                    print(f'failed to get year end values for {obj.exchange} {obj.symbol} {start_date}')
            if end_units > 0:
                vals = get_historical_stock_price_based_on_symbol(obj.symbol, obj.exchange, end_date+relativedelta(days=-5), end_date)
                if vals:
                    conv_rate = 1
                    if obj.exchange in ['NASDAQ', 'NYSE']:
                        conv_val = get_in_preferred_currency(1, 'USD', end_date)
                        if conv_val:
                            conv_rate = conv_val
                    elif obj.exchange in ['BSE', 'NSE', 'NSE/BSE']:
                        conv_val = get_in_preferred_currency(1, 'INR', start_date)
                        if conv_val:
                            conv_rate = conv_val
                    for k,v in vals.items():
                        amt += float(v)*float(conv_rate)*float(end_units)
                        break
                else:
                    print(f'failed to get year end values for {obj.exchange} {obj.symbol} {end_date}')

        ret['start'] = round(start, 2)
        ret['bought'] = round(bought, 2)
        ret['sold'] = round(sold, 2)
        ret['balance'] = round(amt, 2)
        changed = float(start+bought-sold)
        if changed != float(amt):
            if diff_days >= 365:
                cash_flows = list()
                cash_flows.append((start_date, -1*float(changed)))
                cash_flows.append((end_date, float(amt)))
                print(f'finding xirr for {cash_flows}')
                ret['change'] = xirr(cash_flows, 0.1)*100
            else:
                ret['change'] = calc_simple_roi(changed , amt)
        else:
            ret['change'] = 0
        ret['details'].append(e)
        return ret

    @classmethod
    def updates_email(self, ext_user, start_date, end_date):
        update = self.updates_summary(ext_user, start_date, end_date)
        from shared.email_html import get_weekly_update_table
        ret = dict()
        col_names = ['Start','Bought','Sold','Balance', 'Change']
        if update['change'] >= 0:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>{round(update['change'],2)}%"""
        else:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#df2028">▼</span>{round(update['change'],2)}%"""
        values = [update['start'], update['bought'], update['sold'], update['balance'], change]
        ret['content'] = get_weekly_update_table('Employee Stock Purchase Plan', col_names, values)
        ret['start'] = update['start']
        ret['credits'] = update['bought']
        ret['debits'] = update['sold']
        ret['balance'] = update['balance']
        print(f'ret {ret}')
        return ret
