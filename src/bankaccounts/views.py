from django.shortcuts import render
from bankaccounts.bank_account_helper import is_a_loan_account
from shared.utils import *
from shared.handle_get import *
from .models import BankAccount, Transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import IntegrityError
import requests
from decimal import Decimal
import datetime
from goal.goal_helper import get_goal_id_name_mapping_for_user
from shared.handle_real_time_data import get_in_preferred_currency
from tasks.tasks import update_bank_acc_bal, upload_bank_account_transactions
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from common.helper import get_preferred_currency_symbol

# Create your views here.


def get_accounts(request):
    template = 'bankaccounts/account_list.html'
    context = dict()
    context['users'] = get_all_users()
    user = None
    context['object_list'] = list()
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
    context['user_name_mapping'] = get_all_users()
    balance = 0
    loan_balance = 0
    accounts = BankAccount.objects.all()
    as_on = None
    for acc in accounts:
        last_trans = Transaction.objects.filter(account=acc).order_by('trans_date').last()
        last_trans_dt=None
        if last_trans:
            last_trans_dt = last_trans.trans_date
        acc.last_trans_dt = last_trans_dt

        first_trans = Transaction.objects.filter(account=acc).order_by('trans_date').first()
        first_trans_dt=None
        if first_trans:
            first_trans_dt = first_trans.trans_date
        acc.first_trans_dt = first_trans_dt
        acc.preferred_currency_bal = get_in_preferred_currency(float(acc.balance), acc.currency, datetime.date.today())
        context['object_list'].append(acc)
        if is_a_loan_account(acc.acc_type):
            loan_balance += get_in_preferred_currency(float(acc.balance), acc.currency, datetime.date.today())
        else:
            balance += get_in_preferred_currency(float(acc.balance), acc.currency, datetime.date.today())
        if not as_on:
            as_on = acc.as_on_date
        elif acc.as_on_date:
            as_on = acc.as_on_date if as_on > acc.as_on_date else as_on

    if as_on:
        #context['as_on_date'] = get_preferred_tz(as_on)
        context['as_on_date'] = as_on
    else:
        context['as_on_date'] = 'None'
    context['curr_module_id'] = 'id_bank_acc_module'
    context['preferred_currency_bal'] = round(balance, 2)
    context['preferred_currency_loan_bal'] = round(loan_balance, 2)
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
    context['user_name_mapping'] = get_all_users()
    context['preferred_currency'] = get_preferred_currency_symbol()
    return render(request, template, context)

def get_transactions(request, id):
    template = 'bankaccounts/transaction_list.html'
    context = dict()
    try:
        acc = BankAccount.objects.get(id=id)
        trans = Transaction.objects.filter(account=acc)
        context['object_list'] = list()
        for t in trans:
            context['object_list'].append(t)
        context['curr_module_id'] = 'id_bank_acc_module'
        context['account_id'] = acc.id
        context['number'] = acc.number
        return render(request, template, context)
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def add_transaction(request,id):
    template = 'bankaccounts/add_transaction.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        acc = BankAccount.objects.get(id=id)
        if request.method == 'POST':
            try:
                trans_date = request.POST['trans_date']
                notes = request.POST['notes']
                category = request.POST['tran_sub_type']
                trans_type = request.POST['tran_type']
                amount = get_float_or_none_from_string(request.POST['trans_amount'])
                description = request.POST['description']
                Transaction.objects.create(
                    account=acc,
                    trans_type=trans_type,
                    category=category,
                    amount=amount,
                    notes=notes,
                    trans_date=trans_date,
                    description=description
                )
                message = 'Transaction added successfully'
                message_color = 'green'
                update_bank_acc_bal(acc.id)
            except IntegrityError as ie:
                print(f'failed to add transaction {ie}')
                message = 'Failed to add transaction'
                message_color = 'red'
            except Exception as ex:
                print(f'failed to add transaction {ex}')
                message = 'Failed to add transaction'
                message_color = 'red'
        context['message'] = message
        context['message_color'] = message_color
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[acc.user]
        context['curr_module_id'] = 'id_bank_acc_module'
        context['account_id'] = acc.id
        context['number'] = acc.number
        context['bank_name'] = acc.bank_name
        return render(request, template, context)

    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def update_transaction(request, id, trans_id):
    template = 'bankaccounts/edit_transaction.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        acc = BankAccount.objects.get(id=id)
        try:
            trans = Transaction.objects.get(account=acc, id=trans_id)
            if request.method == 'POST':
                try:
                    message = 'Transaction updated successfully'
                    message_color = 'green'
                    if request.POST['notes'] and request.POST['notes'] != '':
                        trans.notes = request.POST['notes']
                    trans.category = request.POST['tran_sub_type']
                    trans.save()
                except Exception as ex:
                    print(f'failed to add transaction {ex}')
                    message = 'Failed to add transaction'
                    message_color = 'red'
            context['trans_date'] = trans.trans_date
            context['tran_type'] = trans.trans_type
            context['trans_amount'] = trans.amount
            context['description'] = trans.description
            context['message'] = message
            context['message_color'] = message_color
            user_name_mapping = get_all_users()
            context['user'] = user_name_mapping[acc.user]
            context['curr_module_id'] = 'id_bank_acc_module'
            context['account_id'] = acc.id
            context['number'] = acc.number
            context['bank_name'] = acc.bank_name
            context['category'] = trans.category
            context['notes'] = trans.notes
            return render(request, template, context)
        except Transaction.DoesNotExist:
            return HttpResponseRedirect(reverse('bankaccounts:get-transactions', args=[str(id)]))
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def add_account(request):
    template = 'bankaccounts/add_account.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        if request.method == 'POST':
            number = request.POST['number']
            bank_name = request.POST['bank_name']
            start_date = request.POST['start_date']
            user = request.POST['user']
            notes = request.POST['notes']
            currency = request.POST['currency']
            goal = request.POST.get('goal', '')
            acc_type = request.POST['acc_type']
            if goal != '':
                goal_id = Decimal(goal)
            else:
                goal_id = None
            if start_date == '':
                start_date = None
            else:
                start_date = get_date_or_none_from_string(start_date)
            BankAccount.objects.create(
                number=number,
                bank_name=bank_name,
                start_date=start_date,
                user=user,
                notes=notes,
                goal=goal_id,
                currency=currency,
                balance=0,
                acc_type=acc_type
            )
            message = 'Account added successfully'
            message_color = 'green'
    except IntegrityError as ie:
        print(f'failed to add bank account {ie}')
        message = 'Failed to add account'
        message_color = 'red'
    except Exception as ex:
        print(f'failed to add bank account {ex}')
        message = 'Failed to add account'
        message_color = 'red'
    url = f'https://raw.githubusercontent.com/krishnakuruvadi/portfoliomanager-data/main/currencies.json'
    print(f'fetching from url {url}')
    r = requests.get(url, timeout=15)
    context['currencies'] = list()
    if r.status_code == 200:
        for entry in r.json()['currencies']:
            context['currencies'].append(entry)
    else:
        context['currencies'].append('INR')
        context['currencies'].append('USD')
    context['message'] = message
    context['message_color'] = message_color
    users = get_all_users()
    context['users'] = users
    context['curr_module_id'] = 'id_bank_acc_module'
    return render(request, template, context)


def update_account(request, id):
    template = 'bankaccounts/update_account.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        ba = BankAccount.objects.get(id=id)
        if request.method == 'POST':
            try:
                number = request.POST['number']
                bank_name = request.POST['bank_name']
                start_date = request.POST['start_date']
                notes = request.POST['notes']
                currency = request.POST['currency']
                acc_type = request.POST['acc_type']
                goal = request.POST.get('goal', '')
                print(f'goal {goal}')
                if goal != '':
                    goal_id = Decimal(goal)
                else:
                    goal_id = None
                if start_date == '':
                    start_date = None
                else:
                    start_date = get_date_or_none_from_string(start_date)
                ba.number=number
                ba.bank_name=bank_name
                ba.start_date=start_date
                ba.notes=notes
                ba.goal=goal_id
                ba.currency=currency
                ba.acc_type = acc_type
                ba.save()
                message = 'Account updated successfully'
                message_color = 'green'
                update_bank_acc_bal(ba.id)
            except IntegrityError as ie:
                print(f'failed to update bank account {ie}')
                message = 'Failed to update account'
                message_color = 'red'
            except Exception as ex:
                print(f'failed to update bank account {ex}')
                message = 'Failed to update account'
                message_color = 'red'
        url = f'https://raw.githubusercontent.com/krishnakuruvadi/portfoliomanager-data/main/currencies.json'
        print(f'fetching from url {url}')
        r = requests.get(url, timeout=15)
        context['currencies'] = list()
        if r.status_code == 200:
            for entry in r.json()['currencies']:
                context['currencies'].append(entry)
        else:
            context['currencies'].append('INR')
            context['currencies'].append('USD')
        context['message'] = message
        context['message_color'] = message_color
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[ba.user]
        context['number'] = ba.number
        context['currency'] = ba.currency
        context['notes'] = ba.notes
        context['bank_name'] = ba.bank_name
        context['acc_type'] = ba.acc_type
        context['goal'] = ba.goal if ba.goal else ''
        context['goals'] = get_goal_id_name_mapping_for_user(ba.user)
        
        context['curr_module_id'] = 'id_bank_acc_module'
        print(context)
        return render(request, template, context)
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def account_detail(request, id):
    template = 'bankaccounts/account_detail.html'
    context = dict()
    try:
        acc = BankAccount.objects.get(id=id)
        context['curr_module_id'] = 'id_bank_acc_module'
        context['balance_preferred_currency'] = round(get_in_preferred_currency(float(acc.balance), acc.currency, datetime.date.today()), 2)
        goal_name_mapping = get_all_goals_id_to_name_mapping()
        if acc.goal:
            context['goal'] = goal_name_mapping[acc.goal]
        else:
            context['goal'] = None
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[acc.user]
        context['preferred_currency'] = get_preferred_currency_symbol()
        context['number'] = acc.number
        context['bank_name'] = acc.bank_name
        context['acc_type'] = acc.acc_type
        context['currency'] = acc.currency
        context['as_on_date'] = acc.as_on_date
        context['start_date'] = acc.start_date
        context['balance'] = acc.balance
        bal_vals = list()
        chart_labels = list()
        balance = 0
        
        prev_trans = None
        for trans in Transaction.objects.filter(account=acc).order_by('trans_date'):
            if trans.trans_type == 'Credit':
                balance += float(trans.amount)
            else:
                balance -= float(trans.amount)
            balance = round(balance, 2)
            if len(bal_vals) == 0:
                bal_vals.append(balance)
                chart_labels.append(trans.trans_date.strftime('%Y-%m-%d'))
            else:
                if float(trans.amount) > balance/10 or prev_trans.month != trans.trans_date.month or prev_trans.year != trans.trans_date.year:
                    bal_vals.append(balance)
                    chart_labels.append(trans.trans_date.strftime('%Y-%m-%d'))
            prev_trans = trans.trans_date
        if len(bal_vals) > 0:
            bal_vals.append(balance)
            chart_labels.append(datetime.date.today().strftime('%Y-%m-%d'))
        context['bal_vals'] = bal_vals
        context['chart_labels'] = chart_labels
        return render(request, template, context)
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def delete_accounts(request):
    BankAccount.objects.all().delete()
    return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def delete_account(request, id):
    try:
        ba = BankAccount.objects.get(id=id)
        ba.delete()
    except BankAccount.DoesNotExist:
        print(f'account with id does not exist {id}')
    return HttpResponseRedirect('../')

