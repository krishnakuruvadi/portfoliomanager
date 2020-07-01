from ppf.models import Ppf, PpfEntry
from ssy.models import Ssy, SsyEntry
from fixed_deposit.models import FixedDeposit
from fixed_deposit.fixed_deposit_helper import get_maturity_value
from espp.models import Espp
from rsu.models import RSUAward, RestrictedStockUnits
from epf.models import Epf, EpfEntry
from goal.models import Goal
from users.models import User
import datetime
from dateutil.relativedelta import relativedelta
from common.models import HistoricalStockPrice, Stock
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price

def get_ppf_amount_for_goal(id):
    ppf_objs = Ppf.objects.filter(goal=id)
    total_ppf = 0
    for ppf_obj in ppf_objs:
        ppf_num = ppf_obj.number
        amt = 0
        ppf_trans = PpfEntry.objects.filter(number=ppf_num)
        for entry in ppf_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.amount
            else:
                amt -= entry.amount
        if amt < 0:
            amt = 0
        total_ppf += amt
    return total_ppf

def get_ssy_amount_for_goal(id):
    ssy_objs = Ssy.objects.filter(goal=id)
    total_ssy = 0
    for ssy_obj in ssy_objs:
        ssy_num = ssy_obj.number
        amt = 0
        ssy_trans = SsyEntry.objects.filter(number=ssy_num)
        for entry in ssy_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.amount
            else:
                amt -= entry.amount
        if amt < 0:
            amt = 0
        total_ssy += amt
    return total_ssy

def get_fd_amount_for_goal(id):
    fd_objs = FixedDeposit.objects.filter(goal=id)
    total_fd = 0
    for fd_obj in fd_objs:
        total_fd += fd_obj.final_val
    return total_fd

def get_espp_amount_for_goal(id):
    espp_objs = Espp.objects.filter(goal=id)
    total_espp = 0
    for espp_obj in espp_objs:
        if not espp_obj.total_sell_price:
            total_espp += espp_obj.latest_value
    return total_espp

def get_rsu_amount_for_goal(id):
    award_objs = RSUAward.objects.filter(goal=id)
    total_rsu = 0
    for award_obj in award_objs:
        for rsu_obj in RestrictedStockUnits.objects.filter(award=award_obj):
            if not rsu_obj.total_sell_price:
                if rsu_obj.latest_value:
                    total_rsu += rsu_obj.latest_value
    return total_rsu

def get_epf_amount_for_goal(id):
    epf_objs = Epf.objects.filter(goal=id)
    total_epf = 0
    for epf_obj in epf_objs:
        epf_id = epf_obj.id
        amt = 0
        epf_trans = EpfEntry.objects.filter(epf_id=epf_id)
        for entry in epf_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
            else:
                amt -= entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
        if amt < 0:
            amt = 0
        total_epf += amt
    return total_epf

def get_goal_contributions(goal_id):
    print("inside get_goal_contributions")
    contrib = dict()
    contrib['epf'] = int(get_epf_amount_for_goal(goal_id))
    contrib['espp'] = int(get_espp_amount_for_goal(goal_id))
    contrib['fd'] = int(get_fd_amount_for_goal(goal_id))
    contrib['ppf'] =int(get_ppf_amount_for_goal(goal_id))
    contrib['ssy'] =int(get_ssy_amount_for_goal(goal_id))
    contrib['rsu'] =int(get_rsu_amount_for_goal(goal_id))
    contrib['equity'] = contrib['espp']+contrib['rsu']
    contrib['debt'] = contrib['epf'] + contrib['fd'] + contrib['ppf'] + contrib['ssy']
    contrib['total'] = contrib['equity'] + contrib['debt']
    contrib['distrib_labels'] = ['EPF','ESPP','FD','PPF','SSY','RSU']
    contrib['distrib_vals'] = [contrib['epf'],contrib['espp'],contrib['fd'],contrib['ppf'],contrib['ssy'],contrib['rsu']]
    contrib['distrib_colors'] = ['#f15664', '#DC7633','#006f75','#92993c','#f9c5c6','#AA12E8']
    print("contrib:", contrib)
    return contrib

def get_ppf_amount_for_user(user_id):
    ppf_objs = Ppf.objects.filter(user=user_id)
    total_ppf = 0
    for ppf_obj in ppf_objs:
        ppf_num = ppf_obj.number
        amt = 0
        ppf_trans = PpfEntry.objects.filter(number=ppf_num)
        for entry in ppf_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.amount
            else:
                amt -= entry.amount
        if amt < 0:
            amt = 0
        total_ppf += amt
    return total_ppf

def get_ssy_amount_for_user(user_id):
    ssy_objs = Ssy.objects.filter(user=user_id)
    total_ssy = 0
    for ssy_obj in ssy_objs:
        ssy_num = ssy_obj.number
        amt = 0
        ssy_trans = SsyEntry.objects.filter(number=ssy_num)
        for entry in ssy_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.amount
            else:
                amt -= entry.amount
        if amt < 0:
            amt = 0
        total_ssy += amt
    return total_ssy

