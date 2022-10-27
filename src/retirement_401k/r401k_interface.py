from .models import Account401K, Transaction401K, NAVHistory
import datetime
from shared.handle_real_time_data import get_conversion_rate, get_in_preferred_currency
from alerts.alert_helper import create_alert_month_if_not_exist, Severity
from dateutil.relativedelta import relativedelta
from .helper import get_nearest_nav

class R401KInterface:

    @classmethod
    def get_chart_name(self):
        return '401K'

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
                        start_day = t.trans_date
                    else:
                        start_day = start_day if start_day < t.trans_date else t.trans_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} RSU {ex}')
        return start_day

    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = Account401K.objects.filter(user=user_id)
            for obj in objs:
                trans = Transaction401K.objects.filter(account=obj)
                for t in trans:
                    if not start_day:
                        start_day = t.trans_date
                    else:
                        start_day = start_day if start_day < t.trans_date else t.trans_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} RSU {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        objs = None
        if user_id:
            objs = Account401K.objects.filter(user=user_id)
        else:
            objs = Account401K.objects.all()
        if not objs:
            return amt
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
                    conv_val = get_in_preferred_currency(1, 'USD', trans.trans_date)
                    if conv_val:
                        conv_rate = conv_val
                    else:
                        print(f'failed to get conversion rate from USD to preferred currency for date {trans.trans_date}')
                    v = float(trans.employee_contribution + trans.employer_contribution) * float(conv_rate)
                    contrib += v
                    cash_flows.append((trans.trans_date, -1*v))
                qty += float(trans.units)
            if qty > 0:
                nav_objs = NAVHistory.objects.filter(account=obj, nav_date__lte=end_date).order_by('-nav_date')#descending
                conv_rate = 1
                conv_val = get_in_preferred_currency(1, 'USD', nav_objs[0].nav_date)
                if conv_val:
                    conv_rate = conv_val
                else:
                    print(f'failed to get conversion rate from USD to preferred currency for date {nav_objs[0].nav_date}')

                total += float(nav_objs[0].nav_value)*qty*float(conv_rate)
        return cash_flows, contrib, deduct, total
    
    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for obj in Account401K.objects.filter(user=user_id):
            for trans in Transaction401K.objects.filter(account=obj, trans_date__gte=st_date, trans_date__lte=end_date):
                conv_rate = 1
                conv_val = get_in_preferred_currency(1, 'USD', trans.trans_date)
                if conv_val:
                    conv_rate = conv_val
                else:
                    print(f'failed to get conversion rate from USD to preferred currency for date {trans.trans_date}')
                contrib += float(trans.employee_contribution + trans.employer_contribution) * float(conv_rate)
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
        for obj in Account401K.objects.filter(user=user_id):
            for trans in Transaction401K.objects.filter(account=obj, trans_date__gte=st_date, trans_date__lte=end_date):
                conv_rate = 1
                conv_val = get_in_preferred_currency(1, 'USD', trans.trans_date)
                if conv_val:
                    conv_rate = conv_val
                else:
                    print(f'failed to get conversion rate from USD to preferred currency for date {trans.trans_date}')
                contrib[trans.trans_date.month-1] += float(trans.employee_contribution + trans.employer_contribution) * float(conv_rate)
        return contrib, deduct
    
    @classmethod
    def get_export_name(self):
        return 'r_401k'
    
    @classmethod
    def get_current_version(self):
        return 'v1'

    @classmethod
    def get_amount_for_user(self, user_id):
        objs = Account401K.objects.filter(user=user_id)
        total = 0
        for obj in objs:
            if obj.latest_value:
                total += obj.latest_value
        return total
    
    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt

    @classmethod
    def export(self, user_id):
        from shared.handle_get import get_goal_name_from_id

        ret = {
            self.get_export_name(): {
                'version':self.get_current_version()
            }
        }
        data = list()
        for so in Account401K.objects.filter(user=user_id):
            eod = {
                'company': so.company,
                'start_date':so.start_date,
                'end_date':so.end_date,
                'notes':so.notes,
                'goal_name':''
            }
            if so.goal:
                eod['goal_name'] = get_goal_name_from_id(so.goal)
            t = list()
            for trans in Transaction401K.objects.filter(account=so):
                t.append({
                    'trans_date':trans.trans_date,
                    'employee_contribution': trans.employee_contribution,
                    'employer_contribution': trans.employer_contribution,
                    'units': trans.units,
                    'notes':trans.notes
                })
            eod['transactions'] = t
            nht = list()
            for nh in NAVHistory.objects.filter(account=so):
                nht.append({
                   'nav_value': nh.nav_value,
                   'nav_date':nh.nav_date,
                   'comparision_nav_value':nh.comparision_nav_value
                })
            eod['nav_history'] = nht
            data.append(eod)
        
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret

    @classmethod
    def raise_alerts(self):
        today = datetime.date.today()
        for ao in Account401K.objects.filter(end_date=None):
            trans = Transaction401K.objects.filter(account=ao).order_by("-trans_date")
            if len(trans) < 2:
                pass
            else:
                diff1 = trans[0].trans_date - trans[1].trans_date
                last_trans_diff =  today - trans[0].trans_date
                expected_trans_date = trans[0].trans_date + diff1
                if  last_trans_diff > diff1:
                    print(f'{ao.company}: last transaction is {last_trans_diff} from today.  Expectation is to keep it {diff1}.  Raising an alarm')
                    cont = f"Missing transactions in account {ao.company} 401K since {expected_trans_date}"
                        
                    create_alert_month_if_not_exist(
                        cont,
                        cont,
                        cont,
                        severity=Severity.warning,
                        alert_type="Action"
                    )
            nh_start = ao.start_date
            nh_end = ao.end_date if ao.end_date is not None else today
            nh_start = nh_start+relativedelta(months=1)
            nh_start = nh_start.replace(day=1)

            while nh_start <= nh_end:
                temp = nh_start+relativedelta(days=-7)
                nhos = NAVHistory.objects.filter(account=ao, nav_date__lte=nh_start,  nav_date__gte=temp)
                if len(nhos) == 0:
                    cont = f"Month end NAV for {ao.company} 401K for {temp.month}/{temp.year} missing"
                    print(cont+ ". Raising an alarm")
                            
                    create_alert_month_if_not_exist(
                        cont,
                        cont,
                        cont,
                        severity=Severity.warning,
                        alert_type="Action"
                    )
                else:
                    print(f'found {len(nhos)} transactions between {temp} and {nh_start}')
                nh_start = nh_start+relativedelta(months=1)
    
    @classmethod
    def updates_summary(self, ext_user, start_date, end_date):
        from users.user_interface import get_users
        from shared.financial import xirr, calc_simple_roi

        diff_days = (end_date - start_date).days

        ret = dict()
        ret['details'] = list()
        ids = list()
        for u in get_users(ext_user):
            ids.append(u.id)
        objs = Account401K.objects.filter(user__in=ids)
        start = 0
        bought = 0
        sold = 0
        e = dict()
        amt = 0
        for obj in objs:
            start_units = obj.units
            end_units = float(obj.units)
            nav_from_trans = dict()

            for tran in Transaction401K.objects.filter(account=obj, trans_date__gte=start_date):
                cont = float(tran.employee_contribution+tran.employer_contribution)
                conv_rate = 1
                conv_val = get_in_preferred_currency(1, 'USD', tran.trans_date)
                if conv_val:
                    conv_rate = conv_val
                bought += conv_rate*cont
                start_units -= tran.units
                nav_from_trans[tran.trans_date] = float((tran.employee_contribution+tran.employer_contribution)/tran.units)

            if start_units > 0:
                dt, val = get_nearest_nav(obj, start_date)
                if dt:
                    conv_rate = 1
                    conv_val = get_in_preferred_currency(1, 'USD', start_date)
                    if conv_val:
                        conv_rate = conv_val
                    start += float(val)*float(conv_rate)*float(start_units)
                elif start_date in nav_from_trans:
                    conv_rate = 1
                    conv_val = get_in_preferred_currency(1, 'USD', start_date)
                    if conv_val:
                        conv_rate = conv_val
                    start += nav_from_trans[start_date]*float(conv_rate)*float(start_units)
                else:
                    print(f'failed to get nav for {obj.company} {start_date}')
            if end_units > 0:
                dt, val = get_nearest_nav(obj, end_date)
                if dt:
                    conv_rate = 1
                    conv_val = get_in_preferred_currency(1, 'USD', end_date)
                    if conv_val:
                        conv_rate = conv_val
                    amt += float(val)*float(conv_rate)*float(end_units)
                elif end_date in nav_from_trans:
                    conv_rate = 1
                    conv_val = get_in_preferred_currency(1, 'USD', end_date)
                    if conv_val:
                        conv_rate = conv_val
                    amt += nav_from_trans[end_date]*float(conv_rate)*float(end_units)
                else:
                    print(f'failed to get nav for {obj.company} {end_date}')
        ret['start'] = round(start, 2)
        ret['bought'] = round(bought, 2)
        ret['sold'] = round(sold, 2)
        ret['balance'] = round(amt, 2)
        if start!= 0 and amt != 0:
            changed = float(start+bought-sold)
            if changed != float(amt):
                if diff_days >= 365:
                    cash_flows = list()
                    cash_flows.append((start_date, -1*float(changed)))
                    cash_flows.append((end_date, float(amt)))
                    print(f'finding xirr for {cash_flows}')
                    ret['change'] = xirr(cash_flows, 0.1)*100
                else:
                    ret['change'] = calc_simple_roi(changed , amt)
        if not 'change' in ret:
            ret['change'] = 0
        ret['details'].append(e)
        return ret

    @classmethod
    def updates_email(self, ext_user, start_date, end_date):
        update = self.updates_summary(ext_user, start_date, end_date)
        from shared.email_html import get_weekly_update_table
        ret = dict()
        col_names = ['Start','New Contribution','Balance', 'Change']
        if update['change'] >= 0:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>{update['change']}%"""
        else:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#df2028">▼</span>{update['change']}%"""
        values = [update['start'] if update['start'] != 0 else 'Unknown', update['bought'],  update['balance'] if update['balance'] != 0 else 'Unknown', change]
        ret['content'] = get_weekly_update_table('401K', col_names, values)
        ret['start'] = update['start']
        ret['credits'] = update['bought']
        ret['debits'] = update['sold']
        ret['balance'] = update['balance']
        print(f'ret {ret}')
        return ret
