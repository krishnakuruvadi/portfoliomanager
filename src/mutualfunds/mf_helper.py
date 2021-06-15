from .kuvera import Kuvera
from .coin import Coin
from .models import Folio, MutualFundTransaction, Sip
from common.models import MutualFund
from shared.utils import *
from django.db import IntegrityError
from django.core.files.storage import FileSystemStorage
from shared.financial import xirr
from alerts.alert_helper import create_alert, Severity
from os.path import isfile
import csv
from shared.handle_real_time_data import get_historical_nearest_mf_nav

def mf_add_transactions(broker, user, full_file_path):
    print('inside mf_add_transactions', broker, user, full_file_path)
    if broker == 'KUVERA':
        kuvera_helper = Kuvera(full_file_path)
        for trans in kuvera_helper.get_transactions():
            print("trans is", trans)
            insert_trans_entry(trans["folio"],
                               trans['fund'],
                               user,
                               trans["trans_type"],
                               trans["units"],
                               trans["nav"],
                               trans["trans_date"],
                               None,
                               'KUVERA',
                               1.0,
                               trans["trans_value"])
    if broker == 'COIN ZERODHA':
        coin_helper = Coin(full_file_path)
        for trans in coin_helper.get_transactions():
            print("trans is", trans)
            insert_trans_entry(trans["folio"],
                               trans['fund'],
                               user,
                               trans["trans_type"],
                               trans["units"],
                               trans["nav"],
                               trans["trans_date"],
                               None,
                               broker,
                               1.0,
                               trans["trans_value"])
    fs = FileSystemStorage()
    fs.delete(full_file_path)


def insert_trans_entry(folio, fund, user, trans_type, units, price, date, notes, broker, conversion_rate=1, trans_price=None):
    print(f'{folio}, {fund}, {user}, {trans_type}, {units}, {price}, {date}')
    folio_obj = None
    try:
        folio_objs = Folio.objects.filter(folio=folio)
        for fo in folio_objs:
            if fo.fund.code == fund:
                folio_obj = fo
                break

    except Folio.DoesNotExist:
        print("Couldnt find folio object:", folio)
    
    if not folio_obj:
        mf_obj = MutualFund.objects.get(code=fund)
        folio_obj = Folio.objects.create(folio=folio,
                                         fund=mf_obj,
                                         user=user,
                                         units=0,
                                         buy_price=0,
                                         buy_value=0,
                                         gain=0)
    if not trans_price:
        trans_price = price*units*conversion_rate
    try:
        trans = MutualFundTransaction.objects.filter(folio=folio_obj,
                                             trans_date=date,
                                             trans_type=trans_type,
                                             price=price,
                                             units=units)
        if len(trans) > 0:
            print('Transaction exists')
            return
        MutualFundTransaction.objects.create(folio=folio_obj,
                                             trans_date=date,
                                             trans_type=trans_type,
                                             price=price,
                                             units=units,
                                             conversion_rate=conversion_rate,
                                             trans_price=trans_price,
                                             broker=broker,
                                             notes=notes)
        if trans_type == 'Buy':
            new_units = get_float_or_zero_from_string(folio_obj.units)+units
            new_buy_value = get_float_or_zero_from_string(folio_obj.buy_value) + trans_price
            folio_obj.units = new_units
            folio_obj.buy_value = new_buy_value
            if float(new_units) == 0:
                folio_obj.buy_price = 0
            else:
                folio_obj.buy_price = new_buy_value/float(new_units)
            folio_obj.save()
        else:
            new_units = get_float_or_zero_from_string(folio_obj.units)-units
            if new_units:
                new_buy_value = get_float_or_zero_from_string(folio_obj.buy_value) - trans_price
                folio_obj.units = new_units
                folio_obj.buy_value = new_buy_value
                folio_obj.buy_price = new_buy_value/float(new_units)
                folio_obj.save()
            else:
                folio_obj.delete()
    except IntegrityError as ex:
        print('Transaction exists', ex)
    except Exception as exc:
        print('Exception occured during adding transaction', exc, folio, fund, user, trans_type, units, price, date)

def calculate_xirr_all_users():
    folios = Folio.objects.all()
    curr_folio_returns, all_folio_returns = calculate_xirr(folios)
    return round(curr_folio_returns, 2), round(all_folio_returns, 2)

def calculate_xirr(folios):
    current_folio_cash_flows = list()
    all_folio_cash_flows = list()

    folios_list = list()
    for folio in folios:
        folios_list.append(folio.folio)
    
    for trans in MutualFundTransaction.objects.all():
        if trans.folio.folio in folios_list:
            all_folio_cash_flows.append((trans.trans_date, float(trans.trans_price) if trans.trans_type=='Sell' else float(-1*trans.trans_price)))

        if trans.folio.folio in folios_list and trans.folio.units and trans.folio.units > 0:
            current_folio_cash_flows.append((trans.trans_date, float(trans.trans_price) if trans.trans_type=='Sell' else float(-1*trans.trans_price)))
    
    latest_value = 0
    for folio in folios:
        if folio.latest_value and folio.latest_value > 0:
            latest_value += float(folio.latest_value)
    if latest_value > 0:
        all_folio_cash_flows.append((datetime.date.today(), latest_value))
        current_folio_cash_flows.append((datetime.date.today(), latest_value))

    curr_folio_returns = 0
    all_folio_returns = 0

    if len(all_folio_cash_flows) > 0:
        all_folio_returns = round(xirr(all_folio_cash_flows, 0.1)*100, 2)
    if len(current_folio_cash_flows) > 0:
        curr_folio_returns = round(xirr(current_folio_cash_flows, 0.1)*100, 2)
    print(f'returning {curr_folio_returns}, {all_folio_returns}')
    return curr_folio_returns, all_folio_returns

def mf_add_or_update_sip_kuvera(sips):
    for sip in sips:
        try:
            print(f"name {sip['name']}")

            folios = Folio.objects.filter(folio=sip['folio'])
            folio = None
            if len(folios) > 1:
                for f in folios:
                    if f.fund.kuvera_name == sip['name']:
                        folio = f
            else:
                folio = folios[0]
            if not folio:
                description = 'Unable to decide on Folio with number ' + sip['folio'] + ' and KUVERA name ' + sip['name']
                create_alert(
                    summary='Folio:' + sip['folio'] + ' Failure to add a sip',
                    content= description,
                    severity=Severity.error
                )
                return
            mf_add_or_update_sip(folio=folio, amount=sip['amount'], date=sip['date'])
        except Folio.DoesNotExist:
            description = 'Folio by that number doesnt exist'
            create_alert(
                summary='Folio:' + sip['folio'] + ' Failure to add a sip since no folio by that number found',
                content= description,
                severity=Severity.error
            )
        except Exception as ex:
            print(f'failed while adding sip for {sip["folio"]}', ex)

def mf_add_or_update_sip_coin(sips, filename):
    mfs = list()
    if isfile(filename):
        ignored_folios = set()
        with open(filename, mode='r', encoding='utf-8-sig') as csv_file:
            print("opened file as csv:", filename)
            csv_reader = csv.DictReader(csv_file, delimiter=",")
            for row in csv_reader:
                    #client_id	isin	scheme_name	plan	transaction_mode	trade_date	ordered_at	folio_number	amount	units	nav	status	remarks
                for k,v in row.items():
                    if 'isin' in k:
                        isin = v.strip()
                    if 'folio_number'in k:
                        folio = v.strip()
                    if 'scheme_name' in k:
                        name = v.strip()
                    if 'plan' in k:
                        plan = v.strip()
                if isin and folio and name:
                    if not name in mfs:
                        mf = dict()
                        mf['name'] = name
                        mf['isin'] = isin
                        mf['folio'] = folio
                        mf['plan'] = plan
                        mfs.append(mf)
    print(mfs)
    print(sips)
    for sip in sips:
        try:
            folio = None
            for mf in mfs:
                if sip['name'] == mf['name'] and sip['plan'] == mf['plan']:
                    folio = mf['folio']
                    break

            if not folio:
                description = 'Unable to find Folio with COIN/ZERODHA name ' + sip['name'] + ' and plan ' + sip['plan']
                create_alert(
                    summary='Name: ' + sip['name'] + ' Failure to add a sip',
                    content= description,
                    severity=Severity.error
                )
                return 
            folios = Folio.objects.filter(folio=folio)
            if len(folios) == 1:
                folio = folios[0]
            else:
                description = 'Unable to decide on Folio for COIN/ZERODHA name ' + sip['name']
                create_alert(
                    summary='Name: ' + sip['name'] + ' Failure to add a sip',
                    content= description,
                    severity=Severity.error
                )
                return
            mf_add_or_update_sip(folio=folio, amount=sip['amount'], date=sip['date'])
        except Exception as ex:
            print(f'failed while adding sip for {k}', ex)

def mf_add_or_update_sip(folio, amount, date):
    try:
        sip = Sip.objects.get(folio=folio)
        sip.amount = amount
        sip.sip_date = date
        sip.save()
    except Sip.DoesNotExist:
        Sip.objects.create(folio=folio, sip_date=date, amount=amount)

def get_no_goal_amount():
    amt = 0
    for obj in Folio.objects.all():
        if not obj.goal:
            amt += 0 if not obj.latest_value else obj.latest_value
    return amt

