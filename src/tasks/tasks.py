from huey.contrib.djhuey import task, periodic_task, db_task, db_periodic_task
from huey import crontab
from mutualfunds.models import Folio, MutualFundTransaction
from common.models import MutualFund, HistoricalMFPrice, MFYearlyReturns
from espp.models import Espp
from espp.espp_helper import update_latest_vals
from shared.handle_real_time_data import get_historical_year_mf_vals
from dateutil.relativedelta import relativedelta
import datetime
import time
from django.db.models import Q
from mftool import Mftool
from common.helper import update_mf_scheme_codes, update_category_returns
from shared.utils import get_float_or_zero_from_string, get_float_or_none_from_string, get_int_or_none_from_string, get_date_or_none_from_string, convert_date_to_string, get_diff
from common.bsestar import download_bsestar_schemes
from shared.handle_get import *
from shared.handle_chart_data import get_investment_data
from pages.models import InvestmentData
from mutualfunds.models import Folio, MutualFundTransaction
from mutualfunds.mf_helper import mf_add_transactions
import os
import json
from mutualfunds.mf_analyse import pull_ms, pull_category_returns, pull_blend, get_ms_code
from django.db import IntegrityError
from goal.goal_helper import update_all_goals_contributions
from .models import Task, TaskState
from alerts.alert_helper import create_alert, Severity
from shares.pull_zerodha import pull_zerodha
from shares.shares_helper import shares_add_transactions, update_shares_latest_val, check_discrepancies, reconcile_shares, add_untracked_transactions
from shared.financial import xirr
from shared.nasdaq import Nasdaq
from django.utils import timezone
from common.models import ScrollData, Preferences
import requests
from bs4 import BeautifulSoup
from json.decoder import JSONDecodeError
from markets.models import PEMonthy, PBMonthy
from django.db import IntegrityError
from common.helper import get_mf_passwords
from .tasks_helper import *
from common.nse import NSE


def set_task_state(name, state):
    try:
        task = Task.objects.get(task_name=name)
        
        if state.value == TaskState.Running.value:
            task.current_state = state.value
            task.last_run = datetime.datetime.now()
        else:
            task.last_run_status = state.value
            task.current_state = TaskState.Unknown.value
        task.save()
    except Task.DoesNotExist:
        print('Task ',name,' doesnt exist')

@db_periodic_task(crontab(minute='0', hour='*/12'))
def get_mf_navs():
    print('inside get_mf_navs')
    set_task_state('get_mf_navs', TaskState.Running)
    folios = Folio.objects.all()
    finished_funds = list()
    for folio in folios:
        if folio.fund.code not in finished_funds:
            finished_funds.append(folio.fund.code)
            print('trying folio', folio.folio, folio.fund.code)
            try:
                fund = MutualFund.objects.get(code=folio.fund.code)
                trans = MutualFundTransaction.objects.filter(folio=folio).order_by('trans_date')
                if len(trans) > 0:
                    start_trans = trans[0].trans_date
                    now = datetime.datetime.now()
                    for yr in range(start_trans.year, now.year+1, 1):
                        print('checking for year', yr)
                        end_date = datetime.date.today()
                        if yr != datetime.datetime.now().year:
                            end_date = datetime.datetime.strptime(str(yr)+'-12-31', '%Y-%m-%d').date()
                        criterion1 = Q(date__gt=end_date+relativedelta(days=-5))
                        criterion2 = Q(date__lt=end_date)
                        criterion3 = Q(code=fund.id)
                        entries = HistoricalMFPrice.objects.filter(criterion1 & criterion2 & criterion3)
                        if len(entries) == 0:
                            get_historical_year_mf_vals(fund.code, end_date.year)
                        else:
                            print('entries found', len(entries))
                else:
                    print('no transactions for folio', folio.folio, folio.fund.code)
            except Exception as ex:
                print('error getting mutual fund historical nav in periodic task', folio.fund.code, ex)
        else:
            print('folio ', folio.folio, ' with code ', folio.fund.code, ' already done')
    set_task_state('get_mf_navs', TaskState.Successful)

