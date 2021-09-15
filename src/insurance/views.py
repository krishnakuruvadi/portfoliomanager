from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.db import IntegrityError
from .models import InsurancePolicy, NAVHistory, Transaction, Fund
from shared.utils import *
from goal.goal_helper import get_goal_id_name_mapping_for_user
from shared.handle_get import *
from django.http import HttpResponseRedirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from tools.ICICIPruLife import ICICIPruLife
from tasks.tasks import update_insurance_policy_vals

def add_fund(request, id):
    template_name = 'insurance/add_fund.html'
    try:
        policy = InsurancePolicy.objects.get(id=id)
        context = dict()
        message = ''
        message_color = 'ignore'
        
        if request.method == 'POST':
            message_color = 'green'
            print(request.POST)
            notes = request.POST['notes']
            fund_code = request.POST['fund_code']
            fund_name = request.POST['fund_name']
            try:
                Fund.objects.create(policy=policy,
                                    name=fund_name,
                                    code=fund_code)
                message = 'Fund added successfully'
            except IntegrityError as ex:
                print(f'{ex} exception during adding fund')
                message = 'Fund already being tracked'
                message_color = 'red'
            except Exception as ex:
                print(f'{ex} exception during adding fund')
                message = 'Failed to add fund'
                message_color = 'red'
        context['curr_module_id'] = 'id_insurance_module'
        context['policy'] = policy.policy
        context['policy_id'] = id
        context['message'] = message
        context['message_color'] = message_color
        return render(request, template_name, context)
    except InsurancePolicy.DoesNotExist:
        return HttpResponseRedirect('../')

def get_fund_names(policy_id):
    fund_names = dict()
    funds = Fund.objects.filter(policy=policy_id)
    for fund in funds:
        fund_names[fund.id] = fund.name
    return fund_names

def add_transaction(request, id):
    template_name = 'insurance/add_transaction.html'
    try:
        policy = InsurancePolicy.objects.get(id=id)
        context = dict()
        message = ''
        message_color = 'ignore'
        
        if request.method == 'POST':
            message_color = 'green'
            message = None
            print(request.POST)
            trans_date = get_date_or_none_from_string(request.POST['trans_date'])
            trans_amount = get_float_or_none_from_string(request.POST['trans_amount'])
            notes = request.POST['notes']
            
            trans_type = request.POST['tran_type']
            description = 'Premium Payment'
            if policy.policy_type != 'Term':
                description = request.POST['description']
            units = None
            nav = None
            fund = None
            skip_trans = False
            if policy.policy_type == 'ULIP':
                units = get_float_or_none_from_string(request.POST['units'])
                nav = get_float_or_none_from_string(request.POST['nav'])
                fund_id = get_int_or_none_from_string(request.POST['fund_name'])
                try:
                    fund = Fund.objects.get(policy=policy, id=fund_id)
                except Fund.DoesNotExist:
                    message = 'Invalid Fund'
                    message_color='red'
                    skip_trans = True

            if not skip_trans:
                try:
                    Transaction.objects.create(
                        policy=policy,
                        trans_date=trans_date,
                        trans_amount=trans_amount,
                        nav=nav,
                        units=units,
                        notes=notes,
                        description=description,
                        trans_type=trans_type,
                        fund=fund
                    )
                    message = 'Transaction added successfully'
                    update_insurance_policy_vals(policy.policy)
                except IntegrityError as ex:
                    print(f'{ex} exception during adding transaction')
                    message = 'Transaction already being tracked'
                    message_color = 'red'
                except Exception as ex:
                    print(f'{ex} exception during adding transaction')
                    message = 'Failed to add transaction'
                    message_color = 'red'

        context['curr_module_id'] = 'id_insurance_module'
        context['users'] = get_all_users()
        context['message'] = message
        context['message_color'] = message_color
        context['policy_id'] = id
        context['policy'] = policy.policy
        context['name'] = policy.name
        context['company'] = policy.company
        context['policy_type'] = policy.policy_type
        context['fund_names'] = get_fund_names(id)
        print(context)
        return render(request, template_name, context)
    except InsurancePolicy.DoesNotExist:
        return HttpResponseRedirect('../')


