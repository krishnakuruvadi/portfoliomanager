from .models import FixedDeposit
import datetime
from .fixed_deposit_helper import get_maturity_value

class FdInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = FixedDeposit.objects.filter(user=user_id)
            else:
                objs = FixedDeposit.objects.all()
            
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for fd {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = FixedDeposit.objects.filter(goal=goal_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} fd {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = FixedDeposit.objects.filter(user=user_id)
        else:
            objs = FixedDeposit.objects.all()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.final_val else obj.final_val
        return amt

    @classmethod
    def get_goal_yearly_contrib(self, goal_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        cash_flows = list()
        contrib = 0
        deduct = 0
        total = 0
        for obj in FixedDeposit.objects.filter(goal=goal_id):
            if obj.start_date.year == yr:
                contrib += float(obj.principal)
                cash_flows.append((obj.start_date, -1*float(obj.principal)))

            if obj.mat_date.year == yr:
                deduct += -1*float(obj.final_val)
                cash_flows.append((obj.start_date, float(obj.final_val)))
            
            if obj.mat_date.year > yr:
                days = (end_date - obj.start_date).days
                _, mat_value = get_maturity_value(float(obj.principal), obj.start_date, float(obj.roi), days)
                total += mat_value
        return cash_flows, contrib, deduct, total
