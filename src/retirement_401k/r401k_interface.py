from .models import Account401K, Transaction401K, NAVHistory
import datetime
from shared.handle_real_time_data import get_conversion_rate

class R401KInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Account401K.objects.filter(user=user_id)
            else:
                objs = Account401K.objects.all()
            
            for obj in objs:
                trans = Transaction401K.objects.filter(account=obj)
                for t in trans:
                    if not start_day:
                        start_day = t.trans_date
                    else:
                        start_day = start_day if start_day < t.trans_date else t.trans_date
        except Exception as ex:
            print(f'exception finding start day for 401K {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Account401K.objects.filter(goal=goal_id)
            for obj in objs:
                trans = Transaction401K.objects.filter(account=obj)
                for t in trans:
                    if not start_day:
                        start_day = obj.trans_date
                    else:
                        start_day = start_day if start_day < obj.trans_date else obj.trans_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} RSU {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Account401K.objects.filter(user=user_id)
        else:
            objs = Account401K.objects.all()
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
        contrib = 0
        deduct = 0
        total = 0
        cash_flows = list()
        for obj in Account401K.objects.filter(goal=goal_id):
            qty = 0
            for trans in Transaction401K.objects.filter(account=obj, trans_date__lte=end_date):
                if trans.trans_date >= st_date:
                    conv_rate = 1
                    conv_val = get_conversion_rate('USD', 'INR', trans.trans_date)
                    if conv_val:
                        conv_rate = conv_val
                    else:
                        print(f'failed to get conversion rate from USD to INR for date {trans.trans_date}')
                    v = float(trans.employee_contribution + trans.employer_contribution) * float(conv_rate)
                    contrib += v
                    cash_flows.append((trans.trans_date, -1*v))
                qty += float(trans.units)
            if qty > 0:
                nav_objs = NAVHistory.objects.filter(account=obj, nav_date__lte=end_date).order_by('-nav_date')#descending
                conv_rate = 1
                conv_val = get_conversion_rate('USD', 'INR', nav_objs[0].nav_date)
                if conv_val:
                    conv_rate = conv_val
                else:
                    print(f'failed to get conversion rate from USD to INR for date {nav_objs[0].nav_date}')

                total += float(nav_objs[0].nav_value)*qty*float(conv_rate)
        return cash_flows, contrib, deduct, total
