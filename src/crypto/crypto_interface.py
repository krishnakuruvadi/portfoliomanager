from .models import Crypto, Transaction
import datetime
from shared.handle_real_time_data import get_in_preferred_currency

class CryptoInterface:

    @classmethod
    def get_chart_name(self):
        return 'Crypto'

    @classmethod
    def get_chart_color(self):
        return "#000080"
        
    @classmethod
    def get_module_id(self):
        return 'id_crypto_module'

    @classmethod
    def get_export_name(self):
        return 'crypto'
    
    @classmethod
    def get_current_version(self):
        return 'v1'

    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Crypto.objects.filter(user=user_id)
            else:
                objs = Crypto.objects.all()
            
            for obj in objs:
                crypto_trans = Transaction.objects.filter(crypto=obj)
                for trans in crypto_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for crypto {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Crypto.objects.filter(goal=goal_id)
            for obj in objs:
                crypto_trans = Transaction.objects.filter(crypto=obj)
                for trans in crypto_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} crypto {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = Crypto.objects.filter(user=user_id)
            for obj in objs:
                crypto_trans = Transaction.objects.filter(crypto=obj)
                for trans in crypto_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} crypto {ex}')
        return start_day
    
    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Crypto.objects.filter(user=user_id)
        else:
            objs = Crypto.objects.all()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.latest_value else obj.latest_value
        return amt

    @classmethod
    def get_amount_for_goal(self, goal_id):
        amt = 0
        objs = Crypto.objects.filter(goal=goal_id)
        for obj in objs:
            amt += 0 if not obj.latest_value else obj.latest_value
        return amt

    @classmethod
    def get_amount_for_user(self, user_id):
        objs = Crypto.objects.filter(user=user_id)
        total = 0
        for obj in objs:
            if obj.latest_value:
                total += obj.latest_value
        return total
    
    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt
    
    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for obj in Crypto.objects.filter(user=user_id):
            transactions = Transaction.objects.filter(crypto=obj, trans_date__gte=st_date, trans_date__lte=end_date)
            for t in transactions:
                if t.trans_type == 'Buy' or t.trans_type == 'Receive':
                    contrib += float(t.trans_price)
                else:
                    deduct += -1*float(t.trans_price)
        return contrib, deduct

    @classmethod
    def get_user_monthly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        contrib = [0]*12
        deduct = [0]*12
        for obj in Crypto.objects.filter(user=user_id):
            transactions = Transaction.objects.filter(crypto=obj, trans_date__gte=st_date, trans_date__lte=end_date)
            for t in transactions:
                if t.trans_type == 'Buy' or t.trans_type == 'Receive':
                    contrib[t.trans_date.month-1] += float(t.trans_price)
                else:
                    deduct[t.trans_date.month-1] += -1*float(t.trans_price)
        return contrib, deduct
    
    @classmethod
    def get_goal_yearly_contrib(self, goal_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        if end_date > datetime.date.today():
            end_date = datetime.date.today()
        contrib = 0
        deduct = 0
        total = 0
        cash_flows = list()
        
        for cobj in Crypto.objects.filter(goal=goal_id):
            tu = 0
            for t in Transaction.objects.filter(crypto=cobj, trans_date__lte=end_date).order_by('trans_date'):
                if t.trans_date >= st_date:
                    if t.trans_type == 'Buy' or t.trans_type == 'Receive':
                        contrib += float(t.trans_price)
                        cash_flows.append((t.trans_date, -1*float(t.trans_price)))
                        tu += t.units
                    else:
                        cash_flows.append((t.trans_date, float(t.trans_price)))
                        deduct += -1*float(t.trans_price)
                        tu -= t.units
                else:
                    if t.trans_type == 'Buy' or t.trans_type == 'Receive':
                        tu += t.units
                    else:
                        tu -= t.units
            if tu > 0:
                from common.models import Coin, HistoricalCoinPrice
                try:
                    coin = Coin.objects.get(symbol=cobj.symbol)
                    try:
                        hcp = HistoricalCoinPrice.objects.get(coin=coin, date=end_date)
                        total += float(hcp.price)*float(tu)*float(get_in_preferred_currency(1, 'USD'))
                    except HistoricalCoinPrice.DoesNotExist:
                        from tasks.tasks import pull_and_store_coin_historical_vals
                        pull_and_store_coin_historical_vals(cobj.symbol, end_date)
                except Coin.DoesNotExist:
                    print(f'coin not tracked for historical prices {cobj.symbol}')
        return cash_flows, contrib, deduct, total

    @classmethod
    def get_value_as_on(self, end_date):
        from .crypto_helper import reconcile_event_based
        from common.models import Coin, HistoricalCoinPrice
        from tasks.tasks import pull_and_store_coin_historical_vals
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        amt = 0
        for crypto in Crypto.objects.filter():
            transactions = Transaction.objects.filter(crypto=crypto, trans_date__lte=end_date)
            qty, buy_value, buy_price, realised_gain, unrealised_gain = reconcile_event_based(transactions)
            if qty > 0:
                try:
                    coin = Coin.objects.get(symbol=crypto.symbol)
                    try:
                        price = HistoricalCoinPrice.objects.get(coin=coin, date=end_date)
                        amt += get_in_preferred_currency(float(price*qty), 'USD', end_date)
                    except HistoricalCoinPrice.DoesNotExist:
                        pull_and_store_coin_historical_vals(crypto.symbol, end_date)
                except Coin.DoesNotExist:  
                    pull_and_store_coin_historical_vals(crypto.symbol, end_date)                
        return round(amt, 2)

    @classmethod
    def export(self, user_id):
        from shared.handle_get import get_goal_name_from_id

        ret = {
            self.get_export_name(): {
                'version':self.get_current_version()
            }
        }
        data = list()
        for co in Crypto.objects.filter(user=user_id):
            cod = {
                'symbol': co.symbol,
                'goal_name':''
            }
            if co.goal:
                cod['goal_name'] = get_goal_name_from_id(co.goal)
            t = list()
            for trans in Transaction.objects.filter(crypto=co):
                t.append({
                    'trans_date':trans.trans_date,
                    'trans_type': trans.trans_type,
                    'price': trans.price,
                    'units': trans.units,
                    'conversion_rate': trans.conversion_rate,
                    'trans_price':trans.trans_price,
                    'broker':trans.broker,
                    'notes':trans.notes
                })
            cod['transactions'] = t
            data.append(cod)
        
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret