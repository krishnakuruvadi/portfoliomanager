from .models import InsurancePolicy, Transaction, Fund
import datetime
from .insurance_helper import get_historical_nav

class InsuranceInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = InsurancePolicy.objects.filter(user=user_id, policy_type='ULIP')
            else:
                objs = InsurancePolicy.objects.filter(policy_type='ULIP')
            
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for InsurancePolicy {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = InsurancePolicy.objects.filter(goal=goal_id, policy_type='ULIP')
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} InsurancePolicy {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = InsurancePolicy.objects.filter(user=user_id, policy_type='ULIP')
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} InsurancePolicy {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = InsurancePolicy.objects.filter(user=user_id, policy_type='ULIP')
        else:
            objs = InsurancePolicy.objects.filter(policy_type='ULIP')
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.latest_value else obj.latest_value
        return amt
    
    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for ip_obj in InsurancePolicy.objects.filter(user=user_id, policy_type='ULIP'):
            for tran_obj in Transaction.objects.filter(policy=ip_obj, trans_date__gte=st_date, trans_date__lte=end_date, trans_type='Premium'):
                contrib += float(tran_obj.trans_amount)
        return contrib, deduct
    
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
        
        for ip_obj in InsurancePolicy.objects.filter(goal=goal_id, policy_type='ULIP'):
            units = dict()
            for tran_obj in Transaction.objects.filter(policy=ip_obj, trans_date__lte=end_date):
                if tran_obj.trans_type=='Premium':
                    if tran_obj.trans_date >= st_date:
                        cash_flows.append((tran_obj.trans_date, -1*float(tran_obj.trans_amount)))
                        contrib += float(tran_obj.trans_amount)
                units[tran_obj.fund.code] = units.get(tran_obj.fund.code, 0) + tran_obj.units

            for f,u in units.items():
                fund = Fund.objects.get(policy=ip_obj, code=f)
                res = get_historical_nav(fund, end_date)
                if res:
                    total += float(res['nav']) * float(u)
                else:
                    print(f'failed to get final value for year {yr} goal {goal_id} fund code {f}')

        return cash_flows, contrib, deduct, total
    
    @classmethod
    def get_amount_for_goal(self, goal_id):
        amt = 0
        objs = InsurancePolicy.objects.filter(goal=goal_id, policy_type='ULIP')
        for obj in objs:
            amt += 0 if not obj.latest_value else obj.latest_value
        return amt
    
    @classmethod
    def get_amount_for_user(self, user_id):
        amt = 0
        objs = InsurancePolicy.objects.filter(user=user_id, policy_type='ULIP')
        for obj in objs:
            amt += 0 if not obj.latest_value else obj.latest_value
        return amt