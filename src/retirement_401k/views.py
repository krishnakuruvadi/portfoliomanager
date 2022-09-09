from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from decimal import Decimal
from shared.handle_get import *
from shared.yahoo_finance_2 import YahooFinance2
from .models import Account401K, Transaction401K, NAVHistory
from shared.utils import *
from goal.goal_helper import get_goal_id_name_mapping_for_user
from django.http import HttpResponseRedirect
from django.views.generic import DeleteView
from .helper import reconcile_401k, get_yearly_contribution
from dateutil.relativedelta import relativedelta
from django.db import IntegrityError
from common.helper import get_preferred_currency_symbol
# Create your views here.


def delete_nav(request, id, nav_id):
    try:
        account = Account401K.objects.get(id=id)
        NAVHistory.objects.get(account=account,id=nav_id).delete()
        return HttpResponseRedirect(reverse('retirement_401k:account-detail',kwargs={'id':id}))
    except Account401K.DoesNotExist:
        return HttpResponseRedirect(reverse('retirement_401k:account-list'))
        
def add_nav(request, id):
    template_name = 'retirement_401k/add_nav.html'
    try:
        account = Account401K.objects.get(id=id)
        message = ''
        message_color = 'ignore'
        if request.method == 'POST':
            message_color = 'green'
            print(request.POST)
            date = get_date_or_none_from_string(request.POST['date'])
            nav_value = get_float_or_none_from_string(request.POST['nav'])
            try:
                NAVHistory.objects.create(account=account, nav_date=date, nav_value=nav_value)

                message = 'NAV addition successful'
            except IntegrityError:
                message = f'NAV entry for {date} exists'
                message_color = 'red'
            except Exception as ex:
                message = 'NAV add failed'
                message_color = 'red'
                print(f'Exception {ex} encountered during NAV add')

        context = {'company':account.company, 'id':account.id, 'message':message, 'message_color':message_color}
        context['curr_module_id'] = 'id_401k_module'
        return render(request, template_name, context)
    except Account401K.DoesNotExist:
        return HttpResponseRedirect(reverse('retirement_401k:account-list'))

def add_account(request):
    template_name = 'retirement_401k/account_create.html'
    message = ''
    message_color = 'ignore'
    if request.method == 'POST':
        print(request.POST)
        company = request.POST['company']
        start_date = get_date_or_none_from_string(request.POST['start_date'])
        end_date = get_date_or_none_from_string(request.POST['end_date'])
        user = request.POST['user']
        goal = request.POST.get('goal', '')
        notes = request.POST['notes']
        if goal != '':
            goal_id = Decimal(goal)
        else:
            goal_id = None
        account = Account401K.objects.create(
                company=company,
                start_date=start_date,
                end_date=end_date,
                user=user,
                goal=goal_id,
                notes=notes
            )
        message = 'Account addition successful'
        message_color = 'green'
    users = get_all_users()
    context = {'users':users, 'curr_module_id':'id_401k_module', 'message':message, 'message_color':message_color}
    return render(request, template_name, context)

def update_account(request, id):
    template_name = 'retirement_401k/account_update.html'
    account = get_object_or_404(Account401K, id=id)
    if request.method == 'POST':
        print(request.POST)
        company = request.POST['company']
        start_date = get_date_or_none_from_string(request.POST['start_date'])
        end_date = get_date_or_none_from_string(request.POST['end_date'])
        #user = request.POST['user']
        goal = request.POST.get('goal', '')
        notes = request.POST['notes']
        if goal != '':
            goal_id = Decimal(goal)
        else:
            goal_id = None
        account.company = company
        account.start_date = start_date
        account.end_date = end_date
        account.notes = notes
        account.goal = goal_id
        account.save()
    else:
        acct = dict()
        acct['id'] = account.id
        acct['company'] = account.company
        acct['start_date'] = account.start_date.strftime("%Y-%m-%d")
        if account.end_date:
            acct['end_date'] = account.end_date.strftime("%Y-%m-%d")
        acct['notes'] = account.notes
        goals = get_goal_id_name_mapping_for_user(account.user)
        acct['goal'] = account.goal
        acct['goals'] = goals
        acct['user'] = account.user
        acct['curr_module_id'] = 'id_401k_module'
        print(f'context {acct}')
        return render(request, template_name, acct)

    return HttpResponseRedirect(reverse('retirement_401k:account-list'))

