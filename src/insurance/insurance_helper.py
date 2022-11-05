from dateutil.relativedelta import relativedelta
from django.db.utils import IntegrityError
from .models import InsurancePolicy, Transaction, Fund, NAVHistory
from shared.financial import xirr
from tools.ICICIPruLife import ICICIPruLife

def update_policies():
    for policy in InsurancePolicy.objects.all():
        update_policy_val(policy)

def update_policy_val_using_policy_num(policy_num):
    try:
        p = InsurancePolicy.objects.get(policy=policy_num)
        update_policy_val(p)
    except InsurancePolicy.DoesNotExist:
        print(f'insurance policy with number {policy_num} not found')

def update_policy_val(policy):
    if policy.policy_type != 'ULIP':
        return
    cash_flows = list()
    summary = dict()
    for trans in Transaction.objects.filter(policy=policy):
        if not trans.fund.name in summary:
            summary[trans.fund.name] = dict()
        if trans.trans_type == 'Premium':
            summary[trans.fund.name]['premium'] = summary[trans.fund.name].get('premium', 0) + trans.trans_amount
            summary[trans.fund.name]['units'] = summary[trans.fund.name].get('units', 0) + trans.units
            cash_flows.append((trans.trans_date, -1*float(trans.trans_amount)))
            if 'nav_date' not in summary[trans.fund.name] or summary[trans.fund.name]['nav_date'] < trans.trans_date:
                summary[trans.fund.name]['nav_date'] = trans.trans_date
                summary[trans.fund.name]['nav'] = trans.nav
        elif trans.trans_type in ['PolicyAdminCharges', 'OtherCharges']:
            summary[trans.fund.name]['charges'] = summary[trans.fund.name].get('charges', 0) + trans.trans_amount
        elif trans.trans_type in ['CentralGST', 'StateGST', 'OtherTaxes']:
            summary[trans.fund.name]['taxes'] = summary[trans.fund.name].get('taxes', 0) + trans.trans_amount
        elif trans.trans_type == 'OtherCredits':
            summary[trans.fund.name]['units'] = summary[trans.fund.name].get('units', 0) + trans.units
            if 'nav_date' not in summary[trans.fund.name] or summary[trans.fund.name]['nav_date'] < trans.trans_date:
                summary[trans.fund.name]['nav_date'] = trans.trans_date
                summary[trans.fund.name]['nav'] = trans.nav
        elif trans.trans_type == 'OtherDeductions':
            summary[trans.fund.name]['units'] = summary[trans.fund.name].get('units', 0) + trans.units
            if 'nav_date' not in summary[trans.fund.name] or summary[trans.fund.name]['nav_date'] < trans.trans_date:
                summary[trans.fund.name]['nav_date'] = trans.trans_date
                summary[trans.fund.name]['nav'] = trans.nav
        elif trans.trans_type == 'MortalityCharges':
            summary[trans.fund.name]['mc'] = summary[trans.fund.name].get('mc', 0) + trans.trans_amount

    print(summary)

    for fund_name, summ in summary.items():
        f = Fund.objects.get(policy=policy, name=fund_name)
        update_fund(policy, f, summ)
    
    as_on_date = None
    premium = 0
    latest_value = 0
    mc = 0
    taxes = 0
    charges = 0
    for fund in Fund.objects.filter(policy=policy):
        if not as_on_date:
            as_on_date = fund.nav_date
        elif as_on_date > fund.nav_date:
            as_on_date = fund.nav_date
        premium += float(summary[fund.name]['premium'])
        latest_value += float(fund.nav*fund.units)
        mc += float(summary[fund.name].get('mc', 0))
        taxes += float(summary[fund.name].get('taxes', 0))
        charges += float(summary[fund.name].get('charges', 0))
    gain = latest_value - premium

    policy.gain = gain
    policy.as_on_date = as_on_date
    policy.buy_value = premium
    policy.latest_value = latest_value
    cash_flows.append((policy.as_on_date, latest_value))
    print(f'cash flows for {policy.policy} {cash_flows}')
    roi = xirr(cash_flows, 0.1)*100
    policy.roi = roi
    policy.mortality_charges = mc
    policy.taxes = taxes
    policy.charges = charges
    policy.save()


def update_fund(policy, fund, summ):
    if policy.company == 'ICICI Prudential Life Insurance Co. Ltd.':
        ipl = ICICIPruLife()
        res = ipl.get_fund_details(fund.code)
        if res:
            try:
                NAVHistory.objects.create(
                                            fund=fund,
                                            nav_value=res['nav'],
                                            nav_date=res['nav_date']
                                        )
            except IntegrityError as ex:
                print(f'exception {ex} when adding NAV to history')
            try:
                fund.nav_date = res['nav_date']
                fund.nav = res['nav']
                fund.fund_type = res['asset_class']
                fund.return_1d = res.get('1D', None)
                fund.return_1w = res.get('1W', None)
                fund.return_1m = res.get('1M', None)
                fund.return_3m = res.get('3M', None)
                fund.return_6m = res.get('6M', None)
                fund.return_1y = res.get('1Y', None)
                fund.return_3y = res.get('3Y', None)
                fund.return_5y = res.get('5Y', None)
                fund.return_10y = res.get('10Y', None)
                fund.return_15y = res.get('15Y', None)
                fund.return_incep = res.get('inception', None)
                fund.return_ytd = res.get('YTD', None)
                fund.save()
            except Exception as ex:
                print(f'exception {ex} when updating fund details')
                
        nh = NAVHistory.objects.filter(fund=fund).order_by('nav_date')
        if len(nh) == 0 or nh[0].nav_date < summ['nav_date']:
            fund.nav_date =  summ['nav_date']
            fund.nav = summ['nav']
        else:
            fund.nav_date =  nh[0].nav_date
            fund.nav = nh[0].nav
        fund.units = summ['units']
        fund.save()
    else:
        print(f'unsupported fund update yet for company {policy.company}')

def get_historical_nav(fund, dt):
    nh = NAVHistory.objects.filter(fund=fund, nav_date__lte=dt, nav_date__gte=dt+relativedelta(days=-5)).order_by('nav_date')
    if len(nh) >0:
        return {'date':nh[0].nav_date, 'nav':nh[0].nav_value}
    
    if fund.policy.company == 'ICICI Prudential Life Insurance Co. Ltd.':
        try:
            ipl = ICICIPruLife()
            res = ipl.get_historical_nav(fund.code, dt)
            if res:
                NAVHistory.objects.create(fund=fund, nav_value=res['nav'], nav_date=res['date'])
                return {'date':res['date'], 'nav':res['nav']}
        except Exception as ex:
            print(f'exception adding nav to history {res} {ex}')

    return None, None