def transaction_detail(request, id, trans_id):
    pass

def delete_transactions(request, id):
    try:
        ba = BankAccount.objects.get(id=id)
        Transaction.objects.filter(account=ba).delete()
        update_bank_acc_bal()
        return HttpResponseRedirect(reverse('bankaccounts:get-transactions', args=[str(id)]))
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))


def delete_transaction(request, id, trans_id):
    try:
        ba = BankAccount.objects.get(id=id)
        try:
            Transaction.objects.get(account=ba, id=trans_id).delete()
            update_bank_acc_bal(ba.id)
        except Transaction.DoesNotExist:
            return HttpResponseRedirect(reverse('bankaccounts:get-transactions', args=[str(id)]))
        return HttpResponseRedirect(reverse('bankaccounts:get-transactions', args=[str(id)]))
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def upload_transactions(request, id):
    template = 'bankaccounts/upload_transactions.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        acc = BankAccount.objects.get(id=id)
        if request.method == 'POST':
            try:
                uploaded_file = request.FILES['document']
                fs = FileSystemStorage()
                file_locn = fs.save(uploaded_file.name, uploaded_file)
                print(settings.MEDIA_ROOT)
                full_file_path = settings.MEDIA_ROOT + '/' + file_locn
                file_type = request.POST['file_format']
                print(f'Read transactions from file: {uploaded_file} {file_type} {file_locn} {full_file_path}')
                passwd = request.POST['cas-pass']
                upload_bank_account_transactions(full_file_path, acc.bank_name, file_type, acc.number, acc.id, passwd)
                message = 'Upload successful. Processing file'
                message_color = 'green'
            except Exception as ex:
                print(f'failed to upload transactions {ex}')
                message = 'Failed to upload transactions'
                message_color = 'red'
        context['message'] = message
        context['message_color'] = message_color
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[acc.user]
        context['curr_module_id'] = 'id_bank_acc_module'
        context['account_id'] = acc.id
        context['number'] = acc.number
        context['bank_name'] = acc.bank_name
        return render(request, template, context)

    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def fr(val, precision=2):
    return round(float(val), precision)

class MultiCurr:
    def __init__(self):
        self.amount = dict()

    def add(self, curr, amount):
        self.amount[curr] = self.amount.get(curr, 0) + fr(amount)
    
    def sub(self, curr, amount):
        self.amount[curr] = self.amount.get(curr, 0) - fr(amount)

    def get_in_preferred_currency(self, end_date, prec=2):
        ret = 0
        for curr, val in self.amount.items():
            ret += get_in_preferred_currency(val, curr, end_date)
        return round(ret, prec)
    
def insights(request):
    template = "bankaccounts/insights.html"
    context = dict()
    context['users'] = get_all_users()
    context['accounts'] = dict()
    context['preferred_currency'] = get_preferred_currency_symbol()
    for ba in BankAccount.objects.all():
        if 'Loan' in ba.acc_type:
            continue
        if not ba.user in context['accounts']:
            context['accounts'][ba.user] = list()
        context['accounts'][ba.user].append(ba.number)
    if request.method == 'POST':
        print(request.POST)
        user = request.POST['user']
        # get from post as list
        sel_accounts = request.POST.getlist('accounts')
        date_from = get_date_or_none_from_string(request.POST['from_date'])
        date_to = get_date_or_none_from_string(request.POST['to_date'])
        context['user'] = user
        context['sel_accounts'] = sel_accounts
        context['from_date'] = request.POST['from_date']
        context['to_date'] = request.POST['to_date']
        context['curr_module_id'] = 'id_bank_acc_module'

        start_curr = MultiCurr()
        credits_curr = MultiCurr()
        debits_curr = MultiCurr()
        end_curr = MultiCurr()

        bas = None
        context['credit_labels'] = list()
        context['credit_vals'] = list()
        context['debit_labels'] = list()
        context['debit_vals'] = list()
        context['credit_colors'] = list()
        context['debit_colors'] = list()
        users = None
        if user == '':
            ext_user = get_ext_user(request)
            users = get_users_from_ext_user(ext_user)
        else:
            users = [user]
        if 'All' in sel_accounts:
            bas = BankAccount.objects.filter(user__in=users)
        else:
            bas = BankAccount.objects.filter(user__in=users, number__in=sel_accounts)
        end_dt = datetime.date.today()
        if end_dt < date_to:
            end_dt = date_to
        for ba in bas:
            if 'Loan' in ba.acc_type:
                continue
            for trans in Transaction.objects.filter(account=ba, trans_date__lt=end_dt).order_by("trans_date"):
                if trans.trans_date < date_from:
                    if trans.trans_type == 'Credit':
                        start_curr.add(ba.currency, trans.amount)
                        end_curr.add(ba.currency, trans.amount)
                    else:
                        start_curr.sub(ba.currency, trans.amount)
                        end_curr.sub(ba.currency, trans.amount)
                else:
                    if trans.trans_type == 'Credit':
                        end_curr.add(ba.currency, trans.amount)
                        cat = trans.category if trans.category else 'Other'
                        if cat != 'Self Transfer':
                            credits_curr.add(ba.currency, trans.amount)
                            if cat not in context['credit_labels']:
                                context['credit_labels'].append(cat)
                                t = MultiCurr()
                                t.add(ba.currency, trans.amount)
                                context['credit_vals'].append(t)
                            else:
                                # find string position in list
                                pos = context['credit_labels'].index(cat)
                                context['credit_vals'][pos].add(ba.currency, trans.amount)
                    else:
                        end_curr.sub(ba.currency, trans.amount)
                        cat = trans.category if trans.category else 'Other'
                        if cat != 'Self Transfer':
                            debits_curr.add(ba.currency, trans.amount)
                            if cat not in context['debit_labels']:
                                context['debit_labels'].append(cat)
                                t = MultiCurr()
                                t.add(ba.currency, trans.amount)
                                context['debit_vals'].append(t)
                            else:
                                # find string position in list
                                pos = context['debit_labels'].index(cat)
                                context['debit_vals'][pos].add(ba.currency, trans.amount)
        context['start'] = start_curr.get_in_preferred_currency(end_dt)
        context['end'] = end_curr.get_in_preferred_currency(end_dt)
        context['credits'] = credits_curr.get_in_preferred_currency(end_dt)
        context['debits'] = debits_curr.get_in_preferred_currency(end_dt)
        for _ in range(len(context['credit_labels'])):
            import random
            r = lambda: random.randint(0,255)
            context['credit_colors'].append('#{:02x}{:02x}{:02x}'.format(r(), r(), r()))
        for _ in range(len(context['debit_labels'])):
            import random
            r = lambda: random.randint(0,255)
            context['debit_colors'].append('#{:02x}{:02x}{:02x}'.format(r(), r(), r()))
        for i, val in enumerate(context['credit_vals']):
            context['credit_vals'][i] = val.get_in_preferred_currency(end_dt)
        for i, val in enumerate(context['debit_vals']):
            context['debit_vals'][i] = val.get_in_preferred_currency(end_dt) 
        print(f'context {context}')

        return render(request, template, context)
    context['start'] = 0
    context['end'] = 0
    context['credits'] = 0
    context['debits'] = 0
    context['curr_module_id'] = 'id_bank_acc_module'
    context['user_name_mapping'] = get_all_users()
    context['sel_accounts'] = list()
    print(f'context {context}')
    return render(request, template, context)
