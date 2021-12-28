from .models import Ppf, PpfEntry
import datetime

class PpfInterface:
    @classmethod
    def get_chart_name(self):
        return 'PPF'

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
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = Ppf.objects.filter(user=user_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} ppf {ex}')
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
    
    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for ppf_obj in Ppf.objects.filter(user=user_id):
            for ppf_trans in PpfEntry.objects.filter(number=ppf_obj, trans_date__gte=st_date, trans_date__lte=end_date):
                if ppf_trans.entry_type == 'CR':
                    contrib += float(ppf_trans.amount)
                else:
                    deduct += -1*float(ppf_trans.amount)
        return contrib, deduct

    @classmethod
    def get_user_monthly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = [0]*12
        deduct = [0]*12
        for ppf_obj in Ppf.objects.filter(user=user_id):
            for ppf_trans in PpfEntry.objects.filter(number=ppf_obj, trans_date__gte=st_date, trans_date__lte=end_date):
                if ppf_trans.entry_type == 'CR':
                    contrib[ppf_trans.trans_date.month-1] += float(ppf_trans.amount)
                else:
                    deduct[ppf_trans.trans_date.month-1] += -1*float(ppf_trans.amount)
        return contrib, deduct
    
    @classmethod
    def get_amount_for_user(self, user_id):
        ppf_objs = Ppf.objects.filter(user=user_id)
        total_ppf = 0
        for ppf_obj in ppf_objs:
            ppf_num = ppf_obj.number
            amt = 0
            ppf_trans = PpfEntry.objects.filter(number=ppf_num)
            for entry in ppf_trans:
                if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                    amt += entry.amount
                else:
                    amt -= entry.amount
            if amt < 0:
                amt = 0
            total_ppf += amt
        return total_ppf

    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt

    @classmethod
    def get_export_name(self):
        return 'ppf'
    
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
        for po in Ppf.objects.filter(user=user_id):
            eod = {
                'number': po.number,
                'start_date': po.start_date,
                'end_date': po.end_date, 
                'notes':po.notes,
                'goal_name':''
            }
            if po.goal:
                eod['goal_name'] = get_goal_name_from_id(po.goal)
            t = list()
            for trans in PpfEntry.objects.filter(number=po):
                t.append({
                    'trans_date':trans.trans_date,
                    'reference': trans.reference,
                    'amount':trans.amount,
                    'entry_type':trans.entry_type,
                    'interest_component':trans.interest_component,
                    'notes':trans.notes
                })
            eod['transactions'] = t
            data.append(eod)
        
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret