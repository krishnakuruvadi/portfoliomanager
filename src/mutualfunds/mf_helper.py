from .kuvera import Kuvera
from .coin import Coin
from .models import Folio, MutualFundTransaction
from common.models import MutualFund
from shared.utils import *
from django.db import IntegrityError
from django.core.files.storage import FileSystemStorage
from shared.financial import xirr


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