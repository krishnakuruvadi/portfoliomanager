from .models import Share, Transactions
import datetime
from tools.stock_reconcile import reconcile_event_based
from common.models import Bonusv2, Splitv2, Stock
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price_based_on_symbol, get_in_preferred_currency
from dateutil.relativedelta import relativedelta

class ShareInterface:

    @classmethod
    def get_chart_name(self):
        return 'Shares'

    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Share.objects.filter(user=user_id)
            else:
                objs = Share.objects.all()
            
            for obj in objs:
                share_trans = Transactions.objects.filter(share=obj)
                for trans in share_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for shares {ex}')
        return start_day

    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Share.objects.filter(goal=goal_id)
            for obj in objs:
                share_trans = Transactions.objects.filter(share=obj)
                for trans in share_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} shares {ex}')
        return start_day

    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = Share.objects.filter(user=user_id)
            for obj in objs:
                share_trans = Transactions.objects.filter(share=obj)
                for trans in share_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} shares {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Share.objects.filter(user=user_id)
        else:
            objs = Share.objects.all()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.latest_value else obj.latest_value
        return amt

    @classmethod
    def get_goal_yearly_contrib(self, goal_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        if end_date > datetime.date.today():
            end_date = datetime.date.today()
        cash_flows = list()
        contrib = 0
        deduct = 0
        total = 0

        for share_obj in Share.objects.filter(goal=goal_id):
            transactions = Transactions.objects.filter(share=share_obj, trans_date__lte=end_date)
            stock = Stock.objects.get(exchange=share_obj.exchange, symbol=share_obj.symbol)
            bonuses = Bonusv2.objects.filter(stock=stock, record_date__lte=end_date)
            splits = Splitv2.objects.filter(stock=stock, ex_date__lte=end_date)
            round_qty_to_int = True if share_obj.exchange in ['NSE', 'BSE', 'NSE/BSE'] else False
            qty, buy_value, buy_price, realised_gain, unrealised_gain = reconcile_event_based(transactions, bonuses, splits, round_qty_to_int=round_qty_to_int, latest_price=share_obj.latest_price, latest_conversion_rate=share_obj.conversion_rate)
            for t in transactions:
                if t.trans_date >= st_date:
                    if t.trans_type == 'Buy':
                        cash_flows.append((t.trans_date, -1*float(t.trans_price)))
                        contrib += float(t.trans_price)
                    else:
                        cash_flows.append((t.trans_date, float(t.trans_price)))
                        deduct += -1*float(t.trans_price)
            if qty > 0:
                year_end_value_vals = get_historical_stock_price_based_on_symbol(share_obj.symbol, share_obj.exchange, end_date+relativedelta(days=-5), end_date)
                if year_end_value_vals:
                    conv_rate = 1
                    if share_obj.exchange in ['NASDAQ', 'NYSE']:
                        conv_val = get_in_preferred_currency(1, 'USD', end_date)
                        if conv_val:
                            conv_rate = conv_val
                    elif share_obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        conv_val = get_in_preferred_currency(1, 'INR', end_date)
                        if conv_val:
                            conv_rate = conv_val
                    for k,v in year_end_value_vals.items():
                        total += float(v)*float(conv_rate)*float(qty)
                        break
                else:
                    print(f'failed to get year end values for {share_obj.exchange} {share_obj.symbol} {end_date}')
            else:
                print(f'qty =0 for {share_obj.exchange} {share_obj.symbol} {yr} {goal_id}')
        print(f'for {yr} shares returning {cash_flows}, {contrib}, {deduct}, {total}')
        return cash_flows, contrib, deduct, total

    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for share_obj in Share.objects.filter(user=user_id):
            transactions = Transactions.objects.filter(share=share_obj, trans_date__gte=st_date, trans_date__lte=end_date)
            for t in transactions:
                if t.trans_type == 'Buy':
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
        for share_obj in Share.objects.filter(user=user_id):
            transactions = Transactions.objects.filter(share=share_obj, trans_date__gte=st_date, trans_date__lte=end_date)
            for t in transactions:
                if t.trans_type == 'Buy':
                    contrib[t.trans_date.month-1] += float(t.trans_price)
                else:
                    deduct[t.trans_date.month-1] += -1*float(t.trans_price)
        return contrib, deduct
    
    @classmethod
    def get_amount_for_user(self, user_id):
        share_objs = Share.objects.filter(user=user_id)
        total_shares = 0
        for share_obj in share_objs:
            if share_obj.latest_value:
                total_shares += share_obj.latest_value
        return total_shares
    
    @classmethod
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
        return amt

    @classmethod
    def get_export_name(self):
        return 'shares'
    
    @classmethod
    def get_current_version(self):
        return 'v1'

    @classmethod
    def export(self, user_id):
        from shared.handle_get import get_goal_name_from_id

        ret = {
            self.get_export_name(): {
                'version':self.get_current_version()
            }
        }
        data = list()
        for so in Share.objects.filter(user=user_id):
            eod = {
                'exchange': so.exchange,
                'symbol': so.symbol,
                'notes':so.notes,
                'etf':so.etf,
                'goal_name':''
            }
            if so.goal:
                eod['goal_name'] = get_goal_name_from_id(so.goal)
            t = list()
            for trans in Transactions.objects.filter(share=so):
                t.append({
                    'trans_date':trans.trans_date,
                    'trans_type': trans.trans_type,
                    'price': trans.price,
                    'quantity': trans.quantity,
                    'conversion_rate': trans.conversion_rate,
                    'trans_price':trans.trans_price,
                    'broker':trans.broker,
                    'div_reinv':trans.div_reinv,
                    'notes':trans.notes
                })
            eod['transactions'] = t
            data.append(eod)
        
        ret[self.get_export_name()]['data'] = data
        print(ret)
        return ret
    
    @classmethod
    def updates_summary(self, ext_user, start_date, end_date):
        from users.user_interface import get_users
        from shared.financial import xirr, calc_simple_roi

        diff_days = (end_date - start_date).days

        ret = dict()
        ret['details'] = list()
        ids = list()
        for u in get_users(ext_user):
            ids.append(u.id)
        objs = Share.objects.filter(user__in=ids)
        start = 0
        bought = 0
        sold = 0
        e = dict()
        amt = 0
        for obj in objs:
            #print(f'processing {obj.folio}')
            amt += float(obj.latest_value) if obj.latest_value else 0
            transactions = Transactions.objects.filter(share=obj, trans_date__lte=start_date)
            stock = Stock.objects.get(exchange=obj.exchange, symbol=obj.symbol)
            bonuses = Bonusv2.objects.filter(stock=stock, record_date__lte=start_date)
            splits = Splitv2.objects.filter(stock=stock, ex_date__lte=start_date)
            round_qty_to_int = True if obj.exchange in ['NSE', 'BSE', 'NSE/BSE'] else False
            qty, buy_value, buy_price, realised_gain, unrealised_gain = reconcile_event_based(transactions, bonuses, splits, round_qty_to_int=round_qty_to_int, latest_price=obj.latest_price, latest_conversion_rate=obj.conversion_rate)

            if qty > 0:
                vals = get_historical_stock_price_based_on_symbol(obj.symbol, obj.exchange, start_date+relativedelta(days=-5), start_date)
                if vals:
                    conv_rate = 1
                    if obj.exchange in ['NYSE', 'NASDAQ']:
                        conv_val = get_in_preferred_currency(1, 'USD', start_date)
                        if conv_val:
                            conv_rate = conv_val
                    elif obj.exchange in ['NSE', 'BSE', 'NSE/BSE']:
                        conv_val = get_in_preferred_currency(1, 'INR', start_date)
                        if conv_val:
                            conv_rate = conv_val
                    for k,v in vals.items():
                        start += float(v)*float(conv_rate)*float(qty)
                        break
                else:
                    print(f'failed to get values for {obj.exchange} {obj.symbol} {start_date}')
            for trans in Transactions.objects.filter(share=obj, trans_date__lte=end_date, trans_date__gte=start_date):
                if trans.trans_type == 'Buy':
                    bought += trans.trans_price
                else:
                    sold += trans.trans_price        

        ret['start'] = round(start, 2)
        ret['bought'] = round(bought, 2)
        ret['sold'] = round(sold, 2)
        ret['balance'] = round(amt, 2)
        changed = float(start)+float(bought)-float(sold)
        if changed != float(amt):
            if diff_days >= 365:
                cash_flows = list()
                cash_flows.append((start_date, -1*float(changed)))
                cash_flows.append((end_date, float(amt)))
                print(f'finding xirr for {cash_flows}')
                ret['change'] = xirr(cash_flows, 0.1)*100
            else:
                ret['change'] = calc_simple_roi(changed , amt)
        else:
            ret['change'] = 0
        ret['details'].append(e)
        return ret

    @classmethod
    def updates_email(self, ext_user, start_date, end_date):
        update = self.updates_summary(ext_user, start_date, end_date)
        from shared.email_html import get_weekly_update_table
        ret = dict()
        col_names = ['Start','Bought','Sold','Balance', 'Change']
        if update['change'] >= 0:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>{round(update['change'], 2)}%"""
        else:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#df2028">▼</span>{round(update['change'], 2)}%"""
        values = [update['start'], update['bought'], update['sold'], update['balance'], change]
        ret['content'] = get_weekly_update_table('Stocks', col_names, values)
        ret['start'] = update['start']
        ret['credits'] = update['bought']
        ret['debits'] = update['sold']
        ret['balance'] = update['balance']
        print(f'ret {ret}')
        return ret