@db_periodic_task(crontab(minute='35', hour='*/12'))
def update_mf():
    print('Updating Mutual Fund with latest nav')
    set_task_state('update_mf', TaskState.Running)
    folios = Folio.objects.all()
    finished_funds = dict()
    mf = Mftool()
    for folio in folios:
        if not folio.units:
            continue
        if folio.fund.code not in finished_funds:
            print('Updating folio', folio.folio, folio.fund.code)
            try:
                fund = MutualFund.objects.get(code=folio.fund.code)
                q = mf.get_scheme_quote(folio.fund.code)
                if q:
                    finished_funds[folio.fund.code] = dict()
                    finished_funds[folio.fund.code]['val'] = get_float_or_zero_from_string(q['nav'])
                    finished_funds[folio.fund.code]['as_on'] = q['last_updated']
            except Exception as ex:
                print('error getting mutual fund nav in periodic task',folio.fund.code, ex)
                finished_funds[folio.fund.code] = None
        if finished_funds[folio.fund.code]:
            folio.latest_price = finished_funds[folio.fund.code]['val']
            folio.conversion_rate = 1 # TODO: change later
            folio.latest_value = float(folio.latest_price) * float(folio.conversion_rate) * float(folio.units)
            folio.gain=float(folio.latest_value)-float(folio.buy_value)
            folio.as_on_date = datetime.datetime.strptime(finished_funds[folio.fund.code]['as_on'], '%d-%b-%Y')
            cash_flows = list()
            for transaction in MutualFundTransaction.objects.filter(folio=folio):
                cash_flows.append((transaction.trans_date, float(transaction.trans_price) if transaction.trans_type=='Sell' else float(-1*transaction.trans_price)))
            if len(cash_flows) > 0:
                cash_flows.append((datetime.date.today(), folio.latest_value))
                #print('cash_flows', cash_flows)
                folio.xirr = xirr(cash_flows, 0.1)*100
            folio.save()
    set_task_state('update_mf', TaskState.Successful)

@db_periodic_task(crontab(minute='0', hour='*/2'))
def update_espp():
    print('Updating ESPP')
    set_task_state('update_espp', TaskState.Running)
    for espp_obj in Espp.objects.all():
        print("looping through espp " + str(espp_obj.id))
        update_latest_vals(espp_obj)
    set_task_state('update_espp', TaskState.Successful)

@db_periodic_task(crontab(minute='0', hour='10'))
def update_mf_schemes():
    print('Updating Mutual Fund Schemes')
    set_task_state('update_mf_schemes', TaskState.Running)
    update_mf_scheme_codes()
    set_task_state('update_mf_schemes', TaskState.Successful)

@db_periodic_task(crontab(minute='55', hour='*/12'))
def update_bse_star_schemes():
    print('Updating BSE STaR Schemes')
    set_task_state('update_bse_star_schemes', TaskState.Running)
    download_bsestar_schemes()
    set_task_state('update_bse_star_schemes', TaskState.Successful)

@db_periodic_task(crontab(minute='45', hour='*/12'))
def update_investment_data():
    set_task_state('update_investment_data', TaskState.Running)
    start_date = get_start_day_across_portfolio()
    investment_data = get_investment_data(start_date)
    try:
        all_investment_data = InvestmentData.objects.get(user='all')
        all_investment_data.ppf_data=investment_data['ppf']
        all_investment_data.epf_data=investment_data['epf']
        all_investment_data.ssy_data=investment_data['ssy']
        all_investment_data.fd_data=investment_data['fd']
        all_investment_data.espp_data=investment_data['espp']
        all_investment_data.rsu_data=investment_data['rsu']
        all_investment_data.shares_data=investment_data['shares']
        all_investment_data.mf_data=investment_data['mf']
        all_investment_data.total_data=investment_data['total']
        all_investment_data.r401k_data=investment_data['401K']
        all_investment_data.start_day_across_portfolio=start_date
        all_investment_data.as_on_date=datetime.datetime.now()
        all_investment_data.save()
    except InvestmentData.DoesNotExist:
        InvestmentData.objects.create(
            user='all',
            ppf_data=investment_data['ppf'],
            epf_data=investment_data['epf'],
            ssy_data=investment_data['ssy'],
            fd_data=investment_data['fd'],
            espp_data=investment_data['espp'],
            rsu_data=investment_data['rsu'],
            shares_data=investment_data['shares'],
            mf_data=investment_data['mf'],
            total_data=investment_data['total'],
            start_day_across_portfolio=start_date,
            as_on_date=datetime.datetime.now()
        )
    set_task_state('update_investment_data', TaskState.Successful)

@db_periodic_task(crontab(minute='0', hour='1'))
def clean_db():
    from markets.models import News
    set_task_state('clean_db', TaskState.Running)
    folios = Folio.objects.all()
    tracking_funds = set()
    for folio in folios:
        tracking_funds.add(folio.fund.code)
    print('funds being tracked', tracking_funds)
    for hmfp in HistoricalMFPrice.objects.all():
        if hmfp.code.code not in tracking_funds:
            print('Deleting unwanted entry', hmfp.id, hmfp.code, hmfp.date)
            hmfp.delete()
        else:
            if hmfp.date.year != datetime.datetime.now().year:
                if hmfp.date.day not in (25, 26, 27, 28, 29, 30, 31, 1, 2):
                    print('Deleting outdated entry', hmfp.id, hmfp.code, hmfp.date)
                    hmfp.delete()
            else:
                if hmfp.date.day not in (25, 26, 27, 28, 29, 30, 31, 1, 2) and abs(datetime.date.today() - hmfp.date).days > 7:
                    print('Deleting recent outdated entry', hmfp.id, hmfp.code, hmfp.date)
                    hmfp.delete()
    clear_date = datetime.date.today()+relativedelta(months=-1)
    for n in News.objects.filter(date__lt=clear_date):
        n.delete()
    set_task_state('clean_db', TaskState.Successful)

@task()
def add_mf_transactions(broker, user, full_file_path):
    mf_add_transactions(broker, user, full_file_path)

@db_periodic_task(crontab(minute='*/30', hour='*/4'))
def pull_mf_transactions():
    from mutualfunds.pull_kuvera import pull_kuvera
    from mutualfunds.pull_coin import pull_coin
    if is_task_run_today('pull_mf_transactions'):
        print('pull_mf_transactions task already run today successfully.  Not trying again')
        return
    set_task_state('pull_mf_transactions', TaskState.Running)
    passwords = get_mf_passwords()
    for passwd in passwords:
        if passwd['broker'] == 'KUVERA':
            #print(f"Pulling Kuvera for {passwd['user']} with user id {passwd['user_id']} and password {passwd['password']} with KUVERA username {passwd['additional_field']}")
            pull_kuvera(passwd['user'], passwd['user_id'], passwd['password'], passwd['additional_field'])
        elif passwd['broker'] == 'COIN ZERODHA':
            #print(f"Pulling COIN for {passwd['user']} with user id {passwd['user_id']} and password {passwd['password']} with 2fa {passwd['password2']}")
            pull_coin(passwd['user'], passwd['user_id'], passwd['password'], passwd['password2'])
    set_task_state('pull_mf_transactions', TaskState.Successful)

@db_periodic_task(crontab(minute='0', hour='2'))
def update_mf_mapping():
    set_task_state('update_mf_mapping', TaskState.Running)
    fp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mapping_file = os.path.join(fp, 'media', 'mf_mapping.json')
    if os.path.exists(mapping_file):
        with open(mapping_file) as f:
            data = json.load(f)
            for k,v in data.items():
                try:
                    fund = MutualFund.objects.get(code=k)
                    if 'kuvera_name' in v:
                        fund.kuvera_name = v['kuvera_name']
                    if 'ms_name' in v:
                        fund.ms_name = v['ms_name']
                    fund.save()
                except MutualFund.DoesNotExist:
                    if 'name' in v:
                        fund = MutualFund.objects.create(
                            code=k,
                            name=v['name'],
                            collection_start_date=datetime.datetime.today()
                        )
                        if 'kuvera_name' in v:
                            fund.kuvera_name = v['kuvera_name']
                        if 'ms_name' in v:
                            fund.ms_name = v['ms_name']
                        if 'isin' in v:
                            fund.isin = v['isin']
                        if 'isin2' in v:
                            fund.isin2 = v['isin2']
                    else:
                        create_alert(
                            summary='Code:' + k + ' Mutual fund not found',
                            content= 'Not able to find a matching Mutual Fund with the code.',
                            severity=Severity.error
                        )
        set_task_state('update_mf_mapping', TaskState.Successful)
    else:
        print(mapping_file + ' doesnt exist')
        set_task_state('update_mf_mapping', TaskState.Failed)

@db_periodic_task(crontab(minute='52', hour='2'))
def update_goal_contrib():
    set_task_state('update_goal_contrib', TaskState.Running)
    update_all_goals_contributions()
    set_task_state('update_goal_contrib', TaskState.Successful)

@db_periodic_task(crontab(minute='22', hour='2'))
def update_shares_latest_vals():
    set_task_state('update_shares_latest_vals', TaskState.Running)
    add_untracked_transactions()
    reconcile_shares()
    update_shares_latest_val()
    set_task_state('update_shares_latest_vals', TaskState.Successful)

