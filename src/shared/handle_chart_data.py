from ppf.models import Ppf, PpfEntry
from ssy.models import Ssy, SsyEntry
from fixed_deposit.models import FixedDeposit
from fixed_deposit.fixed_deposit_helper import get_maturity_value
from espp.models import Espp, EsppSellTransactions
from rsu.models import RSUAward, RestrictedStockUnits, RSUSellTransactions
from epf.models import Epf, EpfEntry
from goal.models import Goal
from shares.models import Share, Transactions
from mutualfunds.models import Folio, MutualFundTransaction
from users.models import User
import datetime
from dateutil.relativedelta import relativedelta
from common.models import HistoricalStockPrice, Stock, MutualFund
from shared.handle_real_time_data import get_conversion_rate, get_historical_stock_price, get_historical_mf_nav, get_historical_stock_price_based_on_symbol
from shared.handle_create import add_common_stock
from mutualfunds.models import Folio, MutualFundTransaction
from shared.financial import xirr
from retirement_401k.helper import get_401k_amount_for_goal, get_401k_amount_for_user, get_r401k_value_as_on
from shared.utils import get_min
from epf.epf_interface import EpfInterface
from espp.espp_interface import EsppInterface
from fixed_deposit.fd_interface import FdInterface
from ppf.ppf_interface import PpfInterface
from ssy.ssy_interface import SsyInterface
from shares.share_interface import ShareInterface
from mutualfunds.mf_interface import MfInterface
from retirement_401k.r401k_interface import R401KInterface
from rsu.rsu_interface import RsuInterface


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
        if espp_obj.latest_value:
            total_espp += espp_obj.latest_value
    return total_espp

def get_rsu_amount_for_goal(id):
    award_objs = RSUAward.objects.filter(goal=id)
    total_rsu = 0
    for award_obj in award_objs:
        for rsu_obj in RestrictedStockUnits.objects.filter(award=award_obj):
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
            amt += entry.employee_contribution + entry.employer_contribution + entry.interest_contribution
            amt -= entry.withdrawl
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
    contrib['distrib_labels'] = ['EPF','ESPP','FD','PPF','SSY','RSU','Shares','MutualFunds']
    contrib['distrib_vals'] = [contrib['epf'],contrib['espp'],contrib['fd'],contrib['ppf'],contrib['ssy'],contrib['rsu'],contrib['shares'],contrib['mf']]
    contrib['distrib_colors'] = ['#f15664', '#DC7633','#006f75','#92993c','#f9c5c6','#AA12E8','#e31219','#bfff00']
    contrib['401k'] = int(get_401k_amount_for_goal(goal_id))
    if contrib['401k'] > 0:
        contrib['distrib_labels'].append('401K')
        contrib['distrib_vals'].append(contrib['401k'])
        contrib['distrib_colors'].append('#617688')
        contrib['equity'] += contrib['401k']
    contrib['total'] = contrib['equity'] + contrib['debt']

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
        contrib_obj[year][key] = float(contrib) + contrib_obj[year].get(key, 0)
    if port:
        port_obj[year][key] = float(port) + port_obj[year].get(key, 0)
    if deduct: 
        deduct_obj[year][key] = float(deduct) + deduct_obj[year].get(key, 0)


def get_goal_yearly_contrib_v2(goal_id, expected_return, format='%Y-%m-%d'):
    start_day = datetime.date.today()
    start_day = get_min(EpfInterface.get_start_day_for_goal(goal_id), start_day)
    start_day = get_min(EsppInterface.get_start_day_for_goal(goal_id), start_day)
    start_day = get_min(FdInterface.get_start_day_for_goal(goal_id), start_day)
    start_day = get_min(MfInterface.get_start_day_for_goal(goal_id), start_day)
    start_day = get_min(PpfInterface.get_start_day_for_goal(goal_id), start_day)
    start_day = get_min(SsyInterface.get_start_day_for_goal(goal_id), start_day)
    start_day = get_min(ShareInterface.get_start_day_for_goal(goal_id), start_day)
    start_day = get_min(R401KInterface.get_start_day_for_goal(goal_id), start_day)
    start_day = get_min(RsuInterface.get_start_day_for_goal(goal_id), start_day)

    new_start_day = datetime.date(start_day.year, start_day.month, 1)
    
    contrib = dict()
    total = dict()
    deduct = dict()
    ret = dict()
    cash_flows = list()
    latest_value = 0
    total_contrib = 0
    # Deduction is a -ve number
    total_deduct = 0

    curr_yr = datetime.date.today().year

    for yr in range(start_day.year, curr_yr+1):
        cf, c, d, t = PpfInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, 'PPF', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding Ppf {t} latest_value is {latest_value}')


        cf, c, d, t = EpfInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, 'EPF', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding Epf {t} latest_value is {latest_value}')

        cf, c, d, t = SsyInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, 'SSY', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding Ssy {t} latest_value is {latest_value}')

        cf, c, d, t = MfInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, 'MutualFunds', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding Mf {t} latest_value is {latest_value}')

        cf, c, d, t = EsppInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, 'ESPP', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding Espp {t} latest_value is {latest_value}')

        cf, c, d, t = FdInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, 'FD', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding FD {t} latest_value is {latest_value}')

        cf, c, d, t = ShareInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, 'Shares', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding shares {t} latest_value is {latest_value}')
        
        cf, c, d, t = RsuInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, 'RSU', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding RSU {t} latest_value is {latest_value}')
    
        cf, c, d, t = R401KInterface.get_goal_yearly_contrib(goal_id, yr)
        if len(cf) > 0 or c+d+t != 0:
            add_or_create(yr, '401K', contrib, deduct, total, c, d, t)
            cash_flows.extend(cf)
        latest_value += float(t) if yr == curr_yr else 0
        total_contrib += float(c)
        total_deduct += float(d)
        if yr == curr_yr:
            print(f'after adding 401K {t} latest_value is {latest_value}')

    print(f'total_contrib {total_contrib}  total_deduct {total_deduct}  latest_value {latest_value}')
    if len(cash_flows) > 0  and latest_value != 0:
        cash_flows.append((datetime.date.today(), latest_value))
    cash_flows = sort_set(cash_flows)
    return contrib, deduct, total, latest_value, cash_flows


def get_goal_yearly_contrib(goal_id, expected_return, format='%Y-%m-%d'):
    if expected_return:
        expected_return = int(expected_return)
    print(f"inside get_goal_yearly_contrib {goal_id} {expected_return}")

    ret = dict()
    curr_yr = datetime.datetime.now().year

    '''
    contrib = dict()
    total = dict()
    deduct = dict()
    cash_flows = list()
    for ppf_obj in Ppf.objects.filter(goal=goal_id):
        for ppf_trans in PpfEntry.objects.filter(number=ppf_obj):
            #entry_date = (datetime.date(ppf_trans.year + (ppf_trans.month == 12), 
            #      (ppf_trans.month + 1 if ppf_trans.month < 12 else 1), 1) - datetime.timedelta(1)).strftime(format)
            if ppf_trans.interest_component:
                if ppf_trans.entry_type == 'CR':
                    add_or_create(ppf_trans.trans_date.year, 'PPF', contrib, deduct, total, 0, 0, ppf_trans.amount)
                else:
                    add_or_create(ppf_trans.trans_date.year, 'PPF', contrib, deduct, total, 0, 0, -1*ppf_trans.amount)
                    cash_flows.append((ppf_trans.trans_date, float(ppf_trans.amount)))
            else:
                if ppf_trans.entry_type == 'CR':
                    add_or_create(ppf_trans.trans_date.year, 'PPF', contrib, deduct, total, ppf_trans.amount, 0, ppf_trans.amount)
                    cash_flows.append((ppf_trans.trans_date, -1*float(ppf_trans.amount)))
                else:
                    add_or_create(ppf_trans.trans_date.year, 'PPF', contrib, deduct, total, 0, -1*ppf_trans.amount, -1*ppf_trans.amount)
                    cash_flows.append((ppf_trans.trans_date, float(ppf_trans.amount)))
     
    for epf_obj in Epf.objects.filter(goal=goal_id):
        for epf_trans in EpfEntry.objects.filter(epf_id=epf_obj):
        #entry_date = (datetime.date(epf_trans.year + (epf_trans.month == 12), 
        #      (epf_trans.month + 1 if epf_trans.month < 12 else 1), 1) - datetime.timedelta(1)).strftime(format)
            add_or_create(epf_trans.trans_date.year, 'EPF', contrib, deduct, total, epf_trans.employer_contribution + epf_trans.employee_contribution, epf_trans.withdrawl, epf_trans.employer_contribution + epf_trans.employee_contribution+ epf_trans.interest_contribution-epf_trans.withdrawl)
            cash_flows.append((epf_trans.trans_date, -1*float(epf_trans.employer_contribution+ epf_trans.employee_contribution)))
            if epf_trans.withdrawl and epf_trans.withdrawl > 0:
                cash_flows.append((epf_trans.trans_date, float(epf_trans.withdrawl)))

    for ssy_obj in Ssy.objects.filter(goal=goal_id):
        for ssy_trans in SsyEntry.objects.filter(number=ssy_obj):
            if ssy_trans.interest_component:
                if ssy_trans.entry_type == 'CR':
                    add_or_create(ssy_trans.trans_date.year, 'SSY', contrib, deduct, total, 0, 0, ssy_trans.amount)
                else:
                    add_or_create(ssy_trans.trans_date.year, 'SSY', contrib, deduct, total, 0, 0, -1*ssy_trans.amount)
                    cash_flows.append((ssy_trans.trans_date, float(ssy_trans.amount)))
            else:
                if ssy_trans.entry_type == 'CR':
                    add_or_create(ssy_trans.trans_date.year, 'SSY', contrib, deduct, total, ssy_trans.amount, 0, ssy_trans.amount)
                    cash_flows.append((ssy_trans.trans_date, -1*float(ssy_trans.amount)))
                else:
                    add_or_create(ssy_trans.trans_date.year, 'SSY', contrib, deduct, total, 0, -1*ssy_trans.amount, -1*ssy_trans.amount)
                    cash_flows.append((ssy_trans.trans_date, float(ssy_trans.amount)))
    
    for espp_obj in Espp.objects.filter(goal=goal_id):
        add_or_create(espp_obj.purchase_date.year, 'ESPP', contrib, deduct, total, espp_obj.total_purchase_price, 0, 0)
        end_year = datetime.datetime.now().year
        for st in EsppSellTransactions.objects.filter(espp=espp_obj):
            add_or_create(st.trans_date.year, 'ESPP', contrib, deduct, total, 0, -1*st.trans_price, 0)
            cash_flows.append((st.trans_date, float(st.trans_price)))
        cash_flows.append((espp_obj.purchase_date, -1*float(espp_obj.total_purchase_price)))
        for i in range (espp_obj.purchase_date.year, end_year+1):
            year_end_value = 0
            end_date = datetime.datetime.now()
            if i != datetime.datetime.now().year:
                end_date = datetime.datetime.strptime(str(i)+'-12-31', '%Y-%m-%d').date()
            units = espp_obj.shares_purchased
            for st in EsppSellTransactions.objects.filter(espp=espp_obj, trans_date__lte=end_date):
                units -= st.units
            
            if units > 0:
                year_end_value_vals = get_historical_stock_price_based_on_symbol(espp_obj.symbol, espp_obj.exchange, end_date+relativedelta(days=-5), end_date)
                if year_end_value_vals:
                    conv_rate = 1
                    if espp_obj.exchange == 'NASDAQ' or espp_obj.exchange == 'NYSE':
                        conv_val = get_conversion_rate('USD', 'INR', end_date)
                        if conv_val:
                            conv_rate = conv_val
                    for k,v in year_end_value_vals.items():
                        year_end_value = float(v)*float(conv_rate)*float(units)
                        break
            print(f'espp year_end_value {i} {year_end_value}')

            add_or_create(i, 'ESPP', contrib, deduct, total, 0, 0, year_end_value)

    year_end_mf = dict()

    try:
        for folio_obj in Folio.objects.filter(goal=goal_id):
            for trans in MutualFundTransaction.objects.filter(folio=folio_obj):
                trans_yr = trans.trans_date.year
                
                for yr in range(trans_yr,datetime.datetime.now().year+1,1):
                    if yr not in year_end_mf:
                        year_end_mf[yr] = dict()
                    if folio_obj.fund.code not in year_end_mf[yr]:
                        year_end_mf[yr][folio_obj.fund.code] = 0
                if trans.trans_type == 'Buy' and not trans.switch_trans:
                    add_or_create(trans.trans_date.year, 'MutualFunds',contrib, deduct, total,trans.trans_price,0,0)
                    cash_flows.append((trans.trans_date, -1*float(trans.trans_price)))
                    for yr in range(trans_yr,datetime.datetime.now().year+1,1):
                        year_end_mf[yr][folio_obj.fund.code] = year_end_mf[yr][folio_obj.fund.code]+trans.units
                elif trans.trans_type == 'Sell' and not trans.switch_trans:
                    add_or_create(trans.trans_date.year, 'MutualFunds',contrib, deduct, total,0, -1*trans.trans_price,0)
                    cash_flows.append((trans.trans_date, float(trans.trans_price)))
                    for yr in range(trans_yr,datetime.datetime.now().year+1,1):
                        year_end_mf[yr][folio_obj.fund.code] = year_end_mf[yr][folio_obj.fund.code]-trans.units
    except Exception as ex:
        print(ex)
    print('year_end_mf', year_end_mf)
    for yr,_ in year_end_mf.items():
        print('yr',yr)
        yr_data = year_end_mf[yr]
        end_date = datetime.datetime.now()
        if yr != datetime.datetime.now().year:
            end_date = datetime.datetime.strptime(str(yr)+'-12-31', '%Y-%m-%d').date()
        print('yr_data', yr_data)
        for code,qty in yr_data.items():
            historical_mf_prices = get_historical_mf_nav(code, end_date+relativedelta(days=-5), end_date)
            if len(historical_mf_prices) > 0:
                print('historical_mf_prices',historical_mf_prices)
                for k,v in historical_mf_prices[0].items():
                    add_or_create(yr, 'MutualFunds',contrib, deduct, total,0,0,v*qty)
    
    
    if len(contrib.keys()):
        for i in range (curr_yr, min(contrib.keys())-1, -1):
            print('i:', i)
            if i not in total:
                total[i] = dict()
            for j in range(i-1, min(contrib.keys())-1, -1):
                if j not in total:
                    total[j] = dict()
                print('j:', j)
                total[i]['PPF'] = total[i].get('PPF', 0) + total[j].get('PPF', 0)
                total[i]['EPF'] = total[i].get('EPF', 0) + total[j].get('EPF', 0)
                total[i]['SSY'] = total[i].get('SSY', 0) + total[j].get('SSY', 0)

    

    '''
    contrib, deduct, total, latest_value, cash_flows = get_goal_yearly_contrib_v2(goal_id, expected_return)

    total_contribution = 0
    total_years = 0
    last_yr_contrib = 0
    if len(contrib.keys()):
        for yr in range(curr_yr, min(contrib.keys())-1, -1):
            total_years += 1
            if yr in contrib:
                for _,amt in contrib[yr].items():
                    total_contribution += amt
                    if yr == datetime.date.today().year -1:
                        last_yr_contrib += amt
    
    '''
    if len(contrib.keys()):
        print('************** time for comparision ***************')
        print('Contribution:"')
        for yr in range(curr_yr, min(contrib.keys())-1, -1):
            if yr in contrib:
                print(f'{yr}: {contrib[yr]} \t {contrib2.get(yr,None)}')
        print('Deduction:"')
        for yr in range(curr_yr, min(deduct.keys())-1, -1):
            if yr in deduct:
                print(f'{yr}: {deduct[yr]} \t {deduct2.get(yr, None)}')
        print('Total:"')
        for yr in range(curr_yr, min(total.keys())-1, -1):
            if yr in total:
                print(f'{yr}: {total[yr]} \t {total2.get(yr, None)}')
        print('************** end of comparision ***************')
    '''

    #print('total @299', total)
    if total_contribution:        
        avg_contrib = total_contribution/total_years
        '''
        latest_value = 0
        for k,v in total[curr_yr].items():
            latest_value += v
        cash_flows.append((datetime.date.today(), latest_value))
        
        cash_flows = sort_set(cash_flows)
        

        if round(latest_value, 2) == round(latest_value2, 2):
            print('same latest values')
        else:
            print('different latest values')
        print('cash flows', cash_flows)
        if cash_flows == cash_flows2:
            print('same cash flows')
        else:
            print('different cash flows')
            i = 0
            while True:
                if i < len(cash_flows):
                    till = 5 if len(cash_flows) - i > 5 else len(cash_flows) - i
                    print(cash_flows[i:i+till])
                    print(cash_flows2[i:i+till])
                    i += till
                    print('')
                else:
                    break
        '''
        #calc_avg_growth = (latest_value-total_contribution)/(total_contribution*total_years)
        calc_avg_growth = None
        try:
            calc_avg_growth = xirr(cash_flows, 0.1)
        except Exception as ex:
            print(f'Exception {ex} when finding XIRR')

        if expected_return:
            avg_growth = expected_return/100
        else:
            avg_growth = calc_avg_growth
        
        goal_obj = Goal.objects.get(id=goal_id)
        goal_end_date = goal_obj.start_date+relativedelta(months=goal_obj.time_period)
        print('*************')
        ret['goal_end_date'] = goal_end_date
        if calc_avg_growth:
            ret['avg_growth'] = int(calc_avg_growth*100)
        ret['latest_value'] = latest_value
        ret['total_contribution'] = total_contribution
        ret['avg_contrib'] = int(avg_contrib)
        ret['last_yr_contrib'] = int(last_yr_contrib)
        print(ret)
        print('*************')

        for yr in range(curr_yr+1, goal_end_date.year+1):
            contrib[yr] = dict()
            total[yr] = dict()
            deduct[yr] = dict()
            contrib[yr]['Projected'] = avg_contrib
            if 'Projected' in total[yr-1]:
                total[yr]['Projected'] = (float(total[yr-1]['Projected'])+float(avg_contrib))*(1+float(avg_growth))
            else:
                total[yr]['Projected'] = (float(latest_value)+float(avg_contrib))*(1+float(avg_growth))
            deduct[yr]['Projected'] = 0
            ret['final_projection'] = int(total[yr]['Projected'])

    print('contrib', contrib)
    print('deduct', deduct)
    print('total', total)
    colormap = {'401K': '#617688', 'EPF':'#f15664','ESPP':'#DC7633','FD':'#006f75','PPF':'#92993c','SSY':'#f9c5c6','RSU':'#AA12E8','Shares':'#e31219', 'MutualFunds':'#bfff00', 'Projected':'#cbcdd1'}
    data = dict()
    data['labels'] = list()
    data['datasets'] = list()
    for i in sorted (contrib.keys()):
        data['labels'].append(str(i))
    print('data at 294', data)

    alloted_types = dict()
    for k,v in contrib.items():
        for typ, val in v.items():
            alloted_types[typ] = None


    for val in alloted_types.keys():
        centry = dict()
        centry['label'] = val+' contribution'
        centry['type'] = 'bar'
        centry['stack'] = 'contribution'
        centry['backgroundColor'] = colormap[val]
        centry['data'] = list()
        for i in sorted (contrib.keys()):
            centry['data'].append(int(contrib[i].get(val,0)))
        data['datasets'].append(centry)

        dentry = dict()
        dentry['label'] = val+ ' deduction'
        dentry['type'] = 'bar'
        dentry['stack'] = 'deduction'
        dentry['backgroundColor'] = colormap[val]
        dentry['data'] = list()
        for i in sorted (contrib.keys()):
            dentry['data'].append(deduct[i].get(val,0))
        data['datasets'].append(dentry)

        tentry = dict()
        tentry['label'] = val + ' total'
        tentry['type'] = 'bar'
        tentry['stack'] = 'total'
        tentry['backgroundColor'] = colormap[val]
        tentry['data'] = list()
        for i in sorted (contrib.keys()):
            tentry['data'].append(int(total[i].get(val,0)))
        data['datasets'].append(tentry)

    return data, ret


def sort_set(cash_flows):
    ret = list()
    done = list()
    while len(done) < len(cash_flows):
        largest = None
        largest_num = 0
        for i, flow in enumerate(cash_flows):
            if not i in done:
                if not largest:
                    largest = flow
                    largest_num = i
                else:
                    if largest[0] > flow[0]:
                        largest = flow
                        largest_num = i
                    elif largest[0] == flow[0]:
                        if largest[1] > flow[1]:
                            largest = flow
                            largest_num = i
        ret.append(largest)
        done.append(largest_num)
    return ret


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
        if espp_obj.latest_value:
            total_espp += espp_obj.latest_value
    return total_espp

def get_rsu_amount_for_user(user_id):
    award_objs = RSUAward.objects.filter(user=user_id)
    total_rsu = 0
    for award_obj in award_objs:
        for rsu_obj in RestrictedStockUnits.objects.filter(award=award_obj):
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
            amt += entry.employee_contribution + entry.employer_contribution + entry.interest_contribution - entry.withdrawl
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
        contrib['distrib_colors'] = list()
        contrib['distrib_vals'] = list()
        contrib['distrib_labels'] = list()
        contrib['target'] = int(get_goal_target_for_user(user_id))
        contrib['EPF'] = int(get_epf_amount_for_user(user_id))
        contrib['ESPP'] = int(get_espp_amount_for_user(user_id))
        contrib['FD'] = int(get_fd_amount_for_user(user_id))
        contrib['PPF'] =int(get_ppf_amount_for_user(user_id))
        contrib['SSY'] =int(get_ssy_amount_for_user(user_id))
        contrib['RSU'] = int(get_rsu_amount_for_user(user_id))
        contrib['Shares'] = int(get_shares_amount_for_user(user_id))
        contrib['MutualFunds'] = int(get_mf_amount_for_user(user_id))
        contrib['401K'] = int(get_401k_amount_for_user(user_id))
        contrib['equity'] = contrib['ESPP']+contrib['RSU']+contrib['Shares']+contrib['MutualFunds']+contrib['401K']
        contrib['debt'] = contrib['EPF'] + contrib['FD'] + contrib['PPF'] + contrib['SSY']
        contrib['total'] = contrib['equity'] + contrib['debt']
        
        item_color_mapping = {
            'EPF': '#f15664',
            'ESPP': '#DC7633',
            'FD': '#006f75',
            'PPF':'#92993c',
            'SSY':'#f9c5c6', 
            'RSU': '#AA12E8', 
            'Shares': '#e31219', 
            'MutualFunds': '#bfff00',
            '401K': '#617688'
        }
        for k,v in item_color_mapping.items():
            if contrib[k] > 0:
                contrib['distrib_vals'].append(contrib[k])
                contrib['distrib_colors'].append(v)
                contrib['distrib_labels'].append(k)

        print("contrib:", contrib)
        return contrib
    except User.DoesNotExist:
        print("User with id ", user_id, " does not exist" )
        pass
    except Exception as ex:
        print(f"Exception getting user contribution for user with id: {str(user_id)} {ex}")

# home chart view
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
    r401k_data = list()
    total_data = list()

    total_epf = 0
    total_ppf = 0
    total_ssy = 0

    epf_reset_on_zero = False
    fd_reset_on_zero = False
    r401k_reset_on_zero = False
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
        print('Calculating for the month', data_start_date)
        total = 0
        data_end_date = data_start_date + relativedelta(months=+1)
        epf_entries = EpfEntry.objects.filter(trans_date__year=data_start_date.year, trans_date__month=data_start_date.month)
        for epf_entry in epf_entries:
            total_epf += int(epf_entry.employee_contribution) + int(epf_entry.employer_contribution) + int(epf_entry.interest_contribution) - int(epf_entry.withdrawl)
        if total_epf != 0:
            if not epf_reset_on_zero:
                epf_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            epf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':total_epf})
            total += total_epf
            epf_reset_on_zero = True
        elif epf_reset_on_zero:
            epf_reset_on_zero = False
            epf_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0})
        
        ppf_entries = PpfEntry.objects.filter(trans_date__year=data_start_date.year, trans_date__month=data_start_date.month)
        for ppf_entry in ppf_entries:
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
        
        
        r401k_val = get_r401k_value_as_on(data_end_date)
        if r401k_val != 0:
            if not r401k_reset_on_zero:
                r401k_data.append({'x':data_start_date.strftime('%Y-%m-%d'),'y':0})
            r401k_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':r401k_val})
            total += r401k_val
            r401k_reset_on_zero = True
        elif r401k_reset_on_zero:
            r401k_reset_on_zero = False
            r401k_data.append({'x':data_end_date.strftime('%Y-%m-%d'),'y':0}) 

        espp_entries = Espp.objects.filter(purchase_date__lte=data_end_date)
        espp_val = 0
        for espp_entry in espp_entries:
            #print("espp entry")
            avail_units = espp_entry.shares_purchased
            for sell_trans in EsppSellTransactions.objects.filter(espp=espp_entry, trans_date__lte=data_end_date):
                avail_units -= sell_trans.units

            if avail_units > 0:
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
                                    espp_val += float(conv_val)*float(v)*float(avail_units)
                                    found = True
                                    break
                            else:
                                espp_val += float(v)*float(avail_units)
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
            su = 0
            for st in RSUSellTransactions.objects.filter(rsu_vest=rsu_entry, trans_date__lte=data_end_date):
                su += float(st.units)
            unsold_shares = float(rsu_entry.shares_for_sale) - su
            if unsold_shares > 0:
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
                                    rsu_val += float(conv_val)*float(v)*unsold_shares
                                    found = True
                                    break
                            else:
                                rsu_val += float(v)*unsold_shares
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
        if len(share_transactions) == 0:
            print(f'no transactions in shares in date range {data_start_date} and {data_end_date}')
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
                                share_val += float(conv_val)*float(v)*float(q)
                                found = True
                                break
                        else:
                            share_val += float(v)*float(q)
                            found = True
                            break
                    if found:
                        break
            else:
                print(f'couldnt create stock object {s}')
        if share_val != 0:
            print(f'share value is not zero {share_val}')
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
                    for k,v in val.items():
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
    print('shares data is:',shares_data)
    print('returning', {'ppf':ppf_data, '401K': r401k_data, 'epf':epf_data, 'ssy':ssy_data, 'fd': fd_data, 'espp': espp_data, 'rsu':rsu_data, 'shares':shares_data, 'mf':mf_data, 'total':total_data})

    return {'ppf':ppf_data, '401K': r401k_data, 'epf':epf_data, 'ssy':ssy_data, 'fd': fd_data, 'espp': espp_data, 'rsu':rsu_data, 'shares':shares_data, 'mf':mf_data, 'total':total_data}
        

