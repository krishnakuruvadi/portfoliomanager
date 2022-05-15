from django.shortcuts import render
from django.urls import reverse
from shared.handle_get import *
from .models import Crypto, Transaction
from shared.handle_real_time_data import get_in_preferred_currency, get_preferred_currency
from common.helper import get_preferred_currency_symbol
from shared.utils import *
from shared.handle_real_time_data import  get_conversion_rate
from common.currency_helper import supported_currencies_as_list
from .crypto_interface import CryptoInterface
from django.http import HttpResponseRedirect
import json
import requests
from .crypto_helper import insert_trans_entry, get_crypto_coins, reconcile_event_based
from common.models import Coin, HistoricalCoinPrice
from tasks.tasks import pull_and_store_coin_historical_vals

# Create your views here.
def get_crypto(request):
    template = 'crypto/crypto_list.html'
    context = dict()
    context['object_list'] = list()
    extuser = get_ext_user(request)
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping(extuser)
    context['user_name_mapping'] = get_all_users(True, extuser)
    as_on = None
    userids_list = get_all_user_ids_as_list(extuser)
    cos = Crypto.objects.filter(user__in=userids_list)
    current_investment = 0
    latest_value = 0
    unrealised_gain = 0
    realised_gain = 0
    total_investment = 0
    for co in cos:
        total_investment += co.buy_value
        if co.latest_value:
            latest_value += co.latest_value
            current_investment += float(co.buy_value)
        unrealised_gain += co.unrealised_gain
        realised_gain += co.realised_gain
        context['object_list'].append(co)
        if not as_on:
            as_on = co.as_on_date
        
    context['total_investment'] = total_investment
    context['current_investment'] = round(current_investment, 2)
    context['latest_value'] = latest_value
    context['unrealised_gain'] = unrealised_gain
    context['realised_gain'] = realised_gain
    context['curr_module_id'] = CryptoInterface.get_module_id()
    if as_on:
        context['as_on_date'] = as_on
    print(context)
    context['preferred_currency'] = get_preferred_currency_symbol()    
    return render(request, template, context)

def update_crypto(request, id):
    template = 'crypto/update_crypto.html'
    try:
        cobj = Crypto.objects.get(id=id)
        if request.method == 'POST':
            goal = request.POST.get('goal', '')
            print('user is:',cobj.user)
            if goal != '':
                cobj.goal = int(goal)
            else:
                cobj.goal = None
            notes = request.POST['notes']
            cobj.notes = notes
            cobj.save()
        else:
            users = get_all_users()
            context = {
                        'users':users,
                        'symbol':cobj.symbol,
                        'user':cobj.user,
                        'goal':cobj.goal,
                        'notes':cobj.notes,
                        'curr_module_id':'id_crypto_module'
                    }
            return render(request, template, context)
        return HttpResponseRedirect(reverse('crypto:crypto-list'))  
    except Crypto.DoesNotExist:
        return HttpResponseRedirect(reverse('crypto:crypto-list'))       

def update_transaction(request, id, trans_id):
    template = 'crypto/update_transaction.html'
    try:
        cobj = Crypto.objects.get(id=id)
        trans = None
        try:
            trans = Transaction.objects.get(crypto=cobj, id=trans_id)
        except Transaction.DoesNotExist:
            return HttpResponseRedirect(reverse('crypto:crypto-list'))
        symbol = cobj.symbol
        user = cobj.user
        currencies = supported_currencies_as_list()
        users = get_all_users()
        preferred_currency = get_preferred_currency()
        if request.method == 'POST':
            if "submit" in request.POST:                
                trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
                trans_type = request.POST['trans_type']
                price = get_float_or_none_from_string(request.POST['price'])
                quantity = get_float_or_none_from_string(request.POST['quantity'])
                conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
                trans_price = get_float_or_none_from_string(request.POST['trans_price'])
                broker = request.POST['broker']
                notes = request.POST['notes']
                chosen_currency = request.POST['currency']
                fees = request.POST['charges']
                trans.trans_type = trans_type
                trans.price = price
                trans.units = quantity
                trans.conversion_rate = conversion_rate
                trans.trans_price = trans_price
                trans.broker = broker
                trans.notes = notes
                trans.fees = fees
                trans.buy_currency = chosen_currency
                trans.save()
            else:
                print('fetching exchange price')
                trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
                trans_type = request.POST['trans_type']
                price = get_float_or_none_from_string(request.POST['price'])
                charges = get_float_or_zero_from_string(request.POST['charges'])
                quantity = get_float_or_none_from_string(request.POST['quantity'])
                chosen_currency = request.POST['currency']
                exchange_rate = get_conversion_rate(chosen_currency, preferred_currency, trans_date)
                broker = request.POST['broker']
                context = {'users':users, 'operation': 'Update Transaction', 'conversion_rate':exchange_rate, 'curr_module_id': CryptoInterface.get_module_id(),
                            'trans_date':trans_date.strftime("%Y-%m-%d"), 'user':user,
                            'symbol':symbol, 'currencies':currencies, 'trans_type':trans_type,
                            'charges':charges,
                            'price':price, 'quantity':quantity,'preferred_currency':preferred_currency, 'currency':chosen_currency, 'broker':broker, 'symbol':symbol}
                return render(request, template, context)
        context = {'users':users, 'currencies':currencies, 'operation': 'Update Transaction', 'conversion_rate':trans.conversion_rate, 'curr_module_id': CryptoInterface.get_module_id(),
                    'preferred_currency':preferred_currency, 'symbol':symbol, 'user':user, 'trans_date':trans.trans_date.strftime("%Y-%m-%d"), 'trans_price':trans.trans_price,
                    'price':trans.price, 'quantity':trans.units, 'broker':trans.broker, 'notes':trans.notes, 'charges':trans.fees, 'currency':trans.buy_currency}
        print(f'view context: {context}')
        return render(request, template, context)
    except Crypto.DoesNotExist:
        return HttpResponseRedirect(reverse('crypto:crypto-list'))

