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
from shared.utils import get_float_or_zero_from_string, get_float_or_none_from_string, get_int_or_none_from_string
from common.bsestar import download_bsestar_schemes
from shared.handle_get import *
from shared.handle_chart_data import get_investment_data
from pages.models import InvestmentData
from mutualfunds.models import Folio, MutualFundTransaction
from mutualfunds.mf_helper import mf_add_transactions
import os
import json
from mutualfunds.mf_analyse import pull_ms, pull_category_returns, pull_blend
from django.db import IntegrityError
from goal.goal_helper import update_all_goals_contributions
from .models import Task, TaskState
from alerts.alert_helper import create_alert, Severity
from shares.pull_zerodha import pull_zerodha
from shares.shares_helper import shares_add_transactions, update_shares_latest_val
from shared.financial import xirr
from shared.nasdaq import Nasdaq
from django.utils import timezone

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
    set_task_state('clean_db', TaskState.Successful)

@task()
def add_mf_transactions(broker, user, full_file_path):
    set_task_state('add_mf_transactions', TaskState.Running)
    mf_add_transactions(broker, user, full_file_path)
    set_task_state('add_mf_transactions', TaskState.Successful)

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
    update_shares_latest_val()
    set_task_state('update_shares_latest_vals', TaskState.Successful)

@db_periodic_task(crontab(minute='35', hour='2'))
def analyse_mf():
    set_task_state('analyse_mf', TaskState.Running)
    ret = pull_category_returns()
    update_category_returns(ret)
    token = None
    folios = Folio.objects.all()
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
def pull_share_trans_from_broker(user, broker, user_id, passwd, pass_2fa):
    print(f'user {user} broker {broker} userid {user_id} password {passwd} 2fa {pass_2fa}')
    if broker == 'ZERODHA':
        files = pull_zerodha(user_id, passwd, pass_2fa)
        for dload_file in files:
            add_share_transactions(broker, user, dload_file)

@db_task()
def add_share_transactions(broker, user, full_file_path):
    shares_add_transactions(broker, user, full_file_path)
    os.remove(full_file_path)

@db_periodic_task(crontab(minute='*/10'))
def update_scroll_data():
    from nsetools import Nse
    from common.models import ScrollData, Preferences
    pref_obj = Preferences.get_solo()
    sel_indexes = list()
    if pref_obj.indexes_to_scroll:
        for index in pref_obj.indexes_to_scroll.split('|'):
            sel_indexes.append(index)

    nse = Nse()
    for item in nse.get_index_list():
        data = nse.get_index_quote(item)
        if data:
            #print(data)
            scroll_item = None
            try:
                scroll_item = ScrollData.objects.get(scrip=item)
                scroll_item.last_updated = timezone.now()
                scroll_item.val = data['lastPrice']
                scroll_item.change = data['change']
                scroll_item.percent = data['pChange']
            except ScrollData.DoesNotExist:
                scroll_item = ScrollData.objects.create(scrip=item,
                                                        last_updated = timezone.now(),
                                                        val = data['lastPrice'],
                                                        change = data['change'],
                                                        percent = data['pChange'])
            if len(sel_indexes) == 0 or item in sel_indexes:
                scroll_item.display = True
            else:
                scroll_item.display = False
            scroll_item.save()
    n = Nasdaq('')
    data = n.get_all_index()
    if data:
        for k, v in data.items():
            scroll_item = None
            try:
                scroll_item = ScrollData.objects.get(scrip=v['name'])
                scroll_item.last_updated = v['last_updated']
                scroll_item.val = v['lastPrice']
                scroll_item.change = v['change']
                scroll_item.percent = v['pChange']
            except ScrollData.DoesNotExist:
                scroll_item = ScrollData.objects.create(scrip=v['name'],
                                                        last_updated = v['last_updated'],
                                                        val = v['lastPrice'],
                                                        change = v['change'],
                                                        percent = v['pChange'])
            if len(sel_indexes) == 0 or v['name'] in sel_indexes:
                scroll_item.display = True
            else:
                scroll_item.display = False
            scroll_item.save()


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