def get_fd_amount_for_user(user_id):
    fd_objs = FixedDeposit.objects.filter(user=user_id)
    total_fd = 0
    for fd_obj in fd_objs:
        total_fd += fd_obj.final_val
    return total_fd

def get_espp_amount_for_user(user_id):
    espp_objs = Espp.objects.filter(user=user_id)
    total_espp = 0
    for espp_obj in espp_objs:
        if not espp_obj.total_sell_price:
            if espp_obj.latest_value:
                total_espp += espp_obj.latest_value
    return total_espp

def get_rsu_amount_for_user(user_id):
    award_objs = RSUAward.objects.filter(user=user_id)
    total_rsu = 0
    for award_obj in award_objs:
        for rsu_obj in RestrictedStockUnits.objects.filter(award=award_obj):
            if not rsu_obj.total_sell_price:
                if rsu_obj.latest_value:
                    total_rsu += rsu_obj.latest_value
    return total_rsu

def get_epf_amount_for_user(user_id):
    epf_objs = Epf.objects.filter(user=user_id)
    total_epf = 0
    for epf_obj in epf_objs:
        epf_id = epf_obj.id
        amt = 0
        epf_trans = EpfEntry.objects.filter(epf_id=epf_id)
        for entry in epf_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                amt += entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
            else:
                amt -= entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
        if amt < 0:
            amt = 0
        total_epf += amt
    return total_epf

def get_goal_target_for_user(user_id):
    goal_objs = Goal.objects.filter(user=user_id)
    target_amt = 0
    for goal_obj in goal_objs:
        target_amt += goal_obj.final_val
    return target_amt

def get_user_contributions(user_id):
    print("inside get_user_contributions")
    try:
        user_obj = User.objects.get(id=user_id)
        contrib = dict()
        contrib['target'] = int(get_goal_target_for_user(user_id))
        contrib['epf'] = int(get_epf_amount_for_user(user_id))
        contrib['espp'] = int(get_espp_amount_for_user(user_id))
        contrib['fd'] = int(get_fd_amount_for_user(user_id))
        contrib['ppf'] =int(get_ppf_amount_for_user(user_id))
        contrib['ssy'] =int(get_ssy_amount_for_user(user_id))
        contrib['rsu'] = int(get_rsu_amount_for_user(user_id))
        contrib['equity'] = contrib['espp']+contrib['rsu']
        contrib['debt'] = contrib['epf'] + contrib['fd'] + contrib['ppf'] + contrib['ssy']
        contrib['total'] = contrib['equity'] + contrib['debt']
        contrib['distrib_labels'] = ['EPF','ESPP','FD','PPF','SSY','RSU']
        contrib['distrib_vals'] = [contrib['epf'],contrib['espp'],contrib['fd'],contrib['ppf'],contrib['ssy'],contrib['rsu']]
        contrib['distrib_colors'] = ['#f15664', '#DC7633','#006f75','#92993c','#f9c5c6','#AA12E8']
        print("contrib:", contrib)
        return contrib
    except User.DoesNotExist:
        print("User with id ", user_id, " does not exist" )
        pass

def get_investment_data(start_date):
    data_start_date = start_date+ relativedelta(months=-1)

    epf_data = list()
    ppf_data = list()
    ssy_data = list()
    fd_data = list()
    espp_data = list()
    rsu_data = list()
    total_data = list()

    total_epf = 0
    total_ppf = 0
    total_ssy = 0

    epf_reset_on_zero = False
    fd_reset_on_zero = False
    ppf_reset_on_zero = False
    ssy_reset_on_zero = False
    espp_reset_on_zero = False
    rsu_reset_on_zero = False
    total_reset_on_zero = False
    
    while data_start_date + relativedelta(months=+1) < datetime.date.today():
        total = 0
        data_end_date = data_start_date + relativedelta(months=+1)
        epf_entries = EpfEntry.objects.filter(trans_date__range=(data_start_date, data_end_date))
        for epf_entry in epf_entries:
            print("epf entry")
            if epf_entry.entry_type.lower() == 'cr' or epf_entry.entry_type.lower() == 'credit':
                total_epf += int(epf_entry.employee_contribution) + int(epf_entry.employer_contribution) + int(epf_entry.interest_contribution)
            else:
                total_epf -= int(epf_entry.employee_contribution) + int(epf_entry.employer_contribution) + int(epf_entry.interest_contribution)
        if total_epf != 0:
            if not epf_reset_on_zero:
                epf_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            epf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':total_epf})
            total += total_epf
            epf_reset_on_zero = True
        elif epf_reset_on_zero:
            epf_reset_on_zero = False
            epf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})
        
        ppf_entries = PpfEntry.objects.filter(trans_date__range=(data_start_date, data_end_date))
        for ppf_entry in ppf_entries:
            print("ppf entry")

            if ppf_entry.entry_type.lower() == 'cr' or ppf_entry.entry_type.lower() == 'credit':
                total_ppf += int(ppf_entry.amount)
            else:
                total_ppf -= int(ppf_entry.amount)
        if total_ppf != 0:
            if not ppf_reset_on_zero:
                ppf_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            ppf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':total_ppf})
            total += total_ppf
            ppf_reset_on_zero = True
        elif ppf_reset_on_zero:
            ppf_reset_on_zero = False
            ppf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})

        ssy_entries = SsyEntry.objects.filter(trans_date__year=data_start_date.year, trans_date__month=data_start_date.month)
        for ssy_entry in ssy_entries:
            if ssy_entry.entry_type.lower() == 'cr' or ssy_entry.entry_type.lower() == 'credit':
                total_ssy += int(ssy_entry.amount)
            else:
                total_ssy -= int(ssy_entry.amount)
        if total_ssy != 0:
            if not ssy_reset_on_zero:
                ssy_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            ssy_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':total_ssy})
            total += total_ssy
            ssy_reset_on_zero = True
        elif ssy_reset_on_zero:
            ssy_reset_on_zero = False
            ssy_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})
        
        fd_entries = FixedDeposit.objects.filter(start_date__lte=data_start_date, mat_date__gte=data_end_date)
        fd_val = 0
        for fd in fd_entries:
            time_period = data_end_date-fd.start_date
            _, val = get_maturity_value(float(fd.principal), fd.start_date.strftime('%Y-%m-%d'), float(fd.roi), time_period.days)
            fd_val += val
        if fd_val != 0:
            if not fd_reset_on_zero:
                fd_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            fd_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':fd_val})
            total += fd_val
            fd_reset_on_zero = True
        elif fd_reset_on_zero:
            fd_reset_on_zero = False
            fd_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})
        
        espp_entries = Espp.objects.filter(purchase_date__lte=data_end_date)
        espp_val = 0
        for espp_entry in espp_entries:
            #print("espp entry")
            if espp_entry.sell_date is None or espp_entry.sell_date < data_end_date:
                try:
                    stock = Stock.objects.get(symbol=espp_entry.symbol, exchange=espp_entry.exchange)
                    historical_stock_prices = get_historical_stock_price(stock, data_end_date+relativedelta(days=-5), data_end_date)
                    for val in historical_stock_prices:
                        found = False
                        #print(val)
                        for k,v in val.items():
                            if espp_entry.exchange == 'NYSE' or espp_entry.exchange == 'NASDAQ':
                                conv_val = get_conversion_rate('USD', 'INR', data_end_date)
                                #print('conversion value', conv_val)
                                if conv_val:
                                    espp_val += float(conv_val)*float(v)*int(espp_entry.shares_purchased)
                                    found = True
                                    break
                            else:
                                espp_val += float(v)*int(espp_entry.shares_purchased)
                                found = True
                                break
                        if found:
                            break
                except Stock.DoesNotExist:
                    pass
        if espp_val != 0:
            if not espp_reset_on_zero:
                espp_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            espp_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':int(espp_val)})
            total += espp_val
            espp_reset_on_zero = True
        elif espp_reset_on_zero:
            espp_reset_on_zero = False
            espp_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})

        rsu_entries = RestrictedStockUnits.objects.filter(vest_date__lte=data_end_date)
        rsu_val = 0
        for rsu_entry in rsu_entries:
            print("rsu entry")
            if rsu_entry.sell_date is None or rsu_entry.sell_date < data_end_date:
                try:
                    stock = Stock.objects.get(symbol=rsu_entry.award.symbol, exchange=rsu_entry.award.exchange)
                    historical_stock_prices = get_historical_stock_price(stock, data_end_date+relativedelta(days=-5), data_end_date)
                    for val in historical_stock_prices:
                        found = False
                        #print(val)
                        for k,v in val.items():
                            if stock.exchange == 'NYSE' or stock.exchange == 'NASDAQ':
                                conv_val = get_conversion_rate('USD', 'INR', data_end_date)
                                #print('conversion value', conv_val)
                                if conv_val:
                                    rsu_val += float(conv_val)*float(v)*int(rsu_entry.shares_for_sale)
                                    found = True
                                    break
                            else:
                                rsu_val += float(v)*int(rsu_entry.shares_for_sale)
                                found = True
                                break
                        if found:
                            break
                except Stock.DoesNotExist:
                    pass
        if rsu_val != 0:
            if not rsu_reset_on_zero:
                rsu_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            rsu_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':int(rsu_val)})
            total += rsu_val
            rsu_reset_on_zero = True
        elif rsu_reset_on_zero:
            rsu_reset_on_zero = False
            rsu_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})

        if total != 0:
            if not total_reset_on_zero:
                total_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            total_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':int(total)})
            total_reset_on_zero = True
        elif total_reset_on_zero:
            total_reset_on_zero = False
            total_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})

        data_start_date  = data_start_date+relativedelta(months=+1)

    return {'ppf':ppf_data, 'epf':epf_data, 'ssy':ssy_data, 'fd': fd_data, 'espp': espp_data, 'rsu':rsu_data, 'total':total_data}
        

