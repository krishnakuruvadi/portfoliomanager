from .models import InsurancePolicy, Transaction, Fund, NAVHistory
from shared.financial import xirr

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
        nh = NAVHistory.objects.filter(fund=f).order_by('nav_date')
        if len(nh) == 0 or nh[0].nav_date < summ['nav_date']:
            f.nav_date =  summ['nav_date']
            f.nav = summ['nav']
        else:
            f.nav_date =  nh[0].nav_date
            f.nav = nh[0].nav
        f.units = summ['units']
        f.save()
    
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
