from .models import RecurringDeposit
import datetime
from .recurring_deposit_helper import get_maturity_value
from dateutil.relativedelta import relativedelta
from alerts.alert_helper import create_alert_month_if_not_exist, Severity

class RdInterface:
    @classmethod
    def get_chart_name(self):
        return 'RD'

    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = RecurringDeposit.objects.filter(user=user_id)
            else:
                objs = RecurringDeposit.objects.all()
            
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for rd {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = RecurringDeposit.objects.filter(goal=goal_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} rd {ex}')
        return start_day

    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = RecurringDeposit.objects.filter(user=user_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} rd {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        today = datetime.date.today()
        if user_id:
            objs = RecurringDeposit.objects.filter(user=user_id)
        else:
            objs = RecurringDeposit.objects.all()
        for obj in objs:
            if not obj.goal and obj.mat_date > today:
                months = relativedelta(today, obj.start_date).months+1
                print(f'months between {today} and {obj.start_date} is {months}')
                _, mat_value = get_maturity_value(float(obj.principal), obj.start_date, float(obj.roi), months)
                print(f'mat_value {mat_value} months {months}')
                amt += mat_value
        return amt
    
    @classmethod
    def get_amount_for_goal(self, id):
        rd_objs = RecurringDeposit.objects.filter(goal=id)
        total_rd = 0
        today = datetime.date.today()
        for rd_obj in rd_objs:
            if rd_obj.mat_date > today:
                months = relativedelta(today, rd_obj.start_date).months+1
                print(f'months between {today} and {rd_obj.start_date} is {months}')
                _, mat_value = get_maturity_value(float(rd_obj.principal), rd_obj.start_date, float(rd_obj.roi), months)
                print(f'mat_value {mat_value} months {months}')
                total_rd += mat_value
        return total_rd
    
    @classmethod
    def get_goal_yearly_contrib(self, goal_id, yr):
        print(f'yr {yr}')
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        cash_flows = list()
        contrib = 0
        deduct = 0
        total = 0
        for obj in RecurringDeposit.objects.filter(goal=goal_id):
            
            if obj.start_date.year <= yr:
                s = datetime.date(month=1, day=obj.start_date.day, year=yr)
                if s < obj.start_date:
                    s = obj.start_date
                while s <= obj.mat_date and s <= end_date:
                    print(f'contrib s: {s} {float(obj.principal)}')
                    contrib += float(obj.principal)
                    cash_flows.append((s, -1*float(obj.principal)))
                    s = s + relativedelta(months=1)

            if obj.mat_date.year == yr:
                deduct += -1*float(obj.final_val)
                cash_flows.append((obj.start_date, float(obj.final_val)))
            
            if obj.mat_date.year > yr:
                months = relativedelta(end_date, obj.start_date).months+1
                print(f'months between {end_date} and {obj.start_date} is {months}')
                _, mat_value = get_maturity_value(float(obj.principal), obj.start_date, float(obj.roi), months)
                print(f'mat_value {mat_value} months {months}')
                total += mat_value
        return cash_flows, contrib, deduct, total

    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for obj in RecurringDeposit.objects.filter(user=user_id, start_date__lte=end_date):
            if obj.start_date.year == yr:
                contrib += float(obj.principal)
            if obj.mat_date.year == yr:
                deduct += -1*float(obj.final_val)
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
        for obj in RecurringDeposit.objects.filter(user=user_id, start_date__lte=end_date):
            if obj.start_date.year == yr:
                contrib[obj.start_date.month-1] += float(obj.principal)
            if obj.mat_date.year == yr:
                deduct[obj.start_date.month-1] += -1*float(obj.final_val)
        return contrib, deduct

    @classmethod
    def get_amount_for_user(self, user_id):
        rd_objs = RecurringDeposit.objects.filter(user=user_id)
        total_rd = 0
        today = datetime.date.today()
        for rd_obj in rd_objs:
            if rd_obj.mat_date > today:
                months = relativedelta(today, rd_obj.start_date).months+1
                print(f'months between {today} and {rd_obj.start_date} is {months}')
                _, mat_value = get_maturity_value(float(rd_obj.principal), rd_obj.start_date, float(rd_obj.roi), months)
                print(f'mat_value {mat_value} months {months}')
                total_rd += mat_value
        return total_rd

    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt

    @classmethod
    def raise_alerts(self):
        today = datetime.date.today()
        rd_objs = RecurringDeposit.objects.filter(mat_date__gte=today, mat_date__lte=today+relativedelta(days=15))
        for rdo in rd_objs:
            cont = f"RD {rdo.number} will be maturing on {rdo.mat_date}.  Renew and stay invested"
            print(cont+ ". Raising an alarm")
                            
            create_alert_month_if_not_exist(
                cont,
                cont,
                cont,
                severity=Severity.warning,
                alert_type="Action"
            )

    @classmethod
    def get_export_name(self):
        return 'rd'
    
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
        for eo in RecurringDeposit.objects.filter(user=user_id):
            eod = {
                'number': eo.number,
                'bank_name': eo.bank_name,
                'start_date': eo.start_date,
                'mat_date': eo.mat_date, 
                'notes':eo.notes,
                'principal': eo.principal,
                'roi':eo.roi,
                'time_period':eo.time_period,
                'final_val':eo.final_val,
                'goal_name':''
            }
            if eo.goal:
                eod['goal_name'] = get_goal_name_from_id(eo.goal)

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
        objs = RecurringDeposit.objects.filter(user__in=ids)
        start = 0
        credits = 0
        debits = 0
        interest = 0
        e = dict()
        amt = 0
        for entry in objs:
            amt += float(entry.principal)
            if entry.start_date >= start_date:
                credits += float(entry.principal)
            else:
                start += float(entry.principal)
            if entry.mat_date <= start_date:
                start -= float(entry.principal)
                amt -= float(entry.principal)
            elif entry.mat_date >= start_date and entry.mat_date <= end_date:
                debits += float(entry.principal)
                interest += float(entry.final_val - entry.principal)

        ret['start'] = round(start,2)
        ret['credits'] = round(credits,2)
        ret['debits'] = round(debits,2)
        ret['balance'] = round(amt,2)
        ret['interest'] = round(interest,2)
        balance = float(start+credits-debits)
        if balance != float(amt):
            cash_flows = list()
            cash_flows.append((start_date, -1*float(balance)))
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
        from shared.email_html import get_weekly_update_table
        ret = dict()
        col_names = ['Start','New Deposit','Matured/Withdrawn','Interest Paid','Balance', 'Change']
        if update['change'] >= 0:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>{round(update['change'], 2)}%"""
        else:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#df2028">▼</span>{round(update['change'], 2)}%"""
        values = [update['start'], update['credits'], update['debits'], update['interest'], update['balance'], change]
        ret['content'] = get_weekly_update_table('Recurring Deposit', col_names, values)
        ret['start'] = round(update['start'], 2)
        ret['credits'] = round(update['credits'], 2)
        ret['debits'] = round(update['debits'], 2)
        ret['balance'] = round(update['balance'], 2)
        print(f'ret {ret}')
        return ret
