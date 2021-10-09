from .models import Gold, SellTransaction
import datetime
from .gold_helper import get_historical_price

class GoldInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Gold.objects.filter(user=user_id)
            else:
                objs = Gold.objects.filter()
            
            for obj in objs:
                if not start_day:
                    start_day = obj.buy_date
                else:
                    start_day = start_day if start_day < obj.buy_date else obj.buy_date
        except Exception as ex:
            print(f'exception finding start day for Gold {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_goal(self, goal_id):
        start_day = None
        try:
            objs = Gold.objects.filter(goal=goal_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.buy_date
                else:
                    start_day = start_day if start_day < obj.buy_date else obj.buy_date
        except Exception as ex:
            print(f'exception finding start day for goal {goal_id} Gold {ex}')
        return start_day
    
    @classmethod
    def get_start_day_for_user(self, user_id):
        start_day = None
        try:
            objs = Gold.objects.filter(user=user_id)
            for obj in objs:
                if not start_day:
                    start_day = obj.buy_date
                else:
                    start_day = start_day if start_day < obj.buy_date else obj.buy_date
        except Exception as ex:
            print(f'exception finding start day for user {user_id} Gold {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Gold.objects.filter(user=user_id)
        else:
            objs = Gold.objects.filter()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.latest_value else obj.latest_value
        return amt
    
    @classmethod
    def get_user_yearly_contrib(self, user_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        contrib = 0
        deduct = 0
        for trans in Gold.objects.filter(user=user_id):
            if trans.buy_date.year == yr:
                contrib += float(trans.buy_value)
            for st in SellTransaction.objects.filter(buy_trans=trans, trans_date__gte=st_date, trans_date__lte=end_date):
                deduct += st.trans_amount
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
        wt = {'physical': {'24K':0, '22K':0}, "digital":0}
        for g_obj in Gold.objects.filter(goal=goal_id, buy_date__lte=end_date):
            bt = 'physical' if g_obj.buy_type == 'Physical' else 'digital'
            if bt == 'digital':
                wt[bt] += g_obj.weight
            else:
                wt[bt][g_obj.purity] += g_obj.weight
            if g_obj.buy_date >= st_date:
                contrib += float(g_obj.buy_value)
                cash_flows.append((g_obj.buy_date, -1*float(g_obj.buy_value)))

            for tran_obj in SellTransaction.objects.filter(buy_trans=g_obj, trans_date__lte=end_date):
                if tran_obj.trans_date >= st_date:
                    cash_flows.append((tran_obj.trans_date, -1*float(tran_obj.trans_amount)))
                    deduct += float(tran_obj.trans_amount)
                if bt == 'digital':
                    wt[bt] -= tran_obj.weight
                else:
                    wt[bt][g_obj.purity] -= tran_obj.weight

        if wt['digital'] > 0:
            res = get_historical_price(end_date, 'Digital', '24K')
            if res:
                total += res * wt['digital']
            else:
                print(f'failed to get total value for digital 24K for year {yr}')
        if wt['physical']['24K'] > 0:
            res = get_historical_price(end_date, 'Physical', '24K')
            if res:
                total += res * wt['physical']['24K']
            else:
                print(f'failed to get total value for physical 24K for year {yr}')
        if wt['physical']['22K'] > 0:
            res = get_historical_price(end_date, 'Physical', '22K')
            if res:
                total += res * wt['physical']['22K']
            else:
                print(f'failed to get total value for physical 22K for year {yr}')
        return cash_flows, contrib, deduct, total
    
    @classmethod
    def get_amount_for_goal(self, goal_id):
        amt = 0
        objs = Gold.objects.filter(goal=goal_id)
        for obj in objs:
            amt += 0 if not obj.latest_value else obj.latest_value
        return amt
    
    @classmethod
    def get_amount_for_user(self, user_id):
        amt = 0
        objs = Gold.objects.filter(user=user_id)
        for obj in objs:
            amt += 0 if not obj.latest_value else obj.latest_value
        return amt
    
    @classmethod
    def get_value_as_on(self, end_date):
        amt = 0
        unsold_wt = {'physical': {'24K':0, '22K':0}, "digital":0}
        for gold_obj in Gold.objects.filter(buy_date__lte=end_date):
            wt = gold_obj.weight
            for tran_obj in SellTransaction.objects.filter(buy_trans=gold_obj, trans_date__lte=end_date):
                wt = wt - tran_obj.weight
            if gold_obj.buy_type == 'Physical':
                unsold_wt['physical'][gold_obj.purity] += float(wt)
            else:
                unsold_wt['digital'] += float(wt)
        if unsold_wt['digital'] > 0:
            res = get_historical_price(end_date, 'Digital', '24K')
            if res:
                amt += res * unsold_wt['digital']
            else:
                print(f'failed to get total value for digital 24K for {end_date}')
        if unsold_wt['physical']['24K'] > 0:
            res = get_historical_price(end_date, 'Physical', '24K')
            if res:
                amt += res * unsold_wt['physical']['24K']
            else:
                print(f'failed to get total value for physical 24K for {end_date}')
        if unsold_wt['physical']['22K'] > 0:
            res = get_historical_price(end_date, 'Physical', '22K')
            if res:
                amt += res * unsold_wt['physical']['22K']
            else:
                print(f'failed to get total value for physical 22K for {end_date}')
        return round(amt, 2)
