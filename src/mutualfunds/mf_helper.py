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

        if trans.folio.units and trans.folio.units > 0:
            current_folio_cash_flows.append((trans.trans_date, float(trans.trans_price) if trans.trans_type=='Sell' else float(-1*trans.trans_price)))
    
    for folio in folios:
        if folio.latest_value and folio.latest_value > 0:
            all_folio_cash_flows.append((datetime.date.today(), float(folio.latest_value)))
            current_folio_cash_flows.append((datetime.date.today(), float(folio.latest_value)))

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