def delete_transaction(request, id, trans_id):
    try:
        cobj = Crypto.objects.get(id=id)
        try:
            trans = Transaction.objects.get(crypto=cobj, id=trans_id)
            trans.delete()
            if len(Transaction.objects.filter(crypto=cobj)) == 0:
                cobj.delete()
        except Transaction.DoesNotExist:
            return HttpResponseRedirect(reverse('crypto:crypto-list'))
    except Crypto.DoesNotExist:
        return HttpResponseRedirect(reverse('crypto:crypto-list'))

def add_transaction(request):
    template = 'crypto/add_transaction.html'
    currencies = supported_currencies_as_list()
    users = get_all_users()
    preferred_currency = get_preferred_currency()
    if request.method == 'POST':
        if "submit" in request.POST:
            symbol = request.POST['symbol']
            user = request.POST['user']
            print('user is of type:',type(user))
            trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
            trans_type = request.POST['trans_type']
            price = get_float_or_none_from_string(request.POST['price'])
            quantity = get_float_or_none_from_string(request.POST['quantity'])
            conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
            trans_price = get_float_or_none_from_string(request.POST['trans_price'])
            broker = request.POST['broker']
            notes = request.POST['notes']
            chosen_currency = request.POST['currency']
            charges = get_float_or_zero_from_string(request.POST['charges'])
            insert_trans_entry(symbol, user, trans_type, quantity, price, trans_date, notes, broker, conversion_rate, charges, chosen_currency, trans_price)
        else:
            print('fetching exchange price')
            symbol = request.POST['symbol']
            user = request.POST['user']
            trans_date = get_datetime_or_none_from_string(request.POST['trans_date'])
            trans_type = request.POST['trans_type']
            price = get_float_or_none_from_string(request.POST['price'])
            charges = get_float_or_zero_from_string(request.POST['charges'])
            quantity = get_float_or_none_from_string(request.POST['quantity'])
            chosen_currency = request.POST['currency']
            exchange_rate = get_conversion_rate(chosen_currency, preferred_currency, trans_date)
            broker = request.POST['broker']
            coins = get_crypto_coins()
            context = {'users':users, 'operation': 'Add Transaction', 'conversion_rate':exchange_rate, 'curr_module_id': CryptoInterface.get_module_id(),
                        'trans_date':trans_date.strftime("%Y-%m-%d"), 'user':user, 
                        'symbol':symbol, 'currencies':currencies, 'trans_type':trans_type,
                        'charges':charges,
                        'price':price, 'quantity':quantity,'preferred_currency':preferred_currency, 'currency':chosen_currency, 'broker':broker, 'coins':coins}
            return render(request, template, context)
    coins = get_crypto_coins()
    context = {'users':users, 'currencies':currencies, 'operation': 'Add Transaction', 'conversion_rate':1, 'curr_module_id': CryptoInterface.get_module_id(),
                'preferred_currency':preferred_currency, 'coins':coins}
    print(f'view context: {context}')
    return render(request, template, context)