def get_accounts(request):
    template_name = 'retirement_401k/account_list.html'
    accounts = Account401K.objects.all()
    context = dict()
    context['accounts'] = list()
    total_investment = 0
    latest_value = 0
    total_gain = 0
    for account in accounts:
        acct = dict()
        acct['id'] = account.id
        acct['company'] = account.company
        acct['start_date'] = account.start_date
        acct['end_date'] = account.end_date
        acct['employee_contribution'] = account.employee_contribution
        acct['employer_contribution'] = account.employer_contribution
        acct['notes'] = account.notes
        acct['as_on_date'] = account.nav_date
        acct['latest_value'] = account.latest_value
        if account.goal:
            acct['goal'] = get_goal_name_from_id(account.goal)
        acct['user'] = get_user_short_name_or_name_from_id(account.user)
        acct['total'] = account.total
        acct['roi'] = account.roi
        acct['gain'] = account.gain
        context['accounts'].append(acct)
        total_investment += float(account.employee_contribution + account.employer_contribution)
        latest_value += float(account.latest_value)
        total_gain += float(account.gain)
    total_investment = latest_value - total_gain
    context['total_investment'] = round(total_investment, 2)
    context['latest_value'] = round(latest_value, 2)
    context['total_gain'] = round(total_gain, 2)
    context['curr_module_id'] = 'id_401k_module'
    context['preferred_currency'] = get_preferred_currency_symbol()
    return render(request, template_name, context)

def links(request):
    template = 'retirement_401k/links.html'
    return render(request, template)

def account_detail(request, id):
    template_name = 'retirement_401k/account_detail.html'
    account = get_object_or_404(Account401K, id=id)
    acct = dict()
    acct['id'] = account.id
    acct['company'] = account.company
    acct['start_date'] = account.start_date
    acct['end_date'] = account.end_date
    acct['employee_contribution'] = account.employee_contribution
    acct['employer_contribution'] = account.employer_contribution
    acct['total'] = account.total
    acct['notes'] = account.notes
    acct['as_on_date'] = account.nav_date
    acct['lv_dollar'] = round(account.units*account.nav, 2)
    acct['units'] = account.units
    acct['latest_value'] = account.latest_value
    if account.goal:
        acct['goal'] = get_goal_name_from_id(account.goal)
    acct['user'] = get_user_name_from_id(account.user)
    acct['roi'] = account.roi
    acct['nav'] = account.nav
    chart_data = get_yearly_contribution(id)
    acct['years'] = chart_data['years']
    acct['er_vals'] = chart_data['er']
    acct['em_vals'] = chart_data['em']
    acct['in_vals'] = chart_data['int']
    acct['total_vals'] = chart_data['total']
    acct['nav_history'] = NAVHistory.objects.filter(account=account)
    #{{fund_vals|safe}}, {{voo_vals|safe}}, {{chart_labels|safe}}
    fund_vals = list()
    spy_vals = list()
    chart_labels = list()
    for nav in NAVHistory.objects.filter(account=account).order_by('nav_date'):
        chart_labels.append(nav.nav_date.strftime('%Y-%m-%d'))
        fund_vals.append(float(nav.nav_value))
        val = None
        if nav.comparision_nav_value and nav.comparision_nav_value != 0:
            val = float(nav.comparision_nav_value)
        else:
            yf = YahooFinance2('SPY')
            response = yf.get_historical_value(nav.nav_date, nav.nav_date+relativedelta(days=5))
            yf.close()
            val_date = None
            for k,v in response.items():
                if not val:
                    val = v
                    val_date = k
                else:
                    if val_date > k:
                        val_date = k
                        val = v
            if val:
                nav.comparision_nav_value = round(val, 2)
                nav.save()
            else:
                val = 0
        spy_vals.append(val)
    acct['fund_vals'] = fund_vals
    acct['chart_labels'] = chart_labels
    
    acct['spy_vals'] = spy_vals
    acct['preferred_currency_symbol'] = get_preferred_currency_symbol()
    acct['curr_module_id'] = 'id_401k_module'
    return render(request, template_name, acct)

def get_transactions(request, id):
    template_name = 'retirement_401k/transactions_list.html'
    try:
        account = Account401K.objects.get(id=id)
        context = dict()
        context['id'] = id
        context['company'] = account.company
        context['trans_list'] = list()
        for transaction in Transaction401K.objects.filter(account=account):
            trans = dict()
            trans['id'] = transaction.id
            trans['trans_date'] = transaction.trans_date
            trans['employee_contribution'] = transaction.employee_contribution
            trans['employer_contribution'] = transaction.employer_contribution
            trans['notes'] = transaction.notes
            trans['units'] = transaction.units
            context['trans_list'].append(trans)
        context['curr_module_id'] = 'id_401k_module'
        return render(request, template_name, context)
    except Account401K.DoesNotExist:
        return HttpResponseRedirect(reverse('retirement_401k:account-list'))

