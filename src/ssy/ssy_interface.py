from .models import Ssy, SsyEntry
import datetime

class SsyInterface:

    @classmethod
    def get_chart_name(self):
        return 'SSY'

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
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = Ssy.objects.filter(user=user_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} ssy {ex}')
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

    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for ssy_obj in Ssy.objects.filter(user=user_id):
            for ssy_trans in SsyEntry.objects.filter(number=ssy_obj, trans_date__gte=st_date, trans_date__lte=end_date):
                if ssy_trans.entry_type == 'CR':
                    contrib += float(ssy_trans.amount)
                else:
                    deduct += -1*float(ssy_trans.amount)
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
        for ssy_obj in Ssy.objects.filter(user=user_id):
            for ssy_trans in SsyEntry.objects.filter(number=ssy_obj, trans_date__gte=st_date, trans_date__lte=end_date):
                if ssy_trans.entry_type == 'CR':
                    contrib[ssy_trans.trans_date.month-1] += float(ssy_trans.amount)
                else:
                    deduct[ssy_trans.trans_date.month-1] += -1*float(ssy_trans.amount)
        return contrib, deduct
    
    @classmethod
    def get_amount_for_user(self, user_id):
        ssy_objs = Ssy.objects.filter(user=user_id)
        total_ssy = 0
        for ssy_obj in ssy_objs:
            ssy_num = ssy_obj.number
            amt = 0
            ssy_trans = SsyEntry.objects.filter(number=ssy_num)
            for entry in ssy_trans:
                if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                    amt += entry.amount
                else:
                    amt -= entry.amount
            if amt < 0:
                amt = 0
            total_ssy += amt
        return total_ssy

    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt
        
    @classmethod
    def get_export_name(self):
        return 'ssy'
    
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
        for so in Ssy.objects.filter(user=user_id):
            eod = {
                'number': so.number,
                'start_date': so.start_date,
                'notes':so.notes,
                'goal_name':''
            }
            if so.goal:
                eod['goal_name'] = get_goal_name_from_id(so.goal)
            t = list()
            for trans in SsyEntry.objects.filter(number=so):
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

    @classmethod
    def updates_summary(self, ext_user, start_date, end_date):
        from users.user_interface import get_users
        from shared.financial import xirr

        ret = dict()
        ret['details'] = list()
        ids = list()
        for u in get_users(ext_user):
            ids.append(u.id)
        ssy_objs = Ssy.objects.filter(user__in=ids)
        start = 0
        credits = 0
        debits = 0
        interest = 0
        e = dict()
        amt = 0
        ssy_trans = SsyEntry.objects.filter(number__in=ssy_objs).order_by("trans_date")
        for entry in ssy_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                if entry.trans_date < start_date:
                    start += entry.amount
                else:
                    if entry.interest_component:
                        interest += entry.amount
                    else:
                        credits += entry.amount
                amt += entry.amount
            else:
                amt -= entry.amount
                if entry.trans_date < start_date:
                    start -= entry.amount
                else:
                    if entry.interest_component:
                        interest -= entry.amount
                    else:
                        debits += entry.amount
        ret['start'] = round(start,2)
        ret['credits'] = round(credits,2)
        ret['debits'] = round(debits,2)
        ret['balance'] = round(amt,2)
        ret['interest'] = round(interest,2)
        changed = float(start+credits-debits)
        if changed != float(amt):
            cash_flows = list()
            cash_flows.append((start_date, -1*float(start+credits-debits)))
            cash_flows.append((end_date, float(amt)))
            print(f'finding xirr for {cash_flows}')
            ret['change'] = xirr(cash_flows, 0.1)*100
        else:
            ret['change'] = 0
        ret['details'].append(e)
        return ret

    @classmethod
    def updates_email(self, ext_user, start_date, end_date):
        update = self.updates_summary(ext_user, start_date, end_date)
        from shared.email_html import get_email_html, get_weekly_update_table
        ret = dict()
        col_names = ['Start','Credits','Debits','Interest','Balance', 'Change']
        if update['change'] >= 0:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>{round(update['change'],2)}%"""
        else:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#df2028">▼</span>{round(update['change'],2)}%"""
        values = [update['start'], update['credits'], update['debits'], update['interest'], update['balance'], change]
        ret['content'] = get_weekly_update_table('Sukanya Samridhi Yojana', col_names, values)
        ret['start'] = update['start']
        ret['credits'] = update['credits']
        ret['debits'] = update['debits']
        ret['balance'] = update['balance']
        print(f'ret {ret}')
        return ret
 