@db_periodic_task(crontab(minute='35', hour='2'))
def analyse_mf():
    set_task_state('analyse_mf', TaskState.Running)
    folios = Folio.objects.all()
    for folio in folios:
        fund = folio.fund
        if not fund.ms_id or fund.ms_id == '':
            ret = get_ms_code(fund.name, fund.isin, fund.isin2, fund.ms_name)
            if ret:
                f = MutualFund.objects.get(id=fund.id)
                f.ms_id = ret
                f.save()
                print(f'set ms_id for {f.id} {f.name} as {ret}')

    ret = pull_category_returns()
    update_category_returns(ret)
    token = None
    finished_funds = set()
    for folio in folios:
        code = folio.fund.code
        if not folio.units or code in finished_funds:
            continue
        finished_funds.add(code)
        fund = MutualFund.objects.get(code=code)
        data, token = pull_ms(code, list(), token=token)
        if not data:
            create_alert(
                summary='Code:' + code + ' Mutual fund not analysed',
                content= 'Not able to find a matching Mutual Fund with the code for analysis.',
                severity=Severity.error
            )
            continue
        print('analysed data for mf', data)
        
        #{'blend': 'Large Growth', 'performance': {'2010': '—', '2011': '—', '2012': '—', '2013': '—', '2014': '1.55', '2015': '-14.06', '2016': '1.49', '2017': '13.54', '2018': '1.78', '2019': '31.88', 
        # 'YTD': '74.40', '1D': '-0.05', '1W': '-1.73', '1M': '8.27', '3M': '18.37', '1Y': '73.53', '3Y': '32.78', '5Y': '21.92', '10Y': '—', '15Y': '—', 'INCEPTION': '13.19'}}
        if 'blend' in data:
            fund.investment_style = data['blend']
        if 'categoryName' in data:
            fund.category = data['categoryName']
        if 'performance' in data:
            for k,v in data['performance'].items():
                if k == 'YTD':
                    fund.return_ytd = get_float_or_none_from_string(v)
                elif k == '1D':
                    fund.return_1d = get_float_or_none_from_string(v)
                elif k == '1W':
                    fund.return_1w = get_float_or_none_from_string(v)
                elif k == '1M':
                    fund.return_1m = get_float_or_none_from_string(v)
                elif k == '3M':
                    fund.return_3m = get_float_or_none_from_string(v)
                elif k == '1Y':
                    fund.return_1y = get_float_or_none_from_string(v)
                elif k == '3Y':
                    fund.return_3y = get_float_or_none_from_string(v)
                elif k == '5Y':
                    fund.return_5y = get_float_or_none_from_string(v)
                elif k == '10Y':
                    fund.return_10y = get_float_or_none_from_string(v)
                elif k == '15Y':
                    fund.return_15y = get_float_or_none_from_string(v)
                elif k == 'INCEPTION':
                    fund.return_incep = get_float_or_none_from_string(v)
                else:
                    yr = get_float_or_none_from_string(k)
                    returns = get_float_or_none_from_string(v)
                    if yr and returns:
                        try:
                            entry = MFYearlyReturns.objects.create(
                                fund=fund,
                                year=yr,
                                returns=returns
                            )
                        except IntegrityError:
                            entry = MFYearlyReturns.objects.get(fund=fund, year=yr)
                            entry.returns = returns
                            entry.save()
        if 'category' in data:
            for k,v in data['category'].items():
                if v:
                    if k == 'YTD':
                        k = str(datetime.date.today().year)
                    yr = get_int_or_none_from_string(k)
                    entry = None
                    try:
                        entry = MFYearlyReturns.objects.get(fund=fund, year=yr)
                    except MFYearlyReturns.DoesNotExist:
                        entry = MFYearlyReturns.objects.create(fund=fund, year=yr)
                    entry.diff_category = get_float_or_none_from_string(v)
                    entry.save()
        if 'fund' in data:
            for k,v in data['fund'].items():
                if v:
                    if k == 'YTD':
                        k = str(datetime.date.today().year)
                    yr = get_int_or_none_from_string(k)
                    entry = None
                    try:
                        entry = MFYearlyReturns.objects.get(fund=fund, year=yr)
                    except MFYearlyReturns.DoesNotExist:
                        entry = MFYearlyReturns.objects.create(fund=fund, year=yr)
                    entry.returns = get_float_or_none_from_string(v)
                    entry.save()
        if 'index' in data:
            for k,v in data['index'].items():
                if v:
                    if k == 'YTD':
                        k = str(datetime.date.today().year)
                    yr = get_int_or_none_from_string(k)
                    entry = None
                    try:
                        entry = MFYearlyReturns.objects.get(fund=fund, year=yr)
                    except MFYearlyReturns.DoesNotExist:
                        entry = MFYearlyReturns.objects.create(fund=fund, year=yr)
                    entry.diff_index = get_float_or_none_from_string(v)
                    entry.save()
        if 'percentileRank' in data:
            for k,v in data['percentileRank'].items():
                if v:
                    if k == 'YTD':
                        k = str(datetime.date.today().year)
                    yr = get_int_or_none_from_string(k)
                    entry = None
                    try:
                        entry = MFYearlyReturns.objects.get(fund=fund, year=yr)
                    except MFYearlyReturns.DoesNotExist:
                        entry = MFYearlyReturns.objects.create(fund=fund, year=yr)
                    entry.percentile_rank = get_int_or_none_from_string(v)
                    entry.save()
        if 'fundNumber' in data:
            for k,v in data['fundNumber'].items():
                if v:
                    if k == 'YTD':
                        k = str(datetime.date.today().year)
                    yr = get_int_or_none_from_string(k)
                    entry = None
                    try:
                        entry = MFYearlyReturns.objects.get(fund=fund, year=yr)
                    except MFYearlyReturns.DoesNotExist:
                        entry = MFYearlyReturns.objects.create(fund=fund, year=yr)
                    entry.funds_in_category = get_int_or_none_from_string(v)
                    entry.save()
        fund.save()
    set_task_state('analyse_mf', TaskState.Successful)

