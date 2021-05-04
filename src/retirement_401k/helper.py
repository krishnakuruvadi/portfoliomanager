from .models import Account401K, Transaction401K, NAVHistory
from shared.handle_real_time_data import get_forex_rate
from shared.financial import xirr
from django.conf import settings
import csv
import os
from shared.utils import *
from django.db import IntegrityError

def reconcile_401k():
    accounts = Account401K.objects.all()
    cash_flows = list()
    for account in accounts:
        total_units = 0
        employee_contrib = 0
        employer_contrib = 0
        latest_date = None
        latest_nav = 0
        for transaction in Transaction401K.objects.filter(account=account).order_by('trans_date'):
            total_units += transaction.units
            employee_contrib += transaction.employee_contribution
            employer_contrib += transaction.employer_contribution
            if not latest_date:
                latest_date = transaction.trans_date
                latest_nav = (transaction.employee_contribution+transaction.employer_contribution)/transaction.units
            else:
                if latest_date < transaction.trans_date:
                    latest_date = transaction.trans_date
                    latest_nav = (transaction.employee_contribution+transaction.employer_contribution)/transaction.units
            cash_flows.append((transaction.trans_date, -1*float(transaction.employee_contribution + transaction.employer_contribution)))

        account.units = total_units
        account.employee_contribution = employee_contrib
        account.employer_contribution = employer_contrib
        account.total = employee_contrib+employer_contrib

        if latest_date:
            nav_date, nav_value = get_latest_month_end_nav(account.id)
            if nav_date > latest_date:
                latest_date = nav_date
                latest_nav = nav_value
            fx = get_forex_rate(latest_date, 'USD', 'INR')
            account.latest_value = float(latest_nav)*float(account.units)*fx
            account.gain = float(account.latest_value) - float(account.total)*fx
            if len(cash_flows) > 1:
                cash_flows.append((latest_date, float(latest_nav)*float(account.units)))
                roi = xirr(cash_flows, 0.1)*100
                roi = round(roi, 2)
                account.roi = roi
            else:
                account.roi = 0
            account.nav = latest_nav
            account.nav_date = latest_date
        else:
            account.latest_value = 0
            account.roi = 0
            account.nav = 0
            account.nav_date = None
        account.save()

def get_nav_file_locn(id):
    location = os.path.join(settings.MEDIA_ROOT, '401k')
    nav_file = os.path.join(location, str(id)+'.csv')
    return nav_file

def upload_nav(id):
    nav_file = get_nav_file_locn(id)
    if os.path.exists(nav_file):
        with open(nav_file, mode='r') as csv_file:
            print("opened file as csv:", nav_file)
            csv_reader = csv.DictReader(csv_file, delimiter=",")
            account = Account401K.objects.get(id=id)
            for row in csv_reader:
                print(row)
                try:
                    date = get_date_or_none_from_string(row['Date'], format='%m/%d/%Y')
                    nav_value = get_float_or_none_from_string(row['NAV'])
                    NAVHistory.objects.create(account=account, nav_date=date, nav_value=nav_value)
                except IntegrityError:
                    print(f'NAV entry for {date} exists')

