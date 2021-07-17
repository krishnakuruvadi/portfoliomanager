from .models import Share, Transactions
import datetime
from tools.stock_reconcile import reconcile_event_based
from common.models import Bonusv2, Splitv2, Stock
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price_based_on_symbol
from dateutil.relativedelta import relativedelta


class ShareInterface:
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
                        start_day = obj.start_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} shares {ex}')
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
                    if share_obj.exchange == 'NASDAQ' or share_obj.exchange == 'NYSE':
                        conv_val = get_conversion_rate('USD', 'INR', end_date)
                        if conv_val:
                            conv_rate = conv_val
                        for k,v in year_end_value_vals.items():
                            total += float(v)*float(conv_rate)*float(qty)
                            break
                else:
                    print(f'failed to get year end values for {share_obj.exchange} {share_obj.symbol} {end_date}')            
        return cash_flows, contrib, deduct, total
