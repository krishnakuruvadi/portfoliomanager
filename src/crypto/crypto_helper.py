from .models import Crypto, Transaction

from django.db import IntegrityError
from alerts.alert_helper import create_alert, Severity
from shared.handle_get import get_user_name_from_id
import requests
import json
from enum import IntEnum
from shared.handle_real_time_data import get_in_preferred_currency
import datetime
from shared.financial import xirr
import os
from dateutil.relativedelta import relativedelta
from django.conf import settings


def insert_trans_entry(symbol, user, trans_type, quantity, price, date, notes, broker, conversion_rate=1, fees=0, currency='USD', trans_price=None):
    try:
        co = None
        try:
            co = Crypto.objects.get(symbol=symbol, user=user)
        except Crypto.DoesNotExist:
            print(f'creating crypto object {symbol} for user {user}')
            co = Crypto.objects.create(symbol=symbol,
                                        user=user,
                                        units=0,
                                        buy_price=0,
                                        buy_value=0,
                                        unrealised_gain=0,
                                        realised_gain=0
                                    )
        if not trans_price:
            trans_price = price*quantity*conversion_rate
        try:
            Transaction.objects.create(crypto=co,
                                        trans_date=date,
                                        trans_type=trans_type,
                                        price=price,
                                        units=quantity,
                                        conversion_rate=conversion_rate,
                                        trans_price=trans_price,
                                        broker=broker,
                                        notes=notes,
                                        fees=fees,
                                        buy_currency=currency)
        except IntegrityError:
            print('Transaction exists')
    except Exception as ex:
        print(f'failed to add transaction {symbol}, {user}, {trans_type}, {quantity}, {price}, {date}, {notes}, {broker}')
        print(ex)
        description = 'failed to add transaction for :' + symbol + ' for user ' + get_user_name_from_id(user)
        create_alert(
            summary=symbol + ' - Failed to add transaction',
            content=description,
            severity=Severity.warning,
            alert_type="Action"
        )


def update_crypto_user(symbol, user):
    latest_prices = dict()
    if symbol:
        try:
            co = Crypto.objects.get(symbol=symbol, user=user)
            update_crypto(co, latest_prices)
        except Crypto.DoesNotExist:
            print(f'crypto object {symbol} for user {user} not found')
    else:
        try:
            for co in Crypto.objects.filter(user=user):
                update_crypto(co, latest_prices)
        except Crypto.DoesNotExist:
            print(f'crypto object {symbol} for user {user} not found')
                
def update_crypto_all():
    latest_prices = dict()
    for co in Crypto.objects.all():
        update_crypto(co, latest_prices)


class EventType(IntEnum):
    SPLIT = 1
    BONUS = 2
    BUY = 3
    SELL = 4

class Event:
    def __init__(self, event_type, dt):
        self.event_type = event_type
        self.dt = dt
        self.qty = 0
        self.old_fv = 0
        self.new_fv = 0
        self.ratio_num = 0
        self.ratio_denom = 0
        self.price = 0

    def setQty(self, qty):
        self.qty = qty
    
    def setPrice(self, price):
        self.price = price

    def __str__(self) -> str:
        if self.event_type == EventType.BUY:
            return self.dt.strftime('%d-%m-%Y') + ':  Buy ' + str(self.qty) + ' totalling ' + str(self.price)
        if self.event_type == EventType.SELL:
            return self.dt.strftime('%d-%m-%Y') + ':  Sell ' + str(self.qty) + ' totalling ' + str(self.price)
        return self.dt + self.event_type