@db_periodic_task(crontab(day='1', minute='35', hour='3'))
def mf_update_blend():
    set_task_state('mf_update_blend', TaskState.Running)
    ms_codes = list()
    folios = Folio.objects.all()
    for folio in folios:
        if folio.fund.ms_id:
            ms_codes.append(folio.fund.ms_id)
    blend_data = pull_blend(ms_codes)
    print(blend_data)
    for k,v in blend_data.items():
        fund = MutualFund.objects.get(ms_id=k)
        fund.investment_style = v
        fund.save()
    set_task_state('mf_update_blend', TaskState.Successful)

@db_task()
def pull_share_trans_from_rh(user, broker, user_id, passwd, challenge_type, challenge_read_file):
    from shares.shares_helper import insert_trans_entry
    print(f'user {user} broker {broker} userid {user_id}')
    if broker == 'ROBINHOOD':
        from shares.pull_robinhood import Robinhood
        rh = Robinhood(user_id, passwd, challenge_type, None, challenge_read_file)
        try:
            rh.login()
            orders = rh.get_orders()
            for k,v in orders.items():
                for ord in v:
                    try:
                        ot = 'Buy' if ord['type'].lower()=='buy' else 'Sell'
                        insert_trans_entry('NASDAQ', k, user, ot, ord['quantity'], ord['price'], ord['date'], None, 'ROBINHOOD', ord['conv_price'], ord['trans_price'], ord['div_reinv'])
                    except IntegrityError:
                        print(f'transaction exists')

        except Exception as ex:
            print(f'Exception pulling transactions {ex}')
        rh.remove_old_challenge()
        rh.logout()
        
        check_discrepancies()
    else:
        print('Unsupported broker')

@db_task()
def pull_share_trans_from_broker(user, broker, user_id, passwd, pass_2fa):
    print(f'user {user} broker {broker} userid {user_id}')
    if broker == 'ZERODHA':
        files = pull_zerodha(user_id, passwd, pass_2fa)
        for dload_file in files:
            add_share_transactions(broker, user, dload_file)
        check_discrepancies()
    else:
        print('Unsupported broker')

@db_task()
def pull_ppf_trans_from_bank(number, bank, user_id, passwd):
    print(f'number {number} bank {bank} userid {user_id}')
    if bank == 'SBI':
        from ppf.ppf_sbi_pull import pull_transactions
        trans = pull_transactions(user_id, passwd, number)
        print(trans)
        add_transactions_sbi_ppf(number, trans)
    else:
        print(f'unsupported bank {bank}')

@db_task()
def pull_ssy_trans_from_bank(number, bank, user_id, passwd):
    print(f'number {number} bank {bank} userid {user_id}')
    if bank == 'SBI':
        from ssy.ssy_helper import pull_transactions
        trans = pull_transactions(user_id, passwd, number)
        print(trans)
        add_transactions_sbi_ssy(number, trans)
    else:
        print(f'unsupported bank {bank}')

@db_task()
def add_share_transactions(broker, user, full_file_path):
    shares_add_transactions(broker, user, full_file_path)
    os.remove(full_file_path)

