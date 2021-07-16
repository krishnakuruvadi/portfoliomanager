from .models import Folio, MutualFundTransaction
import datetime
from dateutil.relativedelta import relativedelta
from shared.handle_real_time_data import get_historical_mf_nav

class MfInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Folio.objects.filter(user=user_id)
            else:
                objs = Folio.objects.all()
            
            for obj in objs:
                mf_trans = MutualFundTransaction.objects.filter(folio=obj)
                for trans in mf_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for Mutual Fund {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Folio.objects.filter(goal=goal_id)
            for obj in objs:
                mf_trans = MutualFundTransaction.objects.filter(folio=obj)
                for trans in mf_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} ppf {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Folio.objects.filter(user=user_id)
        else:
            objs = Folio.objects.all()
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
        year_end_mf = dict()
        contrib = 0
        deduct = 0
        total = 0
        cash_flows = list()
        try:
            for folio_obj in Folio.objects.filter(goal=goal_id):
                for trans in MutualFundTransaction.objects.filter(folio=folio_obj, trans_date__lte=end_date):
                    if trans.trans_date.year == yr:
                        if trans.trans_type == 'Buy' and not trans.switch_trans:
                            contrib += trans.trans_price
                            cash_flows.append((trans.trans_date, -1*float(trans.trans_price)))
                            year_end_mf[folio_obj.fund.code] = year_end_mf.get(folio_obj.fund.code, 0)+trans.units
                        elif trans.trans_type == 'Sell' and not trans.switch_trans:
                            deduct += -1*trans.trans_price
                            cash_flows.append((trans.trans_date, float(trans.trans_price)))
                            year_end_mf[folio_obj.fund.code] = year_end_mf.get(folio_obj.fund.code, 0)-trans.units
                    else:
                        if trans.trans_type == 'Buy' and not trans.switch_trans:
                            year_end_mf[folio_obj.fund.code] = year_end_mf.get(folio_obj.fund.code, 0)+trans.units
                        elif trans.trans_type == 'Sell' and not trans.switch_trans:
                            year_end_mf[folio_obj.fund.code] = year_end_mf.get(folio_obj.fund.code, 0)-trans.units
        except Exception as ex:
            print(f'exception during getting mf goal yearly contribution {ex}')
        print('year_end_mf', year_end_mf)
            
        for code,qty in year_end_mf.items():
            historical_mf_prices = get_historical_mf_nav(code, end_date+relativedelta(days=-5), end_date)
            if len(historical_mf_prices) > 0:
                print('historical_mf_prices',historical_mf_prices)
                for k,v in historical_mf_prices[0].items():
                    total += v*qty
        return cash_flows, contrib, deduct, total
    