class Deal:
    def __init__(self, in_dt, qty, price):
        self.qty = qty
        self.price = price
        self.unsold = True
        self.in_dt = in_dt
        self.out_dt = None
        self.profit = None
        self.sell_price = None

    def can_sell(self):
        return self.unsold

    def sell(self, sell_dt, sell_qty, sell_price):
        new_qty = 0
        if sell_qty == 0:
            return 0, None
        if not self.unsold:
            return sell_qty, None
        self.unsold = False
        self.sell_price = sell_price
        self.out_dt = sell_dt
        if sell_qty > self.qty:
            self.profit =  self.qty*sell_price - self.qty*self.price
            return sell_qty - self.qty, None
        elif sell_qty < self.qty:
            new_qty = self.qty - sell_qty
            self.qty = sell_qty
            self.profit =  self.qty*sell_price - self.qty*self.price
            return 0, Deal(self.in_dt, new_qty, self.price)
        
        self.profit =  self.qty*sell_price - self.qty*self.price
        return 0, None
    

    def __str__(self) -> str:
        ret = f"Buy {str(self.qty)} on {self.in_dt.strftime('%d-%m-%Y')} at {self.price} for {self.qty*self.price}"
        if not self.unsold:
            ret = ret + f". Sell on {self.out_dt.strftime('%d-%m-%Y')} at {self.sell_price} for a "
            if self.profit >= 0:
                ret = ret + 'profit of '
            else:
                ret = ret + 'loss of '
            ret = ret + str(self.profit)
        return ret

def reconcile_event_based(transactions, round_qty_to_int=False, latest_price=None, latest_conversion_rate=1):
    event_list = list()
    buy_value = 0
    buy_price = 0
    for trans in transactions:
        trans_type = trans.trans_type
        if type(trans.trans_type) is str:
            trans_type = EventType.BUY if trans.trans_type == 'Buy' or trans.trans_type == 'Receive' else EventType.SELL
        e = Event(trans_type, trans.trans_date)
        e.setQty(trans.units)
        e.setPrice(trans.price)
        event_list.append(e)
    event_list.sort(key=lambda x: (x.dt,x.event_type), reverse=False)

    print('sorted events:')
    deals = list()
    for event in event_list:
        print(event)
        if event.event_type  == EventType.BUY:
            deals.append(Deal(event.dt, event.qty, event.price))
            deals.sort(key=lambda x: x.in_dt, reverse=False)
        elif event.event_type == EventType.SELL:
            qty = event.qty
            for deal in deals:
                qty, new_deal = deal.sell(event.dt, qty, event.price)
                if new_deal:
                    deals.append(new_deal)
                    deals.sort(key=lambda x: x.in_dt, reverse=False)
    realised_gain = 0
    qty = 0
    unrealised_gain = 0
    current_buy = 0
    for deal in deals:
        print(f'\t {deal}')
        if deal.profit:
            realised_gain += deal.profit
        if deal.can_sell():
            qty += deal.qty
            current_buy += deal.price*deal.qty
    if qty > 0 and latest_price:
        unrealised_gain = ((float(qty) * float(latest_price)) - float(current_buy))* float(latest_conversion_rate)
        buy_price = float(current_buy)/float(qty)
        buy_value = float(qty) * buy_price * float(latest_conversion_rate)
        #buy_price = buy_price/float(latest_conversion_rate)
        
    print(f'buy_value: {buy_value}, quantity: {qty}, realised gain: {realised_gain}, unrealised gain: {unrealised_gain}')
    return qty, buy_value, buy_price, realised_gain, unrealised_gain

