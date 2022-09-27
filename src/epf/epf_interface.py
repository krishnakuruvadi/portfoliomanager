from shared.handle_real_time_data import get_in_preferred_currency
from .models import Epf, EpfEntry
import datetime
from dateutil.relativedelta import relativedelta

class EpfInterface:
    @classmethod
    def get_chart_name(self):
        return 'EPF'

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
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = Epf.objects.filter(user=user_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} epf {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        today = datetime.date.today()
        amt = 0
        if user_id:
            objs = Epf.objects.filter(user=user_id)
        else:
            objs = Epf.objects.all()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.total else get_in_preferred_currency(obj.total, 'INR', today)
        return amt

    #TODO: preferred currency changes
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
    
    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for epf_obj in Epf.objects.filter(user=user_id):
            for epf_trans in EpfEntry.objects.filter(epf_id=epf_obj, trans_date__gte=st_date, trans_date__lte=end_date):
                contrib += float(epf_trans.employer_contribution + epf_trans.employee_contribution)
                deduct += -1*float(epf_trans.withdrawl)
        contrib = get_in_preferred_currency(contrib, 'INR', end_date)
        deduct = get_in_preferred_currency(deduct, 'INR', end_date)
        return contrib, deduct
    
    @classmethod
    def get_user_monthly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = [0]*12
        deduct = [0]*12
        for epf_obj in Epf.objects.filter(user=user_id):
            for epf_trans in EpfEntry.objects.filter(epf_id=epf_obj, trans_date__gte=st_date, trans_date__lte=end_date):
                contrib[epf_trans.trans_date.month-1] += float(epf_trans.employer_contribution + epf_trans.employee_contribution)
                deduct[epf_trans.trans_date.month-1] += -1*float(epf_trans.withdrawl)
        
        for i in range(12):
            dt = datetime.date(year=yr, day=1, month=i+2)
            dt = dt+relativedelta(days=-1)
            contrib[i] = get_in_preferred_currency(contrib[i], 'INR', dt)
            deduct[i] = get_in_preferred_currency(deduct[i], 'INR', dt)

        print(f'returning {contrib} {deduct}')
        return contrib, deduct

    @classmethod
    def get_amount_for_user(self, user_id):
        epf_objs = Epf.objects.filter(user=user_id)
        total_epf = 0
        for epf_obj in epf_objs:
            epf_id = epf_obj.id
            amt = 0
            epf_trans = EpfEntry.objects.filter(epf_id=epf_id)
            for entry in epf_trans:
                amt += entry.employee_contribution + entry.employer_contribution + entry.interest_contribution - entry.withdrawl
            if amt < 0:
                amt = 0
            total_epf += amt
        return total_epf

    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt

    @classmethod
    def update_user(self, ext_user=None):
        from users.user_interface import get_users
        from pages.helper import get_investment_data
        from dateutil.relativedelta import relativedelta
        from .epf_helper import update_epf_vals
        from shared.utils import get_min
        from shared.handle_chart_data import get_in_preferred_currency

        users = get_users(ext_user)
        today = datetime.date.today()
        data_start_date = today
        for u in users:
            data_start_date = get_min(self.get_start_day_for_user(u.id), data_start_date)
        data_start_date = datetime.date(data_start_date.year, data_start_date.month, 1)
        epf_data = list()
        total_epf = 0
        epf_reset_on_zero = False
        epf_objs = Epf.objects.filter(user__in=users)
        print(f'epf obj count: {len(epf_objs)}')
        data_end_date = data_start_date
        epf_user_start_date = data_start_date
        while True:
            if data_end_date == today:
                break

            #print('Calculating for the month', data_start_date)
            data_end_date = data_start_date + relativedelta(months=+1)
            if data_end_date > today:
                data_end_date = today

            epf_entries = EpfEntry.objects.filter(epf_id__in=epf_objs, trans_date__year=data_start_date.year, trans_date__month=data_start_date.month)
            print(f'entries: {len(epf_entries)}')
            for epf_entry in epf_entries:
                total_epf += int(epf_entry.employee_contribution) + int(epf_entry.employer_contribution) + int(epf_entry.interest_contribution) - int(epf_entry.withdrawl)
            if total_epf != 0:
                if not epf_reset_on_zero:
                    epf_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
                epf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':get_in_preferred_currency(total_epf, 'INR', data_end_date)})
                epf_reset_on_zero = True
            elif epf_reset_on_zero:
                epf_reset_on_zero = False
                epf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})
            data_start_date  = data_start_date+relativedelta(months=1)
        inv_data = get_investment_data(ext_user)
        print(f'epf_data {epf_data}')
        inv_data.epf_data = epf_data
        inv_data.start_day_across_portfolio = get_min(inv_data.start_day_across_portfolio, epf_user_start_date)
        inv_data.save()

        update_epf_vals(users)


    @classmethod
    def get_export_name(self):
        return 'epf'
    
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
        for eo in Epf.objects.filter(user=user_id):
            eod = {
                'number': eo.number,
                'company': eo.company,
                'start_date': eo.start_date,
                'end_date': eo.end_date, 
                'notes':eo.notes,
                'uan':eo.uan,
                'eps':eo.eps,
                'goal_name':''
            }
            if eo.goal:
                eod['goal_name'] = get_goal_name_from_id(eo.goal)
            t = list()
            for trans in EpfEntry.objects.filter(epf_id=eo):
                t.append({
                    'trans_date':trans.trans_date,
                    'withdrawl':trans.withdrawl,
                    'reference': trans.reference,
                    'employee_contribution':trans.employee_contribution,
                    'employer_contribution':trans.employer_contribution,
                    'interest_contribution':trans.interest_contribution,
                    'notes':trans.notes
                })
            eod['transactions'] = t
            data.append(eod)
        
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret
    
    # TODO: conversion to preferred currency
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
        epf_objs = Epf.objects.filter(user__in=ids)
        start = 0
        credits = 0
        debits = 0
        interest = 0
        e = dict()
        amt = 0
        epf_trans = EpfEntry.objects.filter(epf_id__in=epf_objs).order_by("trans_date")
        for entry in epf_trans:
            if entry.trans_date >= start_date:
                credits += float(entry.employer_contribution + entry.employee_contribution)
                debits += float(entry.withdrawl)
                interest += float(entry.interest_contribution)
            else:
                start += float(entry.employer_contribution + entry.employee_contribution+ entry.interest_contribution)-1*float(entry.withdrawl)
            amt += float(entry.employer_contribution + entry.employee_contribution+ entry.interest_contribution)-1*float(entry.withdrawl)

        ret['start'] = round(start,2)
        ret['credits'] = round(credits,2)
        ret['debits'] = round(debits,2)
        ret['balance'] = round(amt,2)
        ret['interest'] = round(interest,2)
        balance = float(start+credits-debits)
        if balance != float(amt):
            if diff_days > 365:
                cash_flows = list()
                cash_flows.append((start_date, -1*float(balance)))
                cash_flows.append((end_date, float(amt)))
                print(f'finding xirr for {cash_flows}')
                ret['change'] = xirr(cash_flows, 0.1)*100
            else:
                ret['change'] = calc_simple_roi(balance , amt)
        else:
            ret['change'] = 0
        ret['details'].append(e)
        return ret

    @classmethod
    def updates_email(self, ext_user, start_date, end_date):
        update = self.updates_summary(ext_user, start_date, end_date)
        from shared.email_html import get_weekly_update_table
        ret = dict()
        col_names = ['Start','Credits','Debits','Interest','Balance', 'Change']
        if update['change'] >= 0:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>{round(update['change'], 2)}%"""
        else:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#df2028">▼</span>{round(update['change'], 2)}%"""
        values = [update['start'], update['credits'], update['debits'], update['interest'], update['balance'], change]
        ret['content'] = get_weekly_update_table('Employee Provident Fund', col_names, values)
        ret['start'] = round(update['start'], 2)
        ret['credits'] = round(update['credits'], 2)
        ret['debits'] = round(update['debits'], 2)
        ret['balance'] = round(update['balance'], 2)
        print(f'ret {ret}')
        return ret
