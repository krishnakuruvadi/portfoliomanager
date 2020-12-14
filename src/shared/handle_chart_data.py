from ppf.models import Ppf, PpfEntry
from ssy.models import Ssy, SsyEntry
from fixed_deposit.models import FixedDeposit
from fixed_deposit.fixed_deposit_helper import get_maturity_value
from espp.models import Espp
from rsu.models import RSUAward, RestrictedStockUnits
from epf.models import Epf, EpfEntry
from goal.models import Goal
from shares.models import Share, Transactions
from users.models import User
import datetime
from dateutil.relativedelta import relativedelta
from common.models import HistoricalStockPrice, Stock, MutualFund
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price, get_historical_mf_nav, get_historical_stock_price_based_on_symbol
from shared.handle_create import add_common_stock
from mutualfunds.models import Folio, MutualFundTransaction

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

def get_shares_amount_for_goal(id):
    share_objs = Share.objects.filter(goal=id)
    total_shares = 0
    for share_obj in share_objs:
        if share_obj.latest_value:
            total_shares += share_obj.latest_value
    return total_shares

def get_mf_amount_for_goal(id):
    folio_objs = Folio.objects.filter(goal=id)
    total = 0
    for folio_obj in folio_objs:
        if folio_obj.latest_value:
            total += folio_obj.latest_value
    return total

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
    contrib['shares'] = int(get_shares_amount_for_goal(goal_id))
    contrib['mf'] = int(get_mf_amount_for_goal(goal_id))
    contrib['equity'] = contrib['espp']+contrib['rsu']+contrib['shares']+contrib['mf']
    contrib['debt'] = contrib['epf'] + contrib['fd'] + contrib['ppf'] + contrib['ssy']
    contrib['total'] = contrib['equity'] + contrib['debt']
    contrib['distrib_labels'] = ['EPF','ESPP','FD','PPF','SSY','RSU','Shares','MutualFunds']
    contrib['distrib_vals'] = [contrib['epf'],contrib['espp'],contrib['fd'],contrib['ppf'],contrib['ssy'],contrib['rsu'],contrib['shares'],contrib['mf']]
    contrib['distrib_colors'] = ['#f15664', '#DC7633','#006f75','#92993c','#f9c5c6','#AA12E8','#e31219','#bfff00']
    print("contrib:", contrib)
    return contrib

#port: portfolioval
#contrib: contribution 
#deduct: deduction
def add_or_create(year, key, contrib_obj, deduct_obj, port_obj, contrib, deduct, port):
    if year not in contrib_obj:
        contrib_obj[year] = dict()
        port_obj[year] = dict()
        deduct_obj[year] = dict()
    if contrib:
        contrib_obj[year][key] = contrib + contrib_obj[year].get(key, 0)
    if port:
        port_obj[year][key] = port + port_obj[year].get(key, 0)
    if deduct: 
        deduct_obj[year][key] = port + deduct_obj[year].get(key, 0)

