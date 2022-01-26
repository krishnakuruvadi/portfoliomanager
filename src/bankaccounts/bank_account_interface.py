from .models import BankAccount, Transaction
import datetime
from shared.handle_real_time_data import get_in_preferred_currency
from decimal import Decimal

class BankAccountInterface:
    @classmethod
    def get_chart_color(self):
        return '#E3CA95'

    @classmethod
    def get_chart_name(self):
        return 'Cash'

    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = BankAccount.objects.filter(user=user_id)
            else:
                objs = BankAccount.objects.filter()
            
            for obj in objs:
                trans = Transaction.objects.filter(account=obj).order_by('trans_date')
                if len(trans) > 0:
                    if not start_day:
                        start_day = trans.first().trans_date
                    else:
                        start_day = start_day if start_day < trans.first().trans_date else trans.first().trans_date
        except Exception as ex:
            print(f'exception finding start day for Bank Account {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            valid_acc_types = ['Savings', 'Checking', 'Current', 'Other']
            objs = BankAccount.objects.filter(goal=goal_id, acc_type__in=valid_acc_types)
            for obj in objs:
                trans = Transaction.objects.filter(account=obj).order_by('trans_date')
                if len(trans) > 0:
                    if not start_day:
                        start_day = trans.first().trans_date
                    else:
                        start_day = start_day if start_day < trans.first().trans_date else trans.first().trans_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} Bank Account {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = BankAccount.objects.filter(user=user_id)
            for obj in objs:
                trans = Transaction.objects.filter(account=obj).order_by('trans_date')
                if len(trans) > 0:
                    if not start_day:
                        start_day = trans.first().trans_date
                    else:
                        start_day = start_day if start_day < trans.first().trans_date else trans.first().trans_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} Bank Account {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        valid_acc_types = ['Savings', 'Checking', 'Current', 'Other']
        if user_id:
            objs = BankAccount.objects.filter(user=user_id, acc_type__in=valid_acc_types)
        else:
            objs = BankAccount.objects.filter(acc_type__in=valid_acc_types)
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.balance else get_in_preferred_currency(float(obj.balance), obj.currency, datetime.date.today())
        return Decimal(amt)
    
    @classmethod
    def get_user_monthly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        contrib = [0]*12
        deduct = [0]*12
        valid_acc_types = ['Savings', 'Checking', 'Current', 'Other']
        for acc in BankAccount.objects.filter(user=user_id, acc_type__in=valid_acc_types):
            c = [0]*12
            d = [0]*12
            for trans in Transaction.objects.filter(account=acc, trans_date__lte=end_date, trans_date__gte=st_date):
                if trans.trans_type == 'Credit':
                    c[trans.trans_date.month-1] += float(trans.amount)
                else:
                    d[trans.trans_date.month-1] += float(trans.amount)
            for i in range(0,12):
                contrib[i] += get_in_preferred_currency(c[i], acc.currency, end_date)
                deduct[i] += -1*get_in_preferred_currency(d[i], acc.currency, end_date)
        return contrib, deduct

    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        contrib = 0
        deduct = 0
        valid_acc_types = ['Savings', 'Checking', 'Current', 'Other']
        for acc in BankAccount.objects.filter(user=user_id, acc_type__in=valid_acc_types):
            c = 0
            d = 0
            for trans in Transaction.objects.filter(account=acc, trans_date__lte=end_date, trans_date__gte=st_date):
                if trans.trans_type == 'Credit':
                    c += float(trans.amount)
                else:
                    d += float(trans.amount)
            contrib += get_in_preferred_currency(c, acc.currency, end_date)
            deduct += get_in_preferred_currency(d, acc.currency, end_date)
        return contrib, -1*deduct
    
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
        valid_acc_types = ['Savings', 'Checking', 'Current', 'Other']
        for obj in BankAccount.objects.filter(goal=goal_id, acc_type__in=valid_acc_types):
            c = 0
            d = 0
            tot = 0
            for t in Transaction.objects.filter(account=obj, trans_date__lte=end_date):
                if t.trans_type == 'Credit':
                    if t.trans_date >= st_date:
                        c += float(t.amount)
                        #cash_flows.append((t.trans_date, -1*float(t.amount)))
                    tot += float(t.amount)
                else:
                    if t.trans_date >= st_date:
                        d += -1 * float(t.amount)
                        #cash_flows.append((t.trans_date, float(t.amount)))
                    tot -= float(t.amount)
            contrib +=  get_in_preferred_currency(c, obj.currency, end_date)
            deduct += get_in_preferred_currency(d, obj.currency, end_date)
            total += get_in_preferred_currency(tot, obj.currency, end_date)
            cash_flows.append((end_date, -1*get_in_preferred_currency(tot, obj.currency, end_date)))
        return cash_flows, contrib, deduct, total
    
    @classmethod
    def get_amount_for_goal(self, goal_id):
        amt = 0
        valid_acc_types = ['Savings', 'Checking', 'Current', 'Other']
        objs = BankAccount.objects.filter(goal=goal_id, acc_type__in=valid_acc_types)
        for obj in objs:
            amt += 0 if not obj.balance else get_in_preferred_currency(float(obj.balance), obj.currency, datetime.date.today())
        return amt
    
    @classmethod
    def get_amount_for_user(self, user_id):
        amt = 0
        valid_acc_types = ['Savings', 'Checking', 'Current', 'Other']
        objs = BankAccount.objects.filter(user=user_id, acc_type__in=valid_acc_types)
        for obj in objs:
            amt += 0 if not obj.balance else get_in_preferred_currency(float(obj.balance), obj.currency, datetime.date.today())
        return round(amt, 2)
    
    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt

    @classmethod
    def get_value_as_on(self, end_date):
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        amt = 0
        valid_acc_types = ['Savings', 'Checking', 'Current', 'Other']
        for acc in BankAccount.objects.filter(acc_type__in=valid_acc_types):
            b_amt = 0
            for trans in Transaction.objects.filter(account=acc, trans_date__lte=end_date):
                if trans.trans_type == 'Credit':
                    b_amt += float(trans.amount)
                else:
                    b_amt -= float(trans.amount)
            if b_amt > 0:
                amt += get_in_preferred_currency(b_amt, acc.currency, end_date)
        return round(amt, 2)

    @classmethod
    def get_loan_amount_for_user(self, user_id):
        amt = 0
        valid_acc_types = ['HomeLoan', 'CarLoan', 'PersonalLoan', 'OtherLoan']
        objs = BankAccount.objects.filter(user=user_id, acc_type__in=valid_acc_types)
        for obj in objs:
            amt += 0 if not obj.balance else get_in_preferred_currency(float(obj.balance), obj.currency, datetime.date.today())
        return round(amt, 2)
    
    @classmethod
    def get_loan_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_loan_amount_for_user(u.id)
        return amt

    @classmethod
    def get_loan_value_as_on(self, end_date):
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        amt = 0
        valid_acc_types = ['HomeLoan', 'CarLoan', 'PersonalLoan', 'OtherLoan']
        for acc in BankAccount.objects.filter(acc_type__in=valid_acc_types):
            b_amt = 0
            for trans in Transaction.objects.filter(account=acc, trans_date__lte=end_date):
                if trans.trans_type == 'Credit':
                    b_amt += float(trans.amount)
                else:
                    b_amt -= float(trans.amount)
            amt += get_in_preferred_currency(b_amt, acc.currency, end_date)
        return round(amt, 2)

    @classmethod
    def get_export_name(self):
        return 'bank_accounts'
    
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
        for ba in BankAccount.objects.filter(user=user_id):
            bad = {
                'number': ba.number,
                'bank_name': ba.bank_name,
                'currency': ba.currency,
                'notes':ba.notes,
                'start_date': ba.start_date,
                'acc_type':ba.acc_type,
                'goal_name':''
            }
            if ba.goal:
                bad['goal_name'] = get_goal_name_from_id(ba.goal)
            t = list()
            for trans in Transaction.objects.filter(account=ba):
                t.append({
                    'trans_date':trans.trans_date,
                    'trans_type':trans.trans_type,
                    'category': trans.category,
                    'amount':trans.amount,
                    'notes':trans.notes,
                    'description':trans.description
                })
            bad['transactions'] = t
            data.append(bad)
        
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret
