from .models import FixedDeposit
import datetime
from .fixed_deposit_helper import get_maturity_value
from dateutil.relativedelta import relativedelta
from alerts.alert_helper import create_alert_month_if_not_exist, Severity

class FdInterface:
    @classmethod
    def get_chart_name(self):
        return 'FD'

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
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = FixedDeposit.objects.filter(user=user_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} fd {ex}')
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

    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for obj in FixedDeposit.objects.filter(user=user_id, start_date__lte=end_date):
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
        for obj in FixedDeposit.objects.filter(user=user_id, start_date__lte=end_date):
            if obj.start_date.year == yr:
                contrib[obj.start_date.month-1] += float(obj.principal)
            if obj.mat_date.year == yr:
                deduct[obj.start_date.month-1] += -1*float(obj.final_val)
        return contrib, deduct

    @classmethod
    def get_amount_for_user(self, user_id):
        fd_objs = FixedDeposit.objects.filter(user=user_id)
        total_fd = 0
        for fd_obj in fd_objs:
            total_fd += fd_obj.final_val
        return total_fd

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
        fd_objs = FixedDeposit.objects.filter(mat_date__gte=today, mat_date__lte=today+relativedelta(days=15))
        for fdo in fd_objs:
            cont = f"FD {fdo.number} will be maturing on {fdo.mat_date}.  Renew and stay invested"
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
        return 'fd'
    
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
        for eo in FixedDeposit.objects.filter(user=user_id):
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