def get_goal_yearly_contrib(goal_id, format='%Y-%m-%d'):
    print("inside get_goal_yearly_contrib")
    contrib = dict()
    total = dict()
    deduct = dict()

    for ppf_obj in Ppf.objects.filter(goal=goal_id):
        for ppf_trans in PpfEntry.objects.filter(number=ppf_obj):
            #entry_date = (datetime.date(ppf_trans.year + (ppf_trans.month == 12), 
            #      (ppf_trans.month + 1 if ppf_trans.month < 12 else 1), 1) - datetime.timedelta(1)).strftime(format)
            if ppf_trans.interest_component:
                if ppf_trans.entry_type == 'CR':
                    add_or_create(ppf_trans.trans_date.year, 'PPF', contrib, deduct, total, 0, 0, ppf_trans.amount)
                else:
                    add_or_create(ppf_trans.trans_date.year, 'PPF', contrib, deduct, total, 0, 0, -1*ppf_trans.amount)
            else:
                if ppf_trans.entry_type == 'CR':
                    add_or_create(ppf_trans.trans_date.year, 'PPF', contrib, deduct, total, ppf_trans.amount, 0, ppf_trans.amount)
                else:
                    add_or_create(ppf_trans.trans_date.year, 'PPF', contrib, deduct, total, 0, -1*ppf_trans.amount, -1*ppf_trans.amount)
     
    for epf_obj in Epf.objects.filter(goal=goal_id):
        for epf_trans in EpfEntry.objects.filter(number=epf_obj):
        #entry_date = (datetime.date(epf_trans.year + (epf_trans.month == 12), 
        #      (epf_trans.month + 1 if epf_trans.month < 12 else 1), 1) - datetime.timedelta(1)).strftime(format)
        
            if epf_trans.entry_type == 'CR':
                add_or_create(epf_trans.trans_date.year, 'EPF', contrib, deduct, total, epf_trans.employer_contribution + epf_trans.employee_contribution, 0, epf_trans.employer_contribution + epf_trans.employee_contribution+ epf_trans.interest_contribution)
            else:
                add_or_create(epf_trans.trans_date.year, 'EPF', contrib, deduct, total, 0, -1*(epf_trans.employer_contribution + epf_trans.employee_contribution), -1*(epf_trans.employer_contribution + epf_trans.employee_contribution+ epf_trans.interest_contribution))
    
    for ssy_obj in Ssy.objects.filter(goal=goal_id):
        for ssy_trans in SsyEntry.objects.filter(number=ssy_obj):
            if ssy_trans.interest_component:
                if ssy_trans.entry_type == 'CR':
                    add_or_create(ssy_trans.trans_date.year, 'SSY', contrib, deduct, total, 0, 0, ssy_trans.amount)
                else:
                    add_or_create(ssy_trans.trans_date.year, 'SSY', contrib, deduct, total, 0, 0, -1*ssy_trans.amount)
            else:
                if ssy_trans.entry_type == 'CR':
                    add_or_create(ssy_trans.trans_date.year, 'SSY', contrib, deduct, total, ssy_trans.amount, 0, ssy_trans.amount)
                else:
                    add_or_create(ssy_trans.trans_date.year, 'SSY', contrib, deduct, total, 0, -1*ssy_trans.amount, -1*ssy_trans.amount)
    
    for espp_obj in Espp.objects.filter(goal=goal_id):
        add_or_create(espp_obj.purchase_date.year, 'ESPP', contrib, deduct, total, espp_obj.total_purchase_price, 0, 0)
        end_year = datetime.datetime.now().year
        if espp_obj.sell_date:
            end_year = espp_obj.sell_date.year - 1
            add_or_create(espp_obj.sell_date.year, 'ESPP', contrib, deduct, total, 0, -1*espp_obj.total_sell_price, 0)
        for i in range (espp_obj.purchase_date.year, end_year):
            end_date = datetime.datetime.now()
            if i != datetime.datetime.now().year:
                end_date = datetime.date.datetime.strptime(str(i)+'-12-31', '%Y-%m-%d')
            year_end_value = get_historical_stock_price_based_on_symbol(espp_obj.symbol, espp_obj.exchange, end_date+relativedelta(days=-5), end_date)
            if year_end_value is not None:
                conv_rate = 1
                if espp_obj.exchange == 'NASDAQ' or espp_obj.exchange == 'NYSE':
                    conv_val = get_conversion_rate('USD', 'INR', end_date)
                    if conv_val:
                        conv_rate = conv_val
                year_end_value = year_end_value*conv_rate
                add_or_create(espp_obj.sell_date.year, 'ESPP', contrib, deduct, total, 0, 0, year_end_value)
    print("total", total)
    sorted_years = sorted (contrib.keys(), reverse=True)
    for i, val in enumerate(sorted_years):
        if i != len(sorted_years)-1:
            for j in range (i+1, len(sorted_years)):
                print("val", val, " j", j, " sorted_years[j]", sorted_years[j])
                total[val]['PPF'] = total[val].get('PPF', 0) + total[sorted_years[j]].get('PPF', 0)
                total[val]['EPF'] = total[val].get('EPF', 0) + total[sorted_years[j]].get('EPF', 0)
                total[val]['SSY'] = total[val].get('SSY', 0) + total[sorted_years[j]].get('SSY', 0)

    print('contrib', contrib)
    print('deduct', deduct)
    print('total', total)
    colormap = {'EPF':'#f15664','ESPP':'#DC7633','FD':'#006f75','PPF':'#92993c','SSY':'#f9c5c6','RSU':'#AA12E8','Shares':'#e31219', 'MutualFunds':'#bfff00'}
    data = dict()
    data['labels'] = list()
    data['datasets'] = list()
    for i in sorted (contrib.keys()):
        data['labels'].append(str(i))
    print('data at 218', data)
    for val in ['PPF', 'EPF', 'SSY', 'ESPP']:
        entry = dict()
        entry['label'] = val+' contribution'
        entry['type'] = 'bar'
        entry['stack'] = 'contribution'
        entry['backgroundColor'] = colormap[val]
        entry['data'] = list()
        for i in sorted (contrib.keys()):
            entry['data'].append(contrib[i].get(val,0))
        data['datasets'].append(entry)
    print('data at 229', data)
    for val in ['PPF', 'EPF', 'SSY', 'ESPP']:
        entry = dict()
        entry['label'] = val+ ' deduction'
        entry['type'] = 'bar'
        entry['stack'] = 'deduction'
        entry['backgroundColor'] = colormap[val]
        entry['data'] = list()
        for i in sorted (contrib.keys()):
            entry['data'].append(deduct[i].get(val,0))
        data['datasets'].append(entry)
    print('data at 240', data)
    
    for val in ['PPF', 'EPF', 'SSY', 'ESPP']:
        entry = dict()
        entry['label'] = val + ' total'
        entry['type'] = 'bar'
        entry['stack'] = 'total'
        entry['backgroundColor'] = colormap[val]
        entry['data'] = list()
        for i in sorted (contrib.keys()):
            entry['data'].append(total[i].get(val,0))
        data['datasets'].append(entry)

    print('data at 252', data)
    return data

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

def get_shares_amount_for_user(user_id):
    share_objs = Share.objects.filter(user=user_id)
    total_shares = 0
    for share_obj in share_objs:
        if share_obj.latest_value:
            total_shares += share_obj.latest_value
    return total_shares

def get_mf_amount_for_user(user_id):
    mf_objs = Folio.objects.filter(user=user_id)
    total = 0
    for mf_obj in mf_objs:
        if mf_obj.latest_value:
            total += mf_obj.latest_value
    return total

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
        contrib['shares'] = int(get_shares_amount_for_user(user_id))
        contrib['mf'] = int(get_mf_amount_for_user(user_id))
        contrib['equity'] = contrib['espp']+contrib['rsu']+contrib['shares']+contrib['mf']
        contrib['debt'] = contrib['epf'] + contrib['fd'] + contrib['ppf'] + contrib['ssy']
        contrib['total'] = contrib['equity'] + contrib['debt']
        contrib['distrib_labels'] = ['EPF','ESPP','FD','PPF','SSY','RSU','Shares','MutualFunds']
        contrib['distrib_vals'] = [contrib['epf'],contrib['espp'],contrib['fd'],contrib['ppf'],contrib['ssy'],contrib['rsu'],contrib['shares'],contrib['mf']]
        contrib['distrib_colors'] = ['#f15664', '#DC7633','#006f75','#92993c','#f9c5c6','#AA12E8','#e31219','#bfff00']
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
    shares_data = list()
    mf_data = list()
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
    shares_reset_on_zero = False
    mf_reset_on_zero = False
    total_reset_on_zero = False

    share_qty = dict()
    mf_qty = dict()
    
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

        share_transactions = Transactions.objects.filter(trans_date__range=(data_start_date, data_end_date))
        for trans in share_transactions:
            uni_name = trans.share.exchange+'-'+trans.share.symbol
            if uni_name not in share_qty:
                share_qty[uni_name] = 0
            if trans.trans_type == 'Buy':
                share_qty[uni_name] += trans.quantity
            else:
                share_qty[uni_name] -= trans.quantity
        share_val = 0
        if data_start_date.year == 2020:
            print(share_qty)
        for s,q in share_qty.items():
            stock_obj = add_common_stock(exchange=s[0:s.find('-')], symbol=s[s.find('-')+1:], start_date=data_end_date)
            if stock_obj:
                historical_stock_prices = get_historical_stock_price(stock_obj, data_end_date+relativedelta(days=-5), data_end_date)
                for val in historical_stock_prices:
                    found = False
                    #print(val)
                    for k,v in val.items():
                        if stock_obj.exchange == 'NYSE' or stock_obj.exchange == 'NASDAQ':
                            conv_val = get_conversion_rate('USD', 'INR', data_end_date)
                            #print('conversion value', conv_val)
                            if conv_val:
                                share_val += float(conv_val)*float(v)*int(q)
                                found = True
                                break
                        else:
                            share_val += float(v)*int(q)
                            found = True
                            break
                    if found:
                        break
        if share_val != 0:
            if not shares_reset_on_zero:
                shares_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            shares_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':int(share_val)})
            total += share_val
            shares_reset_on_zero = True
        elif shares_reset_on_zero:
            shares_reset_on_zero = False
            shares_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})
        
        folio_transactions = MutualFundTransaction.objects.filter(trans_date__range=(data_start_date, data_end_date))
        for trans in folio_transactions:
            uni_name = trans.folio.fund.code
            if uni_name not in mf_qty:
                mf_qty[uni_name] = 0
            if trans.trans_type == 'Buy':
                mf_qty[uni_name] += trans.units
            else:
                mf_qty[uni_name] -= trans.units
        mf_val = 0
        if data_start_date.year == 2020:
            print(mf_qty)
        for s,q in mf_qty.items():
            fund_obj = MutualFund.objects.get(code=s)
            if fund_obj:
                historical_mf_prices = get_historical_mf_nav(s, data_end_date+relativedelta(days=-5), data_end_date)
                for val in historical_mf_prices:
                    found = False
                    #print(val)
                    for k,v in val.items():
                        #if stock_obj.exchange == 'NYSE' or stock_obj.exchange == 'NASDAQ':
                        #    conv_val = get_conversion_rate('USD', 'INR', data_end_date)
                            #print('conversion value', conv_val)
                        #    if conv_val:
                        #        share_val += float(conv_val)*float(v)*int(q)
                        #        found = True
                        #        break
                        #else:
                        mf_val += float(v)*int(q)
                        found = True
                        break
                    if found:
                        break
        if mf_val != 0:
            if not mf_reset_on_zero:
                mf_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            mf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':int(mf_val)})
            total += mf_val
            mf_reset_on_zero = True
        elif mf_reset_on_zero:
            mf_reset_on_zero = False
            mf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})
        
        if total != 0:
            if not total_reset_on_zero:
                total_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            total_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':int(total)})
            total_reset_on_zero = True
        elif total_reset_on_zero:
            total_reset_on_zero = False
            total_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})

        data_start_date  = data_start_date+relativedelta(months=+1)
    #print('shares data is:',shares_data)
    return {'ppf':ppf_data, 'epf':epf_data, 'ssy':ssy_data, 'fd': fd_data, 'espp': espp_data, 'rsu':rsu_data, 'shares':shares_data, 'mf':mf_data, 'total':total_data}
        