def update_crypto(co, latest_prices=None):
    latest_price = None
    latest_time = None
    if latest_prices:
        if co.symbol in latest_prices:
            latest_price = latest_prices.get(co.symbol)['price']
            latest_time = latest_prices.get(co.symbol)['time']
    if not latest_price:
        latest_price, latest_time = get_price(co.symbol)

    if latest_price:
        latest_prices[co.symbol] = {'price': latest_price, 'time': latest_time}
        conv_rate = get_in_preferred_currency(1.0, 'USD', datetime.date.today())
        transactions = Transaction.objects.filter(crypto=co).order_by('trans_date')
        qty, buy_value, buy_price, realised_gain, unrealised_gain = reconcile_event_based(transactions,False,latest_price,conv_rate)
        print(f'qty {qty}, buy_value {buy_value}, buy_price {buy_price}, realised_gain {realised_gain}, unrealised_gain {unrealised_gain} in update_crypto')
        co.latest_value = float(latest_price) * float(qty) * float(conv_rate)
        co.buy_price = buy_price
        co.buy_value = buy_value
        co.realised_gain = realised_gain
        co.unrealised_gain = unrealised_gain
        co.units = qty
        co.latest_price = latest_price
        co.as_on_date = latest_time
        cash_flows = list()
        for t in transactions:
            if t.trans_type == 'Buy':
                cash_flows.append((t.trans_date, -1*float(t.trans_price)))
            else:
                cash_flows.append((t.trans_date, float(t.trans_price)))
        co.save()
        if qty > 0:
            cash_flows.append((datetime.date.today(), float(co.latest_value)))
        try:
            roi = xirr(cash_flows, 0.1)*100
            roi = round(roi, 2)
            co.xirr = roi
        except Exception as ex:
            print(f'exception finding xirr {ex}')  
            co.xirr = 0     
    co.save()


def get_price(symbol):
    versus = "usd"
    try:
        coin_id = symbol_to_id(symbol)
        # ex: https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=USD&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true 
        coingecko_price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={versus}&include_market_cap" \
                            "=true&include_24hr_vol=true&include_24hr_change=true&include_last_updated_at=true"

        price_request = json.loads(requests.get(url=coingecko_price_url).text)
        price_output = price_request[coin_id]
        price = price_output["usd"]
        print(price_output)
    except Exception as ex:
        print(f'exception getting latest price {symbol} {ex}')
        return None, None
    '''
    markup = symbol.title() + " - " + symbol_to_name(
        symbol) + "\n" + "Price: " + price + "\n" + "24h Change: " + str(usd_24h_change) + "\n" + "Market Cap: " + str(
        usd_market_cap2) + "\n24h Volume: " + str(usd_24h_vol)
    return markup
    '''
    return price, datetime.datetime.fromtimestamp(price_output['last_updated_at'])

def get_crypto_coins():
    url = 'https://api.coingecko.com/api/v3/coins/list'
    print(f'fetching from url {url}')
    r = requests.get(url, timeout=15)
    coins = list()
    if r.status_code == 200:
        for entry in r.json():
            coins.append(entry['symbol'])
    else:
        coins.append('btc')
        coins.append('btcb')
    return coins

def symbol_to_id(symbol):
    coin_id = None
    fp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mapping_file = os.path.join(fp, 'media', 'crypto_mapping.json')
    if os.path.exists(mapping_file):
        with open(mapping_file) as f:
            data = json.load(f)
            for item in data:
                if item['symbol'] == symbol:
                    return item['id']
    try:  # based on API some keys are lower case and some are upper, so handle this with try and except to resolve
        # KeyError
        cleaned_symbol = str(symbol).strip().lower()
        headers = {'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
            'X-Requested-With': 'XMLHttpRequest'
            }
        symbol_url = "https://api.coingecko.com/api/v3/coins/list?include_platform=true"
        response = requests.get(symbol_url, headers=headers, timeout=15)
        response.raise_for_status()  # raises exception when not a 2xx response
        if response.status_code != 204:
            id_request = response.json()
        else:
            id_request = json.loads(response.text)
        with open(mapping_file, "w") as f:
            json.dump(id_request, f)
        find = {y["symbol"]: x for x, y in list(enumerate(id_request))}
        location = find[cleaned_symbol]

        coin_id = id_request[location]["id"]
        print("id lower", coin_id)

        return coin_id
    except Exception as ex:
        print(f'exception while accessing {symbol_url} {ex}.  Trying alternate url')
        try:
            cleaned_symbol = str(symbol).strip().upper()
            symbol_url = "https://api.coingecko.com/api/v3/coins/list?include_platform=true"
            id_request = json.loads(requests.get(url=symbol_url).text)
            find = {y["symbol"]: x for x, y in list(enumerate(id_request))}
            location = find[cleaned_symbol]

            coin_id = id_request[location]["id"]
            print("id upper", coin_id)
        except Exception as ex:
            print(f'exception while accessing alternate url too {symbol_url} {ex}.')
        return coin_id

def get_historical_price(symbol, date):
    coin_id = symbol_to_id(symbol)
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={date.strftime('%d-%m-%Y')}"

    try:
        price_request = json.loads(requests.get(url=url).text)
        print(price_request)
        price_output = price_request['market_data']['current_price']
        price = price_output["usd"]
        
        return price
    except Exception as ex:
        print(f'exception {ex} while getting historical price for {symbol} on {date} using url {url}')
    return None

def store_returns():
    path = os.path.join(settings.MEDIA_ROOT, "crypto")
    if not os.path.exists(path):
        os.makedirs(path)

    today = datetime.date.today()
    yesterday = today+relativedelta(days=-1)
    returns_file = os.path.join(path, 'crypto_returns.json')
    if os.path.exists(returns_file):
        with open(returns_file) as f:
            data = json.load(f)
            if data['last_updated'] == today.strftime('%d-%b-%Y') or data['reference_dt'] == yesterday.strftime('%d-%b-%Y'):
                return
    
    top_crypto = ['btc', 'eth', 'ltc', 'xrp', 'usdc', 'usdt', 'doge', 'shib', 'bnb', 'bch']
    res = dict()
    res['returns'] = list()
    for symbol in top_crypto:
        
        yprice = get_historical_price(symbol, yesterday)
        ret = {
            'symbol':symbol
        }
        try:
            dbprice = get_historical_price(symbol, yesterday+relativedelta(days=-1))
            c1d = ((yprice-dbprice)/dbprice)*100
            ret['1d'] = round(c1d, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')

        try:
            wbprice = get_historical_price(symbol, yesterday+relativedelta(days=-7))
            c1w = ((yprice-wbprice)/wbprice)*100
            ret['1w'] = round(c1w, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')

        try:
            mbprice = get_historical_price(symbol, yesterday+relativedelta(months=-1))
            c1m = ((yprice-mbprice)/mbprice)*100
            ret['1m'] = round(c1m, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')

        try:
            mb3price = get_historical_price(symbol, yesterday+relativedelta(months=-3))
            c3m = ((yprice-mb3price)/mb3price)*100
            ret['3m'] = round(c3m, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')
        
        try:
            mb6price = get_historical_price(symbol, yesterday+relativedelta(months=-6))
            c6m = ((yprice-mb6price)/mb6price)*100
            ret['6m'] = round(c6m, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')

        try:
            ytdprice = get_historical_price(symbol, datetime.date(day=1, month=1, year=today.year))
            cytd = ((yprice-ytdprice)/ytdprice)*100
            ret['ytd'] = round(cytd, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')

        try:
            ybprice = get_historical_price(symbol, yesterday+relativedelta(years=-1))
            c1y = ((yprice-ybprice)/ybprice)*100
            ret['1y'] = round(c1y, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')

        try:
            yb2price = get_historical_price(symbol, yesterday+relativedelta(years=-2))
            c2y = ((yprice-yb2price)/yb2price)*100
            ret['2y'] = round(c2y, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')

        try:
            yb3price = get_historical_price(symbol, yesterday+relativedelta(years=-3))
            c3y = ((yprice-yb3price)/yb3price)*100
            ret['3y'] = round(c3y, 2)
        except Exception as ex:
            print(f'exception getting price change {ex}')

        res['returns'].append(ret)
    res['reference_dt'] = yesterday.strftime('%d-%b-%Y')
    res['last_updated'] = today.strftime('%d-%b-%Y')
    with open(returns_file, "w") as f:
        json.dump(res, f)