def upload_transactions(request, id):
    template_name = 'insurance/upload_transactions.html'
    try:
        policy = InsurancePolicy.objects.get(id=id)
        context = dict()
        message = ''
        message_color = 'ignore'
        
        if request.method == 'POST':
            message_color = 'green'
            message = None
            print(request.POST)
            uploaded_file = request.FILES['document']
            company = policy.company
            fs = FileSystemStorage()
            file_locn = fs.save(uploaded_file.name, uploaded_file)
            print(settings.MEDIA_ROOT)
            full_file_path = settings.MEDIA_ROOT + '/' + file_locn
            print(f'Read transactions from file: {uploaded_file} {company} {file_locn} {full_file_path}')
            add_transactions_from_file(company, policy, full_file_path)
            update_insurance_policy_vals(policy.policy)
        context['message'] = message
        context['message_color'] = message_color
        context['policy_id'] = policy.id
        context['policy'] = policy.policy
        context['policy_name'] = policy.name
        context['company'] = policy.company
        print(f'context: {context}')
        return render(request, template_name, context)
    except InsurancePolicy.DoesNotExist:
        print(f'InsurancePolicy with id {id} does not exist')
        return HttpResponseRedirect('../')

def get_transactions(request, id):
    template_name = 'insurance/transaction_list.html'
    try:
        for k,v in request.session.items():
            print(f'k: {k} v: {v}')

        context = dict()
        context['policy_id'] = id
        
        context['users'] = get_all_users()
        context['object_list'] = list()
        context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        context['user_name_mapping'] = get_all_users()

        objs = None
        p = InsurancePolicy.objects.get(id=id)
        context['policy'] = p.policy
        context['policy_type'] = p.policy_type
        objs = Transaction.objects.filter(policy=p)
        for t in objs:
            context['object_list'].append(t)
        context['message_color'] = request.session.pop('message_color', 'ignore')
        context['message'] = request.session.pop('message', '')
        context['curr_module_id'] = 'id_insurance_module'
        context['fund_names'] = get_fund_names(p)
        request.session.modified = True
        print(f'context: {context}')
        return render(request, template_name, context)
    except InsurancePolicy.DoesNotExist:
        print(f'InsurancePolicy with id {id} does not exist')
        return HttpResponseRedirect('../')

def delete_transaction(request,id,trans_id):
    msg = 'Transaction deleted'
    msg_color = 'green'
    try:
        policy = InsurancePolicy.objects.get(id=id)
        tr = Transaction.objects.get(policy=policy, id=trans_id)
        tr.delete()
    except InsurancePolicy.DoesNotExist:
        msg = 'Policy does not exist'
        msg_color = 'red'
    except Transaction.DoesNotExist:
        msg = 'Transaction does not exist'
        msg_color = 'red'
    request.session['message'] = msg # set 'token' in the session
    request.session['message_color'] = msg_color
    return HttpResponseRedirect(reverse('insurance:get-transactions',kwargs={'id':id}))

def transaction_detail(request, id, trans_id):
    pass

def add_policy(request):
    template_name = 'insurance/add_policy.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    
    if request.method == 'POST':
        message_color = 'green'
        print(request.POST)
        policy = request.POST['policy']
        name = request.POST['name']
        policy_type = request.POST['policy_type']
        company = request.POST['company']
        start_date = get_date_or_none_from_string(request.POST['start_date'])
        end_date = get_date_or_none_from_string(request.POST['end_date'])
        user = request.POST['user']
        goal = request.POST.get('goal', '')
        notes = request.POST['notes']
        sum_assured = get_float_or_zero_from_string(request.POST['sum_assured'])
        if goal != '':
            goal_id = Decimal(goal)
        else:
            goal_id = None
        try:
            policy = InsurancePolicy.objects.create(
                    company=company,
                    start_date=start_date,
                    end_date=end_date,
                    user=user,
                    goal=goal_id,
                    notes=notes,
                    policy_type=policy_type,
                    policy=policy,
                    name=name,
                    sum_assured=sum_assured
                )
            message = 'Policy added successfully'
        except IntegrityError as ex:
            print(f'{ex} exception during adding policy')
            message = 'Policy already being tracked'
            message_color = 'red'
        except Exception as ex:
            print(f'{ex} exception during adding policy')
            message = 'Failed to add policy'
            message_color = 'red'
        context['curr_module_id'] = 'id_insurance_module'
    else:
        context['curr_module_id'] = 'id_insurance_module'

    context['users'] = get_all_users()
    context['message'] = message
    context['message_color'] = message_color
    return render(request, template_name, context)

