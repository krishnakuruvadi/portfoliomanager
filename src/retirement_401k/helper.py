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
            account.latest_value = float(latest_nav)*float(account.units)*get_forex_rate(latest_date, 'USD', 'INR')
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

def upload_nav(id):
    location = os.path.join(settings.MEDIA_ROOT, '401k')
    nav_file = os.path.join(location, str(id)+'.csv')
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
    return history[0].nav_date, history[0].nav_value

def get_401k_amount_for_goal(id):
    objs = Account401K.objects.filter(goal=id)
    total = 0
    for obj in objs:
        total += obj.latest_value
    return total