@db_periodic_task(crontab(minute='*/20'))
def update_scroll_data():
    pref_obj = Preferences.get_solo()
    sel_indexes = list()
    if pref_obj.indexes_to_scroll:
        for index in pref_obj.indexes_to_scroll.split('|'):
            sel_indexes.append(index)

    nse = NSE(None)
    print('getting index list for nse')
    il = nse.get_index_list()
    if il:
        for item in il:
            print(f'getting data of index {item} from nse')
            data = nse.get_index_quote(item)
            if data:
                print(f"data {data}")
                scroll_item = None
                try:
                    scroll_item = ScrollData.objects.get(scrip=item)
                    if get_diff(float(scroll_item.val), data['lastPrice']) > 0.1:
                        print(f"NSE scroll_item.val {scroll_item.val} data['lastPrice'] {data['lastPrice']}")
                        scroll_item.last_updated = timezone.now()
                        scroll_item.val = data['lastPrice']
                        scroll_item.change = data['change']
                        if not scroll_item.change:
                            scroll_item.change = 0
                        scroll_item.percent = data['pChange']
                        if not scroll_item.percent:
                            scroll_item.percent = 0
                        scroll_item.save()
                except ScrollData.DoesNotExist:
                    scroll_item = ScrollData.objects.create(scrip=item,
                                                            last_updated = timezone.now(),
                                                            val = data['lastPrice'],
                                                            change = data['change'],
                                                            percent = data['pChange'])
                if len(sel_indexes) == 0 or item in sel_indexes:
                    if scroll_item.display != True:
                        scroll_item.display = True
                        scroll_item.save()
                else:
                    if scroll_item.display != False:
                        scroll_item.display = False
                        scroll_item.save()
            else:
                print(f'no data for NSE {item}')
    n = Nasdaq('', None)
    data = n.get_all_index()
    if data:
        print(f"data {data}")
        for k, v in data.items():
            if not v['last_updated']:
                print(f'last updated is none.  Not updating {v["name"]}')
                continue
            try:
                scroll_item = None
                try:
                    scroll_item = ScrollData.objects.get(scrip=v['name'])
                    if get_diff(float(scroll_item.val), float(v['lastPrice'])) > 0.1:
                        print(f"NASDAQ scroll_item.val {scroll_item.val} v['lastPrice'] {v['lastPrice']}")
                        if 'last_updated' in v and v['last_updated']:
                            scroll_item.last_updated = v['last_updated']
                        else:
                            scroll_item.last_updated = timezone.now()
                        scroll_item.val = v['lastPrice']
                        scroll_item.change = v['change']
                        scroll_item.percent = v['pChange']
                        scroll_item.save()
                except ScrollData.DoesNotExist:
                    scroll_item = ScrollData.objects.create(scrip=v['name'],
                                                            last_updated = v['last_updated'],
                                                            val = v['lastPrice'],
                                                            change = v['change'],
                                                            percent = v['pChange'])
                if len(sel_indexes) == 0 or v['name'] in sel_indexes:
                    if scroll_item.display != True:
                        scroll_item.display = True
                        scroll_item.save()
                else:
                    if scroll_item.display != False:
                        scroll_item.display = False
                        scroll_item.save()
            except Exception as ex:
                print(f'Exception {ex} adding index with content {v}')

@db_periodic_task(crontab(minute='10', hour='1-5', day='1-5'))
def get_pe():
    pref_obj = Preferences.get_solo()
    sel_indexes = list()
    if pref_obj.indexes_to_scroll:
            for index in pref_obj.indexes_to_scroll.split('|'):
                sel_indexes.append(index)
    nse = NSE(None)
    avail_indices = ["NIFTY 50","NIFTY NEXT 50","NIFTY100 LIQUID 15","NIFTY MIDCAP LIQUID 15","NIFTY 100","NIFTY 200","NIFTY 500","NIFTY500 MULTICAP 50:25:25","NIFTY MIDCAP 150","NIFTY MIDCAP 50","NIFTY FULL MIDCAP 100",
					"NIFTY MIDCAP 100","NIFTY SMALLCAP 250","NIFTY SMALLCAP 50","NIFTY FULL SMALLCAP 100", "NIFTY SMALLCAP 100", "NIFTY LargeMidcap 250", "NIFTY MIDSMALLCAP 400",
                    "NIFTY AUTO","NIFTY BANK","NIFTY CONSUMER DURABLES","NIFTY FINANCIAL SERVICES","NIFTY FINANCIAL SERVICES 25/50","NIFTY FMCG","Nifty Healthcare Index","NIFTY IT","NIFTY MEDIA","NIFTY METAL",
			        "NIFTY OIL &amp; GAS","NIFTY PHARMA","NIFTY PRIVATE BANK","NIFTY PSU BANK","NIFTY TATA GROUP 25% CAP", "NIFTY100 LIQUID 15",
			        "NIFTY REALTY", "NIFTY COMMODITIES", "Nifty INDIA CONSUMPTION", "NIFTY CPSE",  "NIFTY ENERGY",  "NIFTY100 ESG",  "NIFTY100 Enhanced ESG", "NIFTY100 ESG SECTOR LEADERS", "NIFTY INFRASTRUCTURE",
	                "NIFTY MNC", "NIFTY PSE", "NIFTY SME EMERGE", "NIFTY SERVICES SECTOR", "NIFTY SHARIAH 25", "NIFTY50 SHARIAH", "NIFTY500 SHARIAH", "NIFTY ADITYA BIRLA GROUP", "NIFTY MAHINDRA GROUP", "NIFTY TATA GROUP",
                    "NIFTY MIDCAP LIQUID 15",	"NIFTY500 VALUE 50", "NIFTY MIDCAP150 QUALITY 50", "NIFTY ALPHA LOW-VOLATILITY 30", "NIFTY QUALITY LOW-VOLATILITY 30", "NIFTY ALPHA QUALITY LOW-VOLATILITY 30",	
                    "NIFTY ALPHA QUALITY VALUE LOW-VOLATILITY 30", "NIFTY50 Equal Weight", "NIFTY100 Equal Weight", "NIFTY100 LOW VOLATILITY 30", "NIFTY200 MOMENTUM 30", "NIFTY ALPHA 50",
		            "NIFTY DIVIDEND OPPORTUNITIES 50", "NIFTY HIGH BETA 50","NIFTY LOW VOLATILITY 50","NIFTY100 QUALITY 30","NIFTY50 VALUE 20",	"NIFTY GROWTH SECTORS 15"]
    il = nse.get_index_list()
    if not il:
        return
    for item in il:
        if item in sel_indexes and item in avail_indices:
            fp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            pe_file = os.path.join(fp, 'media', 'pe-ratio', item+'.json')
            print(f'opening file {pe_file}')
            if not os.path.exists(pe_file):
                f = open(pe_file, "w")
                f.close()
            data = dict()
            pe_start = datetime.date(year=1999, month=1, day=1)
            with open(pe_file) as f:
                try:
                    data = json.load(f)
                    for k,_ in data.items():
                        k_date = get_date_or_none_from_string(k,'%d-%b-%Y')
                        if k_date > pe_start:
                            pe_start = k_date
                except JSONDecodeError:
                    pass
            while pe_start < datetime.date.today():
                collect_end_date = pe_start+relativedelta(months=3) + relativedelta(days=-1)
                if collect_end_date >= datetime.date.today():
                    collect_end_date = datetime.date.today() + relativedelta(days=-1)
                url = 'https://www1.nseindia.com/products/dynaContent/equities/indices/historical_pepb.jsp?indexName=' + item.replace(' ', '%20')
                url += '&fromDate=' + convert_date_to_string(pe_start, '%d-%m-%Y') + '&toDate=' + convert_date_to_string(collect_end_date, '%d-%m-%Y')
                url += '&yield1=pe&yield2=pb&yield3=dy&yield4=all'
                print(f'getting url {url}')

                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Host': 'www1.nseindia.com',
                    'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
                }
                page = requests.get(url, headers=headers, timeout=10)
                if not page or page.status_code != 200:
                    break
                print('finished get')
                soup = BeautifulSoup(page.text, 'html.parser')
                print('finished souping')
                pe_start = collect_end_date+ relativedelta(days=1)
                table = soup.find('table')
                if not table:
                    print('no table. continuing')
                    continue
                print('found table')

                table_body = table.find('tbody')
                if not table_body:
                    print('no table body. continuing')
                    continue
                print('found table body')
                rows = table_body.find_all('tr')
                if not rows:
                    print('no row. continuing')
                    continue
                print('found rows')
                row_count = 0
                for row in rows:
                    print('in a row')
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]

                    print(cols)
                    if row_count > 2:
                        data[cols[0]] = dict()
                        data[cols[0]]['p/e'] = get_float_or_none_from_string(cols[1])
                        data[cols[0]]['p/b'] = get_float_or_none_from_string(cols[2])
                        data[cols[0]]['div yield'] = get_float_or_none_from_string(cols[3])
                    row_count = row_count+1
                
            with open(pe_file, 'w') as outfile:
                json.dump(data, outfile)