def get_insurance(request):
    template_name = 'insurance/policy_list.html'
    context = dict()
    context['users'] = get_all_users()
    context['object_list'] = list()
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
    context['user_name_mapping'] = get_all_users()
    total_investment = 0
    latest_value = 0
    as_on_date= None
    total_gain = 0
    total_sum_assured = 0
    objs = None
    objs = InsurancePolicy.objects.all()
    for ip in objs:
        if not as_on_date:
            as_on_date = ip.as_on_date
        else:
            if as_on_date < ip.as_on_date:
                as_on_date = ip.as_on_date
        if not ip.end_date or ip.end_date > datetime.date.today():
            total_sum_assured += ip.sum_assured
        latest_value += ip.latest_value
        total_investment += ip.buy_value
        total_gain += ip.gain
        context['object_list'].append(ip)
    context['as_on_date'] = as_on_date
    context['total_gain'] = round(total_gain, 2)
    context['total_investment'] = round(total_investment, 2)
    context['latest_value'] = round(latest_value, 2)
    cur_ret = 0
    all_ret = 0 
    context['curr_ret'] = cur_ret
    context['all_ret'] = all_ret
    context['total_sum_assured'] = total_sum_assured
    context['curr_module_id'] = 'id_insurance_module'
    return render(request, template_name, context)

def delete_policies(request):
    InsurancePolicy.objects.all().delete()
    return HttpResponseRedirect('../')

def policy_detail(request, id):
    template = 'insurance/policy_detail.html'
    try:
        o = InsurancePolicy.objects.get(id=id)
        context = dict()
        context['policy'] = o.policy
        context['name'] = o.name
        context['company'] = o.company
        context['start_date'] = o.start_date
        context['user'] = get_user_short_name_or_name_from_id(o.user)
        context['goal'] =  get_goal_name_from_id(o.goal)
        context['notes'] = o.notes
        context['end_date'] = o.end_date
        context['policy_type'] = o.policy_type
        context['roi'] = o.roi
        context['buy_value'] = o.buy_value
        context['latest_value'] = o.latest_value
        context['gain'] = o.gain
        context['sum_assured'] = o.sum_assured
        context['as_on_date'] = o.as_on_date
        context['curr_module_id'] = 'id_insurance_module'
        context['funds'] = list()
        for fund in Fund.objects.filter(policy=o):
            f = dict()
            f['name'] = fund.name
            f['units'] = fund.units
            f['nav'] = fund.nav
            f['nav_date'] = fund.nav_date
            context['funds'].append(f)
        return render(request, template, context)
    except InsurancePolicy.DoesNotExist:
        return HttpResponseRedirect('../')

def add_transactions_from_file(company, policy, full_file_path):
    if company == 'ICICI Prudential':
        ipru = ICICIPruLife(full_file_path)
        itrans = ipru.get_transactions()
        for fund_name, transactions in itrans.items():
            try:
                fund = Fund.objects.get(policy=policy, name=fund_name)
                for trans in transactions:
                    trans_type = None
                    if 'Allocated Premium' in trans['description']:
                        trans_type = 'Premium'
                    elif 'Rebalancing' in trans['description']:
                        if trans['trans_amount'] > 0:
                            trans_type='OtherCredits'
                        else:
                            trans_type='OtherDeductions'
                    elif 'Policy Administration Charge' in trans['description']:
                        trans_type='PolicyAdminCharges'
                    elif 'Education Cess' in trans['description']:
                        trans_type='OtherTaxes'
                    elif 'Central GST' in trans['description']:
                        trans_type='CentralGST'
                    elif 'State GST' in trans['description']:
                        trans_type='StateGST'
                    elif 'Service Tax' in trans['description']:
                        trans_type='OtherTaxes'
                    elif 'Cess' in trans['description']:
                        trans_type='OtherTaxes'
                    elif 'Bonus' in trans['description']:
                        trans_type='OtherCredits'
                    else:
                        print(f'ignoring transaction since we cant determine what type it is: {trans}')
                        continue
                    if trans['nav'] == 0:
                        if trans['units'] == 0:
                            trans['units'] = 0.01
                        trans['nav'] = trans['trans_amount']/trans['units']
                    insert_trans_entry(policy,
                                        fund,
                                        trans['date'],
                                        trans['trans_amount'],
                                        trans['nav'],
                                        trans['units'],
                                        '',
                                        trans['description'],
                                        trans_type)
            except Fund.DoesNotExist:
                print(f'failed to add transactions for fund {fund_name} (doesnt exist) for policy {policy.policy}')
    else:
        print(f'unsupported company to upload transactions from file {company} {full_file_path}')


def insert_trans_entry(policy, fund, trans_date, trans_amount, nav, units, notes, description, trans_type):
    try:
        Transaction.objects.create(
            policy=policy,
            trans_date=trans_date,
            trans_amount=trans_amount,
            nav=nav,
            units=units,
            notes=notes,
            description=description,
            trans_type=trans_type,
            fund=fund
        )
    except IntegrityError as ie:
        print(f'Transaction exists {ie}')
    except Exception as ex:
        print(f'exception {ex} when inserting transaction for policy {policy.id}: {policy.policy}')