def create_nav_file(id):
    location = os.path.join(settings.MEDIA_ROOT, '401k')
    if not os.path.exists(location):
        os.makedirs(location)
    nav_file = os.path.join(location, str(id)+'.csv')
    if os.path.exists(nav_file):
        os.remove(nav_file)
    with open(nav_file, mode='w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Date", "NAV"])

def remove_nav_file(id):
    location = os.path.join(settings.MEDIA_ROOT, '401k')
    nav_file = os.path.join(location, str(id)+'.csv')
    if os.path.exists(nav_file):
        os.remove(nav_file)

def get_latest_month_end_nav(id):
    upload_nav(id)
    account = Account401K.objects.get(id=id)
    history = NAVHistory.objects.filter(account=account).order_by('-nav_date')
    if len(history) > 0:
        return history[0].nav_date, history[0].nav_value
    return 0

def get_401k_amount_for_goal(id):
    objs = Account401K.objects.filter(goal=id)
    total = 0
    for obj in objs:
        total += obj.latest_value
    return total

def get_401k_amount_for_user(user_id):
    objs = Account401K.objects.filter(user=user_id)
    total = 0
    for obj in objs:
        if obj.latest_value:
            total += obj.latest_value
    return total

def get_r401k_value_as_on(dt, currency='INR'):
    '''
    dt = input date as on type:datetime.date object
    users = all users
    '''
    if dt > datetime.date.today():
        dt = datetime.date.today()
    objs = Account401K.objects.all()
    total_value = 0
    for obj in objs:
        total_value += get_r401k_value_as_on_for_account(obj, dt, currency)
    return total_value

def get_r401k_value_as_on_for_account(account, dt, currency):
    latest_nav = 0
    latest_nav_date = None
    total_units = 0
    for trans in Transaction401K.objects.filter(account=account, trans_date__lte=dt):
        if latest_nav == 0:
            latest_nav = (trans.employee_contribution+trans.employer_contribution)/trans.units
            latest_nav_date = trans.trans_date
        total_units += trans.units
    if total_units == 0:
        return 0
    #check if nav table has latest value
    checkfrom = datetime.date(day=1,month=dt.month,year=dt.year)
    use_month = dt.month
    use_yr = dt.year
    if dt.month == 12:
        use_month = 1
        use_yr += 1
    else:
        use_month += 1
    checkto = datetime.date(day=1,month=use_month,year=use_yr)+relativedelta(days=-1)
    print(f"checking nav history table for data between {checkfrom} and {checkto}")
    for nav_h in NAVHistory.objects.filter(account=account, nav_date__lte=checkto, nav_date__gte=latest_nav_date).order_by('-nav_date'):
        print(f'found newer date {nav_h.nav_date} nav {str(nav_h.nav_value)}')
        latest_nav = nav_h.nav_value
        latest_nav_date = nav_h.nav_date
        break
    fr = 1
    if currency != 'USD':
        fr = get_forex_rate(dt, 'USD', currency)
    print(f'using units {str(total_units)}, forex rate {str(fr)}, nav {str(latest_nav)} on {latest_nav_date} for total calculation')
    total_value = float(total_units) * float(latest_nav) * float(fr)

    return round(total_value, 2)
            

def get_no_goal_amount():
    amt = 0
    for obj in Account401K.objects.all():
        if not obj.goal:
            amt += 0 if not obj.latest_value else obj.latest_value
    return amt

def get_yearly_contribution(id, currency='INR'):
    data =dict()
    years = list()
    er_contrib = list()
    em_contrib = list()
    int_contrib = list()
    total = list()
    try:
        account = Account401K.objects.get(id=id)
        for trans in Transaction401K.objects.filter(account=account).order_by('trans_date'):
            yr = trans.trans_date.year
            if yr not in years:
                years.append(yr)
                er_contrib.append(0)
                em_contrib.append(0)
                int_contrib.append(0)
                total.append(0)
            ind = years.index(yr)
            er_contrib[ind] += float(trans.employer_contribution)
            em_contrib[ind] += float(trans.employee_contribution)
        
        for i, yr in enumerate(years):
            dt = datetime.date(year=yr, month=12, day=31)
            if dt > datetime.date.today():
                dt = datetime.date.today()
            total[i] = int(get_r401k_value_as_on_for_account(account, dt, currency))
            fr = get_forex_rate(dt, 'USD', currency)
            er_contrib[i] *= fr
            em_contrib[i] *= fr
            er_contrib[i] = int(er_contrib[i])
            em_contrib[i] = int(em_contrib[i])
            if i != 0:
                int_contrib[i] = total[i] - total[i-1] - em_contrib[i] - er_contrib[i]
            else:
                int_contrib[i] = total[i] - em_contrib[i] - er_contrib[i]
        data['years'] = years
        data['er'] = er_contrib
        data['em'] = em_contrib
        data['int'] = int_contrib
        data['total'] = total

    except Account401K.DoesNotExist:
        print(f'no object with id {str(id)}) found')
    return data
