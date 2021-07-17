from .models import Epf, EpfEntry
import datetime
from dateutil.relativedelta import relativedelta

class EpfInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Epf.objects.filter(user=user_id)
            else:
                objs = Epf.objects.all()
            
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for epf {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Epf.objects.filter(goal=goal_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} epf {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Epf.objects.filter(user=user_id)
        else:
            objs = Epf.objects.all()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.total else obj.total
        return amt

    @classmethod
    def get_goal_yearly_contrib(self, goal_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        cash_flows = list()
        contrib = 0
        deduct = 0
        total = 0
        for epf_obj in Epf.objects.filter(goal=goal_id):
            for epf_trans in EpfEntry.objects.filter(epf_id=epf_obj, trans_date__lte=end_date):
                if epf_trans.trans_date >= st_date:
                    contrib += float(epf_trans.employer_contribution + epf_trans.employee_contribution)
                    deduct += -1*float(epf_trans.withdrawl)
                    cash_flows.append((epf_trans.trans_date, -1*float(epf_trans.employer_contribution+ epf_trans.employee_contribution)))
                    if epf_trans.withdrawl and epf_trans.withdrawl > 0:
                        cash_flows.append((epf_trans.trans_date, float(epf_trans.withdrawl)))
                total += float(epf_trans.employer_contribution + epf_trans.employee_contribution+ epf_trans.interest_contribution-epf_trans.withdrawl)

        return cash_flows, contrib, deduct, total