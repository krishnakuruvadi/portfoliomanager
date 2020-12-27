from huey.contrib.djhuey import task, periodic_task, db_task, db_periodic_task
from huey import crontab
from mutualfunds.models import Folio, MutualFundTransaction
from common.models import MutualFund, HistoricalMFPrice
from espp.models import Espp
from espp.espp_helper import update_latest_vals
from shared.handle_real_time_data import get_historical_year_mf_vals
from dateutil.relativedelta import relativedelta
import datetime
import time
from django.db.models import Q
from mftool import Mftool
from common.helper import update_mf_scheme_codes
from shared.utils import get_float_or_zero_from_string
from common.bsestar import download_bsestar_schemes

@db_periodic_task(crontab(minute='0', hour='*/12'))
def get_mf_navs():
    print('inside get_mf_navs')
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

@db_periodic_task(crontab(minute='35', hour='*/12'))
def update_mf():
    print('Updating Mutual Fund with latest nav')
    folios = Folio.objects.all()
    finished_funds = dict()
    mf = Mftool()
    for folio in folios:
        if not folio.units:
            continue
        if folio.fund.code not in finished_funds:
            print('trying folio', folio.folio, folio.fund.code)
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
            folio.as_on_date =  datetime.datetime.strptime(finished_funds[folio.fund.code]['as_on'], '%d-%b-%Y')
            folio.save()

@periodic_task(crontab(minute='0', hour='*/2'))
def update_espp():
    print('Updating ESPP')
    for espp_obj in Espp.objects.all():
        print("looping through espp " + str(espp_obj.id))
        update_latest_vals(espp_obj)

@periodic_task(crontab(minute='0', hour='10'))
def update_mf_schemes():
    print('Updating Mutual Fund Schemes')
    update_mf_scheme_codes()

@periodic_task(crontab(minute='45', hour='*/12'))
def update_bse_star_schemes():
    print('Updating BSE STaR Schemes')
    download_bsestar_schemes()
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