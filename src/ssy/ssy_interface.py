from .models import Ssy, SsyEntry
import datetime

class SsyInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Ssy.objects.filter(user=user_id)
            else:
                objs = Ssy.objects.all()
            
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for Ssy {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Ssy.objects.filter(goal=goal_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} ssy {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Ssy.objects.filter(user=user_id)
        else:
            objs = Ssy.objects.all()
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
        for ssy_obj in Ssy.objects.filter(goal=goal_id):
            for ssy_trans in SsyEntry.objects.filter(number=ssy_obj, trans_date__lte=end_date):
                if ssy_trans.trans_date >= st_date:
                    if ssy_trans.interest_component:
                        if ssy_trans.entry_type != 'CR':
                            cash_flows.append((ssy_trans.trans_date, float(ssy_trans.amount)))
                    else:
                        if ssy_trans.entry_type == 'CR':
                            contrib += float(ssy_trans.amount)
                            cash_flows.append((ssy_trans.trans_date, -1*float(ssy_trans.amount)))
                        else:
                            contrib += -1*float(ssy_trans.amount)
                            cash_flows.append((ssy_trans.trans_date, float(ssy_trans.amount)))
                if ssy_trans.entry_type == 'CR':
                    total += float(ssy_trans.amount)
                else:
                    total += -1*float(ssy_trans.amount)
        return cash_flows, contrib, deduct, total