@db_periodic_task(crontab(minute='10', hour='1-5', day='1-5'))
def update_pe():
    pref_obj = Preferences.get_solo()
    sel_indexes = list()
    if pref_obj.indexes_to_scroll:
        for index in pref_obj.indexes_to_scroll.split('|'):
            sel_indexes.append(index)
        for index in sel_indexes:
            fp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            pe_file = os.path.join(fp, 'media', 'pe-ratio', index+'.json')
            print(f'opening file {pe_file}')
            if not os.path.exists(pe_file):
                print(f'file not found {pe_file}')
                continue
            yearly_pe_vals = dict()
            yearly_pb_vals = dict()

            with open(pe_file) as f:
                try:
                    data = json.load(f)
                    for k,v in data.items():
                        if v['p/e']:
                            k_date = get_date_or_none_from_string(k,'%d-%b-%Y')
                            if k_date.year not in yearly_pe_vals:
                                yearly_pe_vals[k_date.year] = dict()
                            if k_date.month not in yearly_pe_vals[k_date.year]:
                                yearly_pe_vals[k_date.year][k_date.month] = {'min':v['p/e'], 'max':v['p/e'], 'total':v['p/e'], 'num':1}
                            else:
                                if v['p/e'] < yearly_pe_vals[k_date.year][k_date.month]['min']:
                                    yearly_pe_vals[k_date.year][k_date.month]['min'] = v['p/e']
                                if v['p/e'] > yearly_pe_vals[k_date.year][k_date.month]['max']:
                                    yearly_pe_vals[k_date.year][k_date.month]['max'] = v['p/e']
                                yearly_pe_vals[k_date.year][k_date.month]['num'] = yearly_pe_vals[k_date.year][k_date.month]['num'] + 1
                                yearly_pe_vals[k_date.year][k_date.month]['total'] = yearly_pe_vals[k_date.year][k_date.month]['total'] + v['p/e']
                        if v['p/b']:
                            k_date = get_date_or_none_from_string(k,'%d-%b-%Y')
                            if k_date.year not in yearly_pb_vals:
                                yearly_pb_vals[k_date.year] = dict()
                            if k_date.month not in yearly_pb_vals[k_date.year]:
                                yearly_pb_vals[k_date.year][k_date.month] = {'min':v['p/b'], 'max':v['p/b'], 'total':v['p/b'], 'num':1}
                            else:
                                if v['p/b'] < yearly_pb_vals[k_date.year][k_date.month]['min']:
                                    yearly_pb_vals[k_date.year][k_date.month]['min'] = v['p/b']
                                if v['p/b'] > yearly_pb_vals[k_date.year][k_date.month]['max']:
                                    yearly_pb_vals[k_date.year][k_date.month]['max'] = v['p/b']
                                yearly_pb_vals[k_date.year][k_date.month]['num'] = yearly_pb_vals[k_date.year][k_date.month]['num'] + 1
                                yearly_pb_vals[k_date.year][k_date.month]['total'] = yearly_pb_vals[k_date.year][k_date.month]['total'] + v['p/b']
                        
                except Exception as ex:
                    print('exception during updating pe')
                    print(ex)
            print(yearly_pe_vals)
            for year, val in yearly_pe_vals.items():
                for k,v in val.items():
                    try:
                        PEMonthy.objects.create(
                            index_name=index,
                            month=k,
                            year=year,
                            pe_max=v['max'],
                            pe_min=v['min'],
                            pe_avg=v['total']/v['num']
                        )
                    except IntegrityError:
                        pass
            print(yearly_pb_vals)
            for year, val in yearly_pb_vals.items():
                for k,v in val.items():
                    try:
                        PBMonthy.objects.create(
                            index_name=index,
                            month=k,
                            year=year,
                            pb_max=v['max'],
                            pb_min=v['min'],
                            pb_avg=v['total']/v['num']
                        )
                    except IntegrityError:
                        pass

@db_periodic_task(crontab(minute='10', hour='1-12', day='10-15'))
def update_latest_vals_epf_ssy_ppf():
    from epf.epf_helper import update_epf_vals
    from ppf.ppf_helper import update_ppf_vals
    from ssy.ssy_helper import update_ssy_vals
    set_task_state('update_latest_vals_epf_ssy_ppf', TaskState.Running)

    update_epf_vals()
    update_ssy_vals()
    update_ppf_vals()
    set_task_state('update_latest_vals_epf_ssy_ppf', TaskState.Successful)

@db_periodic_task(crontab(minute='30', hour='*/6'))
def poll_market_news():
    from markets.markets_helper import get_news
    get_news()

@db_periodic_task(crontab(minute='30', hour='*/4', day='1-10'))
def pull_corporate_actions_shares():
    from shares.shares_helper import pull_and_store_corporate_actions
    pull_and_store_corporate_actions()

@db_task()
def update_401k_month_end_vals():
    from retirement_401k.helper import reconcile_401k
    reconcile_401k()

@db_periodic_task(crontab(minute='20', hour='*/6'))
def check_updates_pending():
    day = datetime.date.today().day
    if day in [1,2,3,4,5]:
        update_401k_month_end_vals()


'''
#  example code below

def tprint(s, c=32):
    # Helper to print messages from within tasks using color, to make them
    # stand out in examples.
    print('\x1b[1;%sm%s\x1b[0m' % (c, s))


# Tasks used in examples.

@task()
def add(a, b):
    return a + b


@task()
def mul(a, b):
    return a * b


@db_task()  # Opens DB connection for duration of task.
def slow(n):
    tprint('going to sleep for %s seconds' % n)
    time.sleep(n)
    tprint('finished sleeping for %s seconds' % n)
    return n


@task(retries=1, retry_delay=5, context=True)
def flaky_task(task=None):
    if task is not None and task.retries == 0:
        tprint('flaky task succeeded on retry.')
        return 'succeeded on retry.'
    tprint('flaky task is about to raise an exception.', 31)
    raise Exception('flaky task failed!')


# Periodic tasks.

@periodic_task(crontab(minute='*/2'))
def every_other_minute():
    tprint('This task runs every 2 minutes.', 35)


@periodic_task(crontab(minute='*/5'))
def every_five_mins():
    tprint('This task runs every 5 minutes.', 34)

'''