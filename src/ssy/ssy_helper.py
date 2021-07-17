from .ssy_sbi_xls import SsySbiHelper
from .models import SsyEntry, Ssy
from django.db import IntegrityError
from shared.financial import xirr
import datetime
from ppf.ppf_sbi_pull import pull_sbi_transactions

def ssy_add_transactions(bank, file_locn):
    if bank == 'SBI':
        ssy_sbi_helper = SsySbiHelper(file_locn)
        for trans in ssy_sbi_helper.get_transactions():
            print("trans is", trans)
            insert_ssy_trans_entry(
                trans["ssy_number"], trans["trans_date"], trans["type"], trans["amount"], trans["notes"],  trans["reference"], 
                trans["interest_component"])


def insert_ssy_trans_entry(ssy_number, date, trans_type, amount, notes, reference, interest_component):
    try:
        ssy_obj = Ssy.objects.get(number=ssy_number)
        SsyEntry.objects.create(number=ssy_obj, trans_date=date, entry_type=trans_type,
                                notes=notes, reference=reference, amount=amount, interest_component=interest_component)
    except Ssy.DoesNotExist:
        print("Couldnt find ssy object with number ", ssy_number)
    except IntegrityError:
        print('Transaction exists')

    '''
    number = models.ForeignKey('Ssy', on_delete=models.CASCADE)
    trans_date = models.DateField()
    notes = models.CharField(max_length=40)
    reference = models.CharField(max_length=20)
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPE_CHOICES, default=CREDIT)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    interest_component = models.BooleanField()
    '''

def get_ssy_details(number):
    try:
        ssy_obj = Ssy.objects.get(number=number)
        total = 0
        interest = 0
        principal = 0
        cash_flows = list()
        ssy_num = ssy_obj.number
        ssy_trans = SsyEntry.objects.filter(number=ssy_num).order_by('trans_date')
        for entry in ssy_trans:
            if entry.entry_type.lower() == 'cr' or entry.entry_type.lower() == 'credit':
                if entry.interest_component:
                    interest += entry.amount
                else:
                    principal += entry.amount
                    cash_flows.append((entry.trans_date, -1*float(entry.amount)))
            else:
                principal -= entry.amount
                if principal < 0:
                    interest += principal
                    principal = 0
                cash_flows.append((entry.trans_date, float(entry.amount)))
        total = principal + interest
        cash_flows.append((datetime.date.today(), float(total)))
        roi = xirr(cash_flows, 0.1)*100
        roi = round(roi, 2)
        return {'number': ssy_num, 'total': total, 'principal':principal, 'interest':interest, 'roi':roi}
    except Ssy.DoesNotExist:
        return None

def pull_transactions(user, password, number):
    print(f'pulling transactions for SSY {number}')
    ssy_obj = Ssy.objects.get(number=number)
    return pull_sbi_transactions(user, password, number, ssy_obj.start_date)

def update_ssy_vals():
    for ssy_obj in Ssy.objects.all():
        res = get_ssy_details(ssy_obj.number)
        ssy_obj.contribution = res['principal']
        ssy_obj.interest_contribution = res['interest']
        ssy_obj.total = res['total']
        ssy_obj.roi = res['roi']
        ssy_obj.save()

