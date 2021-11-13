from .models import RSUAward, RestrictedStockUnits, RSUSellTransactions
import datetime
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price_based_on_symbol
from dateutil.relativedelta import relativedelta

class RsuInterface:
    @classmethod
    def get_chart_name(self):
        return 'RSU'

    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = RSUAward.objects.filter(user=user_id)
            else:
                objs = RSUAward.objects.all()
            
            for obj in objs:
                trans = RestrictedStockUnits.objects.filter(award=obj)
                for t in trans:
                    if not start_day:
                        start_day = t.vest_date
                    else:
                        start_day = start_day if start_day < t.vest_date else t.vest_date
        except Exception as ex:
            print(f'exception finding start day for RSU {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = RSUAward.objects.filter(goal=goal_id)
            for obj in objs:
                trans = RestrictedStockUnits.objects.filter(award=obj)
                for t in trans:
                    if not start_day:
                        start_day = t.vest_date
                    else:
                        start_day = start_day if start_day < t.vest_date else t.vest_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} RSU {ex}')
        return start_day

    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = RSUAward.objects.filter(user=user_id)
            for obj in objs:
                trans = RestrictedStockUnits.objects.filter(award=obj)
                for t in trans:
                    if not start_day:
                        start_day = t.vest_date
                    else:
                        start_day = start_day if start_day < t.vest_date else t.vest_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} RSU {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = RSUAward.objects.filter(user=user_id)
        else:
            objs = RSUAward.objects.all()
        for obj in objs:
            if not obj.goal:
                trans = RestrictedStockUnits.objects.filter(award=obj)
                for t in trans:
                    amt += 0 if not t.latest_value else t.latest_value
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
        for aw_obj in RSUAward.objects.filter(goal=goal_id):
            for rsu_obj in RestrictedStockUnits.objects.filter(award=aw_obj, vest_date__lte=end_date):
                units = rsu_obj.shares_for_sale
                if rsu_obj.vest_date >= st_date:
                    current_cost = float(rsu_obj.shares_for_sale*rsu_obj.aquisition_price*rsu_obj.conversion_rate)
                    contrib += current_cost
                    cash_flows.append((rsu_obj.vest_date, -1*current_cost))
                for st in RSUSellTransactions.objects.filter(rsu_vest=rsu_obj, trans_date__lte=end_date):
                    if st.trans_date >= st_date:
                        cash_flows.append((st.trans_date, float(st.trans_price)))
                        deduct += -1*float(st.trans_price)
                    units -= st.units
                        
                if units > 0:
                    year_end_value_vals = get_historical_stock_price_based_on_symbol(aw_obj.symbol, aw_obj.exchange, end_date+relativedelta(days=-5), end_date)
                    if year_end_value_vals:
                        conv_rate = 1
                        if aw_obj.exchange == 'NASDAQ' or aw_obj.exchange == 'NYSE':
                            conv_val = get_conversion_rate('USD', 'INR', end_date)
                            if conv_val:
                                conv_rate = conv_val
                            for k,v in year_end_value_vals.items():
                                total += float(v)*float(conv_rate)*float(units)
                                break
                    else:
                        print(f'failed to get year end values for {aw_obj.exchange} {aw_obj.symbol} {end_date}')
        return cash_flows, contrib, deduct, total
    
    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for aw_obj in RSUAward.objects.filter(user=user_id):
            for rsu_obj in RestrictedStockUnits.objects.filter(award=aw_obj, vest_date__lte=end_date):
                if rsu_obj.vest_date >= st_date:
                    contrib += float(rsu_obj.total_aquisition_price)
                for st in RSUSellTransactions.objects.filter(rsu_vest=rsu_obj, trans_date__gte=st_date, trans_date__lte=end_date):
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
        for aw_obj in RSUAward.objects.filter(user=user_id):
            for rsu_obj in RestrictedStockUnits.objects.filter(award=aw_obj, vest_date__lte=end_date):
                if rsu_obj.vest_date >= st_date:
                    contrib[rsu_obj.vest_date.month-1] += float(rsu_obj.total_aquisition_price)
                for st in RSUSellTransactions.objects.filter(rsu_vest=rsu_obj, trans_date__gte=st_date, trans_date__lte=end_date):
                    deduct[rsu_obj.vest_date.month-1] += -1*float(st.trans_price)
        return contrib, deduct
    
    @classmethod
    def get_export_name(self):
        return 'rsu'
    
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
        for rao in RSUAward.objects.filter(user=user_id):
            rad = {
                'exchange': rao.exchange,
                'symbol':rao.symbol,
                'award_date':rao.award_date,
                'award_id': rao.award_id,
                'shares_awarded':rao.shares_awarded,
                'goal_name':''
            }
            if rao.goal:
                rad['goal_name'] = get_goal_name_from_id(rao.goal)
            t = list()
            for trans in RestrictedStockUnits.objects.filter(award=rao):
                rsu = {
                    'vest_date':trans.vest_date,
                    'fmv': trans.fmv,
                    'aquisition_price': trans.aquisition_price,
                    'shares_vested': trans.shares_vested,
                    'shares_for_sale': trans.shares_for_sale,
                    'conversion_rate': trans.conversion_rate,
                    'total_aquisition_price': trans.total_aquisition_price,
                    'notes':trans.notes
                }
                st = list()
                for trans in RSUSellTransactions.objects.filter(rsu_vest=trans):
                    t.append({
                        'trans_date':trans.trans_date,
                        'price': trans.price,
                        'units': trans.units,
                        'conversion_rate': trans.conversion_rate,
                        'trans_price': trans.trans_price,
                        'notes':trans.notes
                    })
                rsu['sell_transactions'] = st
                t.append(rsu)
            rad['transactions'] = t
            data.append(rad)
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret