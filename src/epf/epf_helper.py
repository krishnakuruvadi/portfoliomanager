from .models import Epf, EpfEntry
import datetime
from shared.financial import xirr

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