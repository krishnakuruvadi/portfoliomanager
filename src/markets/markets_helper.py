from django.db.utils import IntegrityError
from shares.shares_helper import get_invested_shares
from .mc_news import MoneyControlNews
import datetime
from .models import News, IndexRollingReturns, IndexYearlyReturns, IndexQuarterlyReturns, IndexMonthlyReturns

def get_news():
    total_results = 0
    for ish in get_invested_shares():
        print(f"getting news for {ish['exchange']} {ish['symbol']}")
        count = 0
        if ish['exchange'] in ['NSE', 'BSE', 'NSE/BSE']:
            if ish['exchange'] == 'NSE/BSE' or ish['exchange'] == 'NSE':
                mc = MoneyControlNews('NSE/BSE', ish['symbol'])
            else:
                mc = MoneyControlNews(ish['exchange'], ish['symbol'])
            try:
                results = mc.fetch_ticker_news()
                if results:
                    for res in results:
                        if ((datetime.date.today() - res['date']).days < 30):
                            try:
                                News.objects.create(
                                    exchange=ish['exchange'],
                                    symbol=ish['symbol'],
                                    text=res['text'],
                                    date=res['date'],
                                    link=res['link'],
                                    source='moneycontrol'
                                )
                            except IntegrityError:
                                print('news exists')
                            count += 1
                            total_results += 1
                            if count > 5:
                                break
                        else:
                            print(f'stale news from {res["date"]}')
            except Exception as ex:
                print(f"Exception {ex} while getting news from MC for {ish['exchange']} {ish['symbol']}")

def update_india_market_returns(input):
    if 'as_on' in input:
        if type(input['as_on']) == datetime.datetime:
            input['as_on'] = input['as_on'].date()
    if 'trailing_ret' in input:
        for ret in input['trailing_ret']:
            try:
                r = IndexRollingReturns.objects.get(country='India', name=ret['name'])
                r.return_1d=ret['1D']
                r.return_1w=ret['1W']
                r.return_1m=ret['1M']
                r.return_3m=ret['3M']
                r.return_6m=ret['6M']
                r.return_1y=ret['1Y']
                r.return_3y=ret['3Y']
                r.return_5y=ret['5Y']
                r.return_10y=ret['10Y']
                r.return_15y=ret['15Y']
                r.return_incep=ret['inception']
                r.return_ytd=ret['YTD']
                r.as_on_date=input['as_on']
                r.save()
            
            except IndexRollingReturns.DoesNotExist:
                IndexRollingReturns.objects.create(
                    country='India',
                    name=ret['name'],
                    return_1d=ret['1D'],
                    return_1w=ret['1W'],
                    return_1m=ret['1M'],
                    return_3m=ret['3M'],
                    return_6m=ret['6M'],
                    return_1y=ret['1Y'],
                    return_3y=ret['3Y'],
                    return_5y=ret['5Y'],
                    return_10y=ret['10Y'],
                    return_15y=ret['15Y'],
                    return_incep=ret['inception'],
                    return_ytd=ret['YTD'],
                    as_on_date=input['as_on']
                )
            except Exception as ex:
                print(f'Exception when updating trailing_ret: {ex}')
    if 'yearly_ret' in input:
        for yr in input['yearly_ret']:
            for k,v in yr.items():
                if k == 'name':
                    continue
                try:
                    IndexYearlyReturns.objects.create(
                        country='India',
                        name=yr['name'],
                        year=k,
                        ret=v,
                        as_on_date=input['as_on']
                    )
                except IntegrityError:
                    pass
                except Exception as ex:
                    print(f'Exception when updating yearly_ret: {ex}')

    if 'quarterly_ret' in input:
        for qtr in input['quarterly_ret']:
            for k,v in qtr.items():
                if k == 'name':
                    continue
                try:
                    IndexQuarterlyReturns.objects.create(
                        country='India',
                        name=qtr['name'],
                        quarter=k,
                        ret=v,
                        as_on_date=input['as_on']
                    )
                except IntegrityError:
                    pass
                except Exception as ex:
                    print(f'Exception when updating quarterly_ret: {ex}')

    if 'monthly_ret' in input:
        for month in input['monthly_ret']:
            for k,v in month.items():
                if k == 'name':
                    continue
                try:
                    IndexMonthlyReturns.objects.create(
                        country='India',
                        name=month['name'],
                        month=k,
                        ret=v,
                        as_on_date=input['as_on']
                    )
                except IntegrityError:
                    pass
                except Exception as ex:
                    print(f'Exception when updating monthly_ret: {ex}')
