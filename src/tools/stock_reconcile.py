from enum import IntEnum

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
    
    def setSplit(self,old_fv,new_fv):
        self.old_fv = old_fv
        self.new_fv = new_fv
    
    def setBonus(self, ratio_num, ratio_denom):
        self.ratio_num = ratio_num
        self.ratio_denom = ratio_denom
    
    def __str__(self) -> str:
        if self.event_type == EventType.BUY:
            return self.dt.strftime('%d-%m-%Y') + ':  Buy ' + str(self.qty) + ' totalling ' + str(self.price)
        if self.event_type == EventType.SELL:
            return self.dt.strftime('%d-%m-%Y') + ':  Sell ' + str(self.qty) + ' totalling ' + str(self.price)
        if self.event_type == EventType.SPLIT:
            return self.dt.strftime('%d-%m-%Y') + ': Split old fv:' + str(self.old_fv) + ' new fv:' + str(self.new_fv)
        if self.event_type == EventType.BONUS:
            return self.dt.strftime('%d-%m-%Y') + ': Bonus ratio:' + str(self.ratio_num) + ':' + str(self.ratio_denom)
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
    
    def split(self, old_fv, new_fv):
        if not self.unsold:
            return
        self.qty = self.qty*old_fv/new_fv
        self.price = self.price*new_fv/old_fv

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

class Bonus():
    def __init__(self, ratio_num, ratio_denom, record_date, ex_date, announcement_date):
        self.ratio_num = ratio_num
        self.ratio_denom = ratio_denom
        self.announcement_date = announcement_date
        self.record_date = record_date
        self.ex_date = ex_date

class Splitv():
    def __init__(self, old_fv, new_fv, announcement_date, ex_date):
        self.old_fv = old_fv
        self.new_fv = new_fv
        self.announcement_date = announcement_date
        self.ex_date = ex_date


def reconcile_event_based(transactions, bonuses, splits, round_qty_to_int=False, latest_price=None, latest_conversion_rate=1):
    event_list = list()
    buy_value = 0
    buy_price = 0
    for trans in transactions:
        trans_type = trans.trans_type
        if type(trans.trans_type) is str:
            trans_type = EventType.BUY if trans.trans_type.lower()=='buy' else EventType.SELL
        e = Event(trans_type, trans.trans_date)
        e.setQty(trans.quantity)
        e.setPrice(trans.price)
        event_list.append(e)
        buy_value += float(trans.trans_price)
        buy_price += float(trans.price)
    
    for b in bonuses:
        #https://www.angelbroking.com/knowledge-center/demat-account/what-are-bonus-shares
        '''
        India follows the T+2 rolling system for the delivery of shares, wherein the ex-date is two days ahead of the record date.
        Shares must be bought before the ex-date because, if an investor purchases the shares on the ex-date, they will not be credited with the ownership of given shares by the set record date and therefore, will not be eligible for the bonus shares.
        '''
        e = Event(EventType.BONUS, b.ex_date)
        e.setBonus(b.ratio_num, b.ratio_denom)
        event_list.append(e)
    
    for s in splits:
        e = Event(EventType.SPLIT, s.ex_date)
        e.setSplit(s.old_fv, s.new_fv)
        event_list.append(e)
    
    event_list.sort(key=lambda x: (x.dt,x.event_type), reverse=False)

    # https://blog.quicko.com/bonus-shares-tax-applicability
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
        elif event.event_type == EventType.SPLIT:
            for deal in deals:
                deal.split(event.old_fv, event.new_fv)
        elif event.event_type == EventType.BONUS:
            qty = 0
            for deal in deals:
                if deal.can_sell():
                    qty += deal.qty
            if qty > 0 :
                qty = qty*event.ratio_num/event.ratio_denom
                if round_qty_to_int:
                    qty = int(qty)
                if qty > 0:
                    deals.append(Deal(event.dt, qty, 0))
                    deals.sort(key=lambda x: x.in_dt, reverse=False)
        #for deal in deals:
        #    print(f'\t {deal}')
    realised_gain = 0
    qty = 0
    unrealised_gain = 0
    for deal in deals:
        print(f'\t {deal}')
        if deal.profit:
            realised_gain += deal.profit
        if deal.can_sell():
            qty += deal.qty
    if qty > 0 and latest_price:
        unrealised_gain = float(qty) * float(latest_price) * float(latest_conversion_rate)
    print(f'quantity: {qty}, realised gain: {realised_gain}, unrealised gain: {unrealised_gain}')
    return qty, buy_value, buy_price, realised_gain, unrealised_gain

