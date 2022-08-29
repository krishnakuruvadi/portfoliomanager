from .models import Gold, SellTransaction
import datetime
from .gold_helper import get_historical_price, get_latest_price
from dateutil.relativedelta import relativedelta

class GoldInterface:
    
    @classmethod
    def get_chart_name(self):
        return 'Gold'

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
                deduct += float(st.trans_amount)
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
        for trans in Gold.objects.filter(user=user_id):
            if trans.buy_date.year == yr:
                contrib[trans.buy_date.month-1] += float(trans.buy_value)
            for st in SellTransaction.objects.filter(buy_trans=trans, trans_date__gte=st_date, trans_date__lte=end_date):
                deduct[trans.buy_date.month-1] += float(st.trans_amount)
        return contrib, deduct

    @classmethod
    def get_goal_yearly_contrib(self, goal_id, yr):
        st_date = datetime.date(year=yr, day=1, month=1)
        end_date = datetime.date(year=yr, day=31, month=12)
        today = datetime.date.today()
        if end_date > today:
            end_date = today
        contrib = 0
        deduct = 0
        total = 0
        cash_flows = list()
        wt = {'physical': {'24K':0, '22K':0}, "digital":0}
        for g_obj in Gold.objects.filter(goal=goal_id, buy_date__lte=end_date):
            bt = 'physical' if g_obj.buy_type == 'Physical' else 'digital'
            if bt == 'digital':
                wt[bt] += float(g_obj.weight)
            else:
                wt[bt][g_obj.purity] += float(g_obj.weight)
            if g_obj.buy_date >= st_date:
                contrib += float(g_obj.buy_value)
                cash_flows.append((g_obj.buy_date, -1*float(g_obj.buy_value)))

            for tran_obj in SellTransaction.objects.filter(buy_trans=g_obj, trans_date__lte=end_date):
                if tran_obj.trans_date >= st_date:
                    cash_flows.append((tran_obj.trans_date, -1*float(tran_obj.trans_amount)))
                    deduct += float(tran_obj.trans_amount)
                if bt == 'digital':
                    wt[bt] -= float(tran_obj.weight)
                else:
                    wt[bt][g_obj.purity] -= float(tran_obj.weight)
        if end_date == today:
            if wt['digital'] > 0:
                price,dt = get_latest_price('Digital', '24K')
                if price:
                    total += price * wt['digital']
                else:
                    print(f'failed to get total value for digital 24K for year {yr} {end_date}')
            if wt['physical']['24K'] > 0:
                price,dt = get_latest_price('Physical', '24K')
                if price:
                    total += price * wt['physical']['24K']
                else:
                    print(f'failed to get total value for physical 24K for year {yr}')
            if wt['physical']['22K'] > 0:
                price,dt = get_latest_price('Physical', '22K')
                if price:
                    total += price * wt['physical']['22K']
                else:
                    print(f'failed to get total value for physical 22K for year {yr}')
        else:
            if wt['digital'] > 0:
                res = get_historical_price(end_date+relativedelta(days=1), 'Digital', '24K')
                if res:
                    total += res * wt['digital']
                else:
                    print(f'failed to get total value for digital 24K for year {yr} {end_date}')
            if wt['physical']['24K'] > 0:
                res = get_historical_price(end_date+relativedelta(days=1), 'Physical', '24K')
                if res:
                    total += res * wt['physical']['24K']
                else:
                    print(f'failed to get total value for physical 24K for year {yr}')
            if wt['physical']['22K'] > 0:
                res = get_historical_price(end_date+relativedelta(days=1), 'Physical', '22K')
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
    def get_amount_for_all_users(self, ext_user):
        from users.user_interface import get_users
        amt = 0
        for u in get_users(ext_user):
            amt += self.get_amount_for_user(u.id)
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

    @classmethod
    def get_export_name(self):
        return 'gold'
    
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
        for go in Gold.objects.filter(user=user_id):
            eod = {
                'weight': go.weight,
                'per_gm': go.per_gm,
                'buy_value': go.buy_value,
                'buy_date': go.buy_date, 
                'notes':go.notes,
                'purity':go.purity,
                'buy_type':go.buy_type,
                'goal_name':''
            }
            if go.goal:
                eod['goal_name'] = get_goal_name_from_id(go.goal)
            t = list()
            for trans in SellTransaction.objects.filter(buy_trans=go):
                t.append({
                    'trans_date':trans.trans_date,
                    'weight':trans.weight,
                    'per_gm': trans.per_gm,
                    'trans_amount':trans.trans_amount,
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
        objs = Gold.objects.filter(user__in=ids)
        start = 0
        bought = 0
        sold = 0
        e = dict()
        amt = 0
        for obj in objs:
            #print(f'processing Gold {obj.buy_date}')
            if obj.buy_date < start_date:
                start_wt = float(obj.weight)
            else:
                start_wt = 0
                bought += obj.buy_value
            end_wt = float(obj.unsold_weight)
            amt += float(obj.latest_value) if obj.latest_value else 0
            for trans in SellTransaction.objects.filter(buy_trans=obj, trans_date__lte=end_date, trans_date__gte=start_date):
                start_wt -= float(trans.weight)
                sold += trans.trans_amount
            if start_wt > 0:
                res = get_historical_price(start_date, obj.buy_type, obj.purity)
                if res:
                    start += res * start_wt
                else:
                    print(f'failed to get vals for gold {obj.purity} {start_date}')
        

        ret['start'] = round(start, 2)
        ret['bought'] = round(bought, 2)
        ret['sold'] = round(sold, 2)
        ret['balance'] = round(amt, 2)
        changed = float(start+bought-sold)
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
            change = f"""<span style="margin-right:15px;font-size:18px;color:#56b454">▲</span>{round(update['change'],2)}%"""
        else:
            change = f"""<span style="margin-right:15px;font-size:18px;color:#df2028">▼</span>{round(update['change'],2)}%"""
        values = [update['start'], update['bought'], update['sold'], update['balance'], change]
        ret['content'] = get_weekly_update_table('Gold', col_names, values)
        ret['start'] = update['start']
        ret['credits'] = update['bought']
        ret['debits'] = update['sold']
        ret['balance'] = update['balance']
        print(f'ret {ret}')
        return ret
