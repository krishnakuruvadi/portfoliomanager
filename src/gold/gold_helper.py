from common.models import HistoricalGoldPrice
from dateutil.relativedelta import relativedelta
import requests
from shared.utils import get_date_or_none_from_string
from tools.gold_india import get_last_close_digital_gold_price, get_latest_physical_gold_price
import datetime
from django.db import IntegrityError
from .models import Gold, SellTransaction
from shared.financial import xirr


def get_historical_price(dt, buy_type, purity):
    st_dt = dt+relativedelta(days=-5)
    hgp = HistoricalGoldPrice.objects.filter(purity=purity, buy_type=buy_type, date__lte=dt, date__gte=st_dt).order_by('-date')
    if len(hgp) > 0:
        return float(hgp[0].price)
    else:
        print(f'no historical price for gold found in db for buy_type:{buy_type} purity:{purity} between {st_dt} and {dt}')

    url = f'https://raw.githubusercontent.com/krishnakuruvadi/portfoliomanager-data/main/India/gold/{dt.year}.json'
    print(f'fetching from url {url}')
    r = requests.get(url, timeout=15)
    val = None
    if r.status_code == 200:
        print(r.text)
        print(r.json())
        for dt_str, entry in r.json()['prices'].items():
            tempdt = get_date_or_none_from_string(dt_str, '%d/%m/%Y')
            if '24K' in entry:
                try:
                    HistoricalGoldPrice.objects.create(date=tempdt, purity='24K', buy_type='Physical', price=entry['24K'])
                except IntegrityError:
                    pass
                except Exception as ex:
                    print(f'{ex} when adding to HistoricalGoldPrice')
            if '22K' in entry:
                try:
                    HistoricalGoldPrice.objects.create(date=tempdt, purity='22K', buy_type='Physical', price=entry['22K'])
                except IntegrityError:
                    pass
                except Exception as ex:
                    print(f'{ex} when adding to HistoricalGoldPrice')
            if 'digital' in entry:
                try:
                    HistoricalGoldPrice.objects.create(date=tempdt, purity='24K', buy_type='Digital', price=entry['digital'])
                except IntegrityError:
                    pass
                except Exception as ex:
                    print(f'{ex} when adding to HistoricalGoldPrice')
            if tempdt and tempdt == dt:
                if buy_type == 'Digital':
                    val = entry.get('digital', None)
                else:
                    val = entry.get(purity, None)
    else:
        print(f'failed to get url {url} {r.status_code}')
    return val

def get_latest_price(buy_type, purity='24K'):
    latest_day = datetime.date.today() + relativedelta(days=-1)
    try:
        hgp = HistoricalGoldPrice.objects.get(purity=purity, buy_type=buy_type, date=latest_day)
        return float(hgp.price), hgp.date
    except HistoricalGoldPrice.DoesNotExist:
        print(f'latest price for {latest_day} {buy_type} {purity} not found')

    dt = None
    price = None
    if buy_type == 'Digital':
        dt, price = get_last_close_digital_gold_price()
        try:
            HistoricalGoldPrice.objects.create(date=dt, purity='24K', buy_type=buy_type, price=price)
        except IntegrityError as ie:
            print(f'error adding entry to gold {dt}, 24K, {buy_type} {price}: {ie}')
    else:
        res = get_latest_physical_gold_price()
        if res:
            print(res)
            dt = res['date']
            try:
                HistoricalGoldPrice.objects.create(date=dt, purity='24K', buy_type=buy_type, price=res['24K'])
                HistoricalGoldPrice.objects.create(date=dt, purity='22K', buy_type=buy_type, price=res['22K'])
            except IntegrityError as ie:
                print(f'error adding entry to gold {res}, {buy_type} : {ie}')
            price = res.get(purity, None)
    if dt and price:
        #print(f'returning {dt} {price} for gold {buy_type} {purity}')
        return price,dt
    print(f'not found any valid value for gold {buy_type} {purity}')
    return None, None

def update_latest_value(user):
    if not user:
        objs = Gold.objects.all()
    else:
        objs = Gold.objects.filter(user=user)
    for g in objs:
        cash_flows = list()
        cash_flows.append((g.buy_date, -1*float(g.buy_value)))
        lp,ld = get_latest_price(g.buy_type, g.purity)
        wt = float(g.weight)
        realised_gain = 0
        sold_wt = 0
        for st in SellTransaction.objects.filter(buy_trans=g):
            sold_wt += float(st.weight)
            realised_gain += float(st.weight) * (float(st.per_gm) - float(g.per_gm))
            cash_flows.append((st.trans_date, float(st.trans_amount)))
        unsold_wt = wt - sold_wt
        g.unsold_weight = unsold_wt
        g.realised_gain = realised_gain
        if ld and lp:
            g.unrealised_gain = (float(lp) - float(g.per_gm))* unsold_wt
            g.as_on_date = ld
            g.latest_value = float(lp) * unsold_wt
            g.latest_price = float(lp)
            if unsold_wt > 0:
                cash_flows.append((ld, float(g.latest_value)))
                x = xirr(cash_flows, 0.1)*100
                print(f'roi: {x}')
                g.roi = x        
        g.save()

'''
def add_broker_trans(broker, user, trans):
    if broker == 'kuvera':
        for tran in trans:
            if tran['type'].lower() == 'buy':
                try:
                    weight = tran['units']
                    Gold.objects.create(
                        user=user,
                        notes='KUVERA broker buy',
                        weight=weight,
                        per_gm=tran['NAV'],
                        buy_value=tran['amount'],
                        buy_date=tran['date'],
                        buy_type='Other',
                        unsold_weight=weight,
                        purity='24K'
                    )
                except IntegrityError as ie:
                    pass
        update_latest_value(user)
        notes = 'KUVERA broker sell'
        for tran in trans:
            if tran['type'].lower() != 'buy':
                weight = tran['units']
                per_gm = tran['NAV']
                trans_date = get_date_or_none_from_string(tran['date'])

                while weight > 0:
                    objs = Gold.objects.filter(user=user)
                    for g in objs:
                        if g.unsold_weight == 0:
                            continue
                        part_wt = weight
                        if weight > g.unsold_weight:
                            part_wt = g.unsold_weight
                        weight -= part_wt
                        sell_value = part_wt * per_gm
                        SellTransaction.objects.create(
                            buy_trans=g,
                            notes=notes,
                            weight=part_wt,
                            per_gm=per_gm,
                            trans_amount=sell_value,
                            trans_date=trans_date
                        )
                        update_latest_value(user)
'''