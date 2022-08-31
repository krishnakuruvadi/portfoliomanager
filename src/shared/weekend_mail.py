from ssy.ssy_interface import SsyInterface
from epf.epf_interface import EpfInterface
from espp.espp_interface import EsppInterface
from fixed_deposit.fd_interface import FdInterface
from mutualfunds.mf_interface import MfInterface
from ppf.ppf_interface import PpfInterface
from retirement_401k.r401k_interface import R401KInterface
from shares.share_interface import ShareInterface
from rsu.rsu_interface import RsuInterface
from insurance.insurance_interface import InsuranceInterface
from gold.gold_interface import GoldInterface
from bankaccounts.bank_account_interface import BankAccountInterface
from crypto.crypto_interface import CryptoInterface
import datetime
from django.template.loader import render_to_string
from shared.financial import xirr, calc_simple_roi
from users.user_interface import get_users
from shared.handle_get import get_user_short_name_or_name_from_id
from common.helper import get_preferred_currency_symbol

def send_weekend_updates(ext_user=None):
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=7)
    short_names = list()
    for u in get_users(ext_user):
        short_names.append(get_user_short_name_or_name_from_id(u.id))
    context = dict()
    context['from_date'] = last_week.strftime('%Y-%m-%d')
    context['to_date'] = today.strftime('%Y-%m-%d')
    # list to comma separated string
    context['name'] = ', '.join(short_names)
    context['content'] = None
    start = 0
    credits = 0
    debits = 0
    total = 0
    for intf in [SsyInterface, PpfInterface, EpfInterface, EsppInterface, FdInterface, BankAccountInterface, RsuInterface, R401KInterface, MfInterface, ShareInterface, GoldInterface, CryptoInterface]:#   , InsuranceInterface,]:
        data = intf.updates_email(ext_user, last_week, today)
        print(f'data: {data}')
        if not context['content']:
            context['content'] = data['content']
        else:
            context['content'] += data['content']
        start += float(data['start'])
        credits += float(data['credits'])
        debits += float(data['debits'])
        total += float(data['balance'])
    '''
    ssy = SsyInterface.weekly_update_email(ext_user)
    context['content'] = ssy['content']
    start += ssy['start']
    credits += ssy['credits']
    debits += ssy['debits']
    total += ssy['balance']
    '''
    changed = float(start+credits-debits)
    if changed != float(total):
        '''
        cash_flows = list()
        cash_flows.append((last_week, -1*float(start+credits-debits)))
        cash_flows.append((today, float(total)))
        print(f'finding xirr for {cash_flows}')
        change = xirr(cash_flows, 0.1)*100
        '''
        change = calc_simple_roi(changed , total)
        if change >= 0:
            context['change'] = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>{round(change, 2)}%"""
        else:
            context['change'] = f"""<span style="margin-right:15px;font-size:18px;color:#df2028">▼</span>{round(change, 2)}%"""
    else:
        context['change'] = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>0%"""
    context['pref_curr'] = get_preferred_currency_symbol()
    mail = render_to_string('email_templates/weekly_email.html', context)
    print(f'{mail}')
    return mail
