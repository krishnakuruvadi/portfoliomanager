from .models import Epf, EpfEntry
import datetime
from shared.financial import xirr
from dateutil.relativedelta import relativedelta

def get_epf_details(number):
    try:
        epf_obj = Epf.objects.get(number=number)
        total = 0
        interest = 0
        principal = 0
        employer_contrib = 0
        employee_contrib = 0
        cash_flows = list()
        epf_trans = EpfEntry.objects.filter(epf_id=epf_obj).order_by('trans_date')
        for entry in epf_trans:
            employer_contrib += entry.employer_contribution
            employee_contrib += entry.employee_contribution
            interest += entry.interest_contribution
            principal += entry.employee_contribution + entry.employer_contribution
            cash_flows.append((entry.trans_date, -1*float(entry.employee_contribution + entry.employer_contribution)))
            if entry.withdrawl and entry.withdrawl > 0:
                principal -= entry.withdrawl
                if principal < 0:
                    interest += principal
                    principal = 0
                cash_flows.append((entry.trans_date, float(entry.withdrawl)))
        total = principal + interest
        cash_flows.append((datetime.date.today(), float(total)))
        roi = xirr(cash_flows, 0.1)*100
        roi = round(roi, 2)
        return {'number': number, 'total': total, 'employer_contrib':employer_contrib, 'employee_contrib':employee_contrib, 'interest':interest, 'roi':roi}
    except Epf.DoesNotExist:
        return None

def update_epf_vals():
    for epf_obj in Epf.objects.all():
        res = get_epf_details(epf_obj.number)
        epf_obj.employee_contribution = res['employee_contrib']
        epf_obj.employer_contribution = res['employer_contrib']
        epf_obj.interest_contribution = res['interest']
        epf_obj.total = res['total']
        epf_obj.roi = res['roi']
        epf_obj.save()



def get_summary_for_range(epf_obj, start_date, end_date):
    print(f'getting summary for {epf_obj.number} between {start_date} and {end_date}')
    start_amount = 0

    if end_date > datetime.date.today():
        end_date = datetime.date.today()

    if start_date < epf_obj.start_date:
        start_date = datetime.date(year=epf_obj.start_date.year, month=epf_obj.start_date.month, day=1)
    else:
        st = datetime.date(year=epf_obj.start_date.year, month=epf_obj.start_date.month, day=1)
        en = start_date + relativedelta(days=-1)
        contribs = EpfEntry.objects.filter(epf_id=epf_obj, trans_date__range=[st, en])
        for c in contribs:
            start_amount += round(float(c.employee_contribution + c.employer_contribution + c.interest_contribution - c.withdrawl), 2)
    
    ee_c = 0
    er_c = 0
    int_c = 0
    contribs = EpfEntry.objects.filter(epf_id=epf_obj, trans_date__range=[start_date, end_date])
    for contrib in contribs:
        ee_c += float(contrib.employee_contribution)
        er_c += float(contrib.employer_contribution)
        int_c += float(contrib.interest_contribution)
    end_amount =  start_amount +  ee_c +  er_c + int_c
    data = dict()
    data['start_amt'] = start_amount
    data['end_amount'] = end_amount
    data['employee_contrib'] = ee_c
    data['employer_contrib'] = er_c
    data['interest_contrib'] = int_c
    return data

def get_tax_for_user(user_id, start_date, end_date):
    data = dict()
    for epf_obj in Epf.objects.filter(user=user_id):
        data[epf_obj.number] = get_summary_for_range(epf_obj, start_date, end_date)
    return data