def all_transactions(request):
    template = 'crypto/transactions.html'
    context = dict()
    context['object_list'] = list()
    for trans in Transaction.objects.all():
        context['object_list'].append(trans)
    context['curr_module_id'] = CryptoInterface.get_module_id()
    context['crypto_name']=''
    context['user_name_mapping'] = get_all_users()
    return render(request, template, context)

def get_transactions(request, id):
    template = 'crypto/transactions.html'
    context = dict()
    context['object_list'] = list()
    try:
        co = Crypto.objects.get(id=id)
        for trans in Transaction.objects.filter(crypto=co):
            context['object_list'].append(trans)
    except Crypto.DoesNotExist:
        print(f'no crypto with id {id}')
        return HttpResponseRedirect("../")
    context['curr_module_id'] = CryptoInterface.get_module_id()
    context['crypto_name'] = co.symbol
    context['cypto_id'] = co.id
    context['user_name_mapping'] = get_all_users()
    return render(request, template, context)

def upload_transactions(request):
    #TBD: Implement me
    return HttpResponseRedirect(reverse('crypto:crypto-list'))


def delete_crypto(request, id):
    Crypto.objects.get(id=id).delete()
    return HttpResponseRedirect(reverse('crypto:crypto-list'))

def crypto_detail(request, id):
    template = 'crypto/crypto_detail.html'
    context = dict()
    try:
        crypto = Crypto.objects.get(id=id)
        context['curr_module_id'] = CryptoInterface.get_module_id()
        context['latest_value_preferred_currency'] = round(crypto.latest_value, 2)
        goal_name_mapping = get_all_goals_id_to_name_mapping()
        if crypto.goal:
            context['goal'] = goal_name_mapping[crypto.goal]
        else:
            context['goal'] = None
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[crypto.user]
        context['preferred_currency'] = get_preferred_currency_symbol()
        context['symbol'] = crypto.symbol
        context['as_on_date'] = crypto.as_on_date
        context['latest_value'] = crypto.latest_value
        bal_vals = list()
        price_vals = list()
        chart_labels = list()
        balance = 0
        
        prev_trans = None
        
        today = datetime.date.today()
        end_date = today
        transactions = Transaction.objects.filter(crypto=crypto).order_by('trans_date')
        if len(transactions) > 0:
            #bal_vals.append(transactions[0].trans_price)
            #chart_labels.append(transactions[0].trans_date.strftime('%Y-%m-%d'))
            new_trans = list()
            start_day = transactions[0].trans_date
            start_day = start_day.replace(day=1)
            start_day = start_day+relativedelta(months=1)
            i = 0
            try:
                coin = Coin.objects.get(symbol=crypto.symbol)
                while start_day < end_date:
                    print(f'start_day{start_day}')
                    while i < len(transactions):
                        if transactions[i].trans_date <= start_day:
                            new_trans.append(transactions[i])
                            i += 1
                        else:
                            break
                    qty, buy_value, buy_price, realised_gain, unrealised_gain = reconcile_event_based(transactions)
                    print(f'quantity is {qty} as of {start_day}')
                    if qty > 0:
                        try:
                            hcp = HistoricalCoinPrice.objects.get(coin=coin, date=start_day)
                            amt = get_in_preferred_currency(float(hcp.price*qty), 'USD', start_day)
                            bal_vals.append(amt)
                            price_vals.append(float(hcp.price))
                            chart_labels.append(start_day.strftime('%Y-%m-%d'))
                        except HistoricalCoinPrice.DoesNotExist:
                            pull_and_store_coin_historical_vals(crypto.symbol, start_day)
                        
                    start_day  = start_day+relativedelta(months=1)
                if today.day != 1 and len(bal_vals) > 0:
                    bal_vals.append(float(crypto.latest_value))
                    chart_labels.append(crypto.as_on_date.strftime('%Y-%m-%d'))
                    price_vals.append(float(crypto.latest_price))
                    
            except Coin.DoesNotExist:  
                pull_and_store_coin_historical_vals(crypto.symbol, start_day)
           
        context['bal_vals'] = bal_vals
        context['chart_labels'] = chart_labels
        context['price_vals'] = price_vals
        print(context)
        return render(request, template, context)
    except Crypto.DoesNotExist:
        return HttpResponseRedirect(reverse('crypto:crypto-list'))

def delete_all_crypto(request):
    Crypto.objects.all().delete()
    return HttpResponseRedirect(reverse('crypto:crypto-list'))

def transaction_detail(request, id, trans_id):
    #TBD: handle me
    return HttpResponseRedirect(reverse('crypto:crypto-list'))

def insights(request):
    #TBD: handle me
    template = 'crypto/investment_insights.html'
    return HttpResponseRedirect(reverse('crypto:crypto-list'))