def get_summary_for_range(obj, start_date, end_date):
    realised_gain = 0
    st_realised_gain = 0
    lt_realised_gain = 0
    income = 0
    c_trans = list()
    for trans in MutualFundTransaction.objects.filter(folio=obj, trans_date__lt=start_date).order_by('trans_date', 'trans_type'):
        if trans.trans_type == 'Buy':
            c_trans.append({'date':trans.trans_date, 'bought':trans.units, 'sold_before':0, 'sold_during':0, 'nav':trans.price})
        else:
            sell_units = trans.units
            for t in c_trans:   
                rem_units = t['bought'] - t['sold_before']
                if rem_units > 0:
                    units_to_consider = sell_units if sell_units < rem_units else rem_units
                    sell_units -= units_to_consider
                    t['sold_before'] += units_to_consider
                if sell_units == 0:
                    break
            if sell_units != 0:
                print(f'something seriously wrong here for folio {trans.folio.folio}')
                    
    units_at_start = 0
    start_amount = 0
    for t in c_trans:
        units_at_start += t['bought'] - t['sold_before']
    if units_at_start:
        hmp = get_historical_nearest_mf_nav(obj.fund.code, start_date)
        if not hmp:
            print(f'Failed to get nav for date {start_date}')
            return

        start_amount = hmp*float(units_at_start)
    
    investment = 0
    for trans in MutualFundTransaction.objects.filter(folio=obj, trans_date__range=[start_date, end_date]).order_by('trans_date', 'trans_type'):
        if trans.trans_type == 'Buy':
            c_trans.append({'date':trans.trans_date, 'bought':trans.units, 'sold_before':0, 'sold_during':0, 'nav':trans.price})
            investment += float(trans.trans_price)
        else:
            sell_units = trans.units
            for t in c_trans:   
                rem_units = t['bought'] - t['sold_before'] - t['sold_during']
                if rem_units > 0:
                    units_to_consider = sell_units if sell_units < rem_units else rem_units
                    sell_units -= units_to_consider
                    t['sold_during'] += units_to_consider
                    print(f'sold {units_to_consider}@{trans.price} which was bought at {t["nav"]}')
                    rg = float(units_to_consider*trans.price - units_to_consider*t['nav'])
                    realised_gain += rg
                    # TODO: adjust duration of long term here based on whether it is a equity mf or debt mf
                    lt_dur = 365
                    if abs((t['date'] - trans.trans_date).days)>=lt_dur:
                        lt_realised_gain += rg
                    else:
                        st_realised_gain += rg

                if sell_units == 0:
                    break
            if sell_units != 0:
                print(f'calculations went wrong here for folio {trans.folio.folio}')
            income += float(trans.trans_price)
    income -= (start_amount+investment)

    final_units = 0  
    for t in c_trans:
        if t['bought']-t['sold_before'] - t['sold_during'] > 0:
            final_units += t['bought'] - t['sold_before'] - t['sold_during']
    
    final_amount = 0
    
    if final_units:
        hmp = get_historical_nearest_mf_nav(obj.fund.code, end_date)
        if not hmp:
            print(f'Failed to get nav for date {end_date}')
            return

        final_amount = hmp*float(final_units)
        income += final_amount
    income = round(income, 2)
    final_amount = round(final_amount, 2)
    start_amount = round(start_amount, 2)
    investment = round(investment, 2)
    realised_gain = round(realised_gain, 2)
    lt_realised_gain = round(lt_realised_gain, 2)
    st_realised_gain = round(st_realised_gain, 2)

    return {'start':start_amount, 'final':final_amount, 'investment':investment, 'realised_gain':realised_gain, 'longterm_gain':lt_realised_gain, 'shortterm_gain':st_realised_gain, 'income':income}

def get_tax_for_user(user_id, start_date, end_date):
    data = list()
    for obj in Folio.objects.filter(user=user_id):
        summ = get_summary_for_range(obj, start_date, end_date)
        if summ:
            if summ['start'] > 0 or summ['final'] > 0 or summ['realised_gain'] > 0 or summ['income'] > 0:
                summ['folio'] = obj.folio
                summ['fund'] = obj.fund.code
                summ['name'] = obj.fund.name
                data.append(summ)
            else:
                print(f'{obj.folio} ignoring folio for date range {start_date} {end_date}')
    return data

def clean_mutual_fund_table():
    tbc = MutualFund.objects.filter(folio__isnull=True)
    total = MutualFund.objects.all()
    #print('following mutual funds will be cleaned')
    #for mf in tbc:
    #    print(f'{mf}')
    print(f'{len(tbc)}/{len(total)}  will be cleaned')
    tbc.delete()