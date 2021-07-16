from .models import Ppf, PpfEntry
import datetime

class PpfInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Ppf.objects.filter(user=user_id)
            else:
                objs = Ppf.objects.all()
            
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for ppf {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Ppf.objects.filter(goal=goal_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} ppf {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Ppf.objects.filter(user=user_id)
        else:
            objs = Ppf.objects.all()
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
        for ppf_obj in Ppf.objects.filter(goal=goal_id):
            for ppf_trans in PpfEntry.objects.filter(number=ppf_obj, trans_date__lte=end_date):
                if ppf_trans.trans_date >= st_date:
                    if ppf_trans.interest_component:
                        if ppf_trans.entry_type != 'CR':
                            cash_flows.append((ppf_trans.trans_date, float(ppf_trans.amount)))
                    else:
                        if ppf_trans.entry_type == 'CR':
                            contrib += float(ppf_trans.amount)
                            cash_flows.append((ppf_trans.trans_date, -1*float(ppf_trans.amount)))
                        else:
                            deduct += -1*float(ppf_trans.amount)
                            cash_flows.append((ppf_trans.trans_date, float(ppf_trans.amount)))
                if ppf_trans.entry_type == 'CR':
                    total += float(ppf_trans.amount)
                else:
                    total += -1*float(ppf_trans.amount)
                print(f'total: {total}')
        return cash_flows, contrib, deduct, total