def add_transaction(request, id):
    template_name = 'retirement_401k/add_transaction.html'
    try:
        account = Account401K.objects.get(id=id)
        message = ''
        message_color = 'ignore'
        if request.method == 'POST':
            message_color = 'green'
            print(request.POST)
            trans_date = get_date_or_none_from_string(request.POST['trans_date'])
            employee_contribution = get_float_or_none_from_string(request.POST['employee_contribution'])
            employer_contribution = get_float_or_none_from_string(request.POST['employee_contribution'])
            notes = request.POST['notes']
            units = get_float_or_none_from_string(request.POST['units'])
            try:
                Transaction401K.objects.create(
                    account=account,
                    trans_date=trans_date,
                    employee_contribution=employee_contribution,
                    employer_contribution=employer_contribution,
                    units=units,
                    notes=notes
                )
                message = 'Transaction addition successful'
            except IntegrityError:
                message = 'Transaction already being tracked'
                message_color = 'red'
            except Exception as ex:
                message = 'Transaction add failed'
                message_color = 'red'
                print(f'Exception {ex} encountered during transaction add')
            reconcile_401k()

        context = {'company':account.company, 'id':account.id, 'operation':'Add', 'message':message, 'message_color':message_color}
        context['curr_module_id'] = 'id_401k_module'
        return render(request, template_name, context)
    except Account401K.DoesNotExist:
        return HttpResponseRedirect(reverse('retirement_401k:account-list'))

def edit_transaction(request, id, trans_id):
    template_name = 'retirement_401k/add_transaction.html'
    message = ''
    message_color = 'ignore'
    try:
        acc = Account401K.objects.get(id=id)
        try:
            transaction = Transaction401K.objects.get(id=trans_id)
            if request.method == 'POST':
                try:
                    print(request.POST)
                    trans_date = get_date_or_none_from_string(request.POST['trans_date'])
                    employee_contribution = get_float_or_none_from_string(request.POST['employee_contribution'])
                    employer_contribution = get_float_or_none_from_string(request.POST['employee_contribution'])
                    notes = request.POST['notes']
                    units = get_float_or_none_from_string(request.POST['units'])
                    transaction.trans_date = trans_date
                    transaction.employee_contribution = employee_contribution
                    transaction.employer_contribution = employer_contribution
                    transaction.units = units
                    transaction.notes = notes
                    transaction.save()
                    reconcile_401k()
                    message = 'Transaction updated'
                    message_color = 'green'
                except Exception as ex:
                    print(f'exception {ex} when editing transaction {trans_id}')
                    message = 'Transaction update failed'
                    message_color = 'red'
            context = {'company':transaction.account.company, 'id':transaction.account.id}
            context['trans_date'] = transaction.trans_date.strftime("%Y-%m-%d")
            context['employee_contribution'] = transaction.employee_contribution
            context['employer_contribution'] = transaction.employer_contribution
            context['notes'] = transaction.notes
            context['units'] = transaction.units
            context['operation'] = 'Edit'
            context['curr_module_id'] = 'id_401k_module'
            context['message'] = message
            context['message_color'] = message_color
            return render(request, template_name, context)
        except Exception as ex:
            print(f'failed to edit transaction {trans_id} for account {id}')
        return HttpResponseRedirect(reverse('retirement_401k:transaction-list', args=(id,)))
    except Account401K.DoesNotExist:
        print(f'failed to edit transaction {trans_id} for account {id}.  Account doesnt exist')
        return HttpResponseRedirect(reverse('retirement_401k:account-list'))

def delete_transaction(request, id, trans_id):
    try:
        acc = Account401K.objects.get(id=id)
        try:
            trans = Transaction401K.objects.get(id=trans_id, account=acc)
            trans.delete()
        except Exception as ex:
            print(f'failed to delete transction with id {trans_id} for account with id {id}')
        return HttpResponseRedirect(reverse('retirement_401k:transaction-list', args=(id,)))
    except Account401K.DoesNotExist:
        return HttpResponseRedirect(reverse('retirement_401k:account-list'))

def delete_401k(request, id):
    try:
        acc = Account401K.objects.get(id=id)
        acc.delete()
    except Exception as ex:
        print(f'failed to delete account with id {id}')
    return HttpResponseRedirect(reverse('retirement_401k:account-list'))
