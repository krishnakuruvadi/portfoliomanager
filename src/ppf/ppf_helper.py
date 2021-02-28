from .ppf_sbi_xls import PpfSbiHelper
from .models import PpfEntry, Ppf
from django.db import IntegrityError
from shared.financial import xirr
import datetime

def ppf_add_transactions(bank, file_locn):
    if bank == 'SBI':
        ppf_sbi_helper = PpfSbiHelper(file_locn)
        for trans in ppf_sbi_helper.get_transactions():
            print("trans is", trans)
            insert_ppf_trans_entry(
                trans["ppf_number"], trans["trans_date"], trans["type"], trans["amount"], trans["notes"],  trans["reference"], 
                trans["interest_component"])


def insert_ppf_trans_entry(ppf_number, date, trans_type, amount, notes, reference, interest_component):
    try:
        ppf_obj = Ppf.objects.get(number=ppf_number)
        PpfEntry.objects.create(number=ppf_obj, trans_date=date, entry_type=trans_type,
                                notes=notes, reference=reference, amount=amount, interest_component=interest_component)
    except Ppf.DoesNotExist:
        print("Couldnt find ppf object with number ", ppf_number)
    except IntegrityError:
        print('Transaction exists')


    '''
    number = models.ForeignKey('Ppf', on_delete=models.CASCADE)
    trans_date = models.DateField()
    notes = models.CharField(max_length=40)
    reference = models.CharField(max_length=20)
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPE_CHOICES, default=CREDIT)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    interest_component = models.BooleanField()
    '''

def get_ppf_details(number):
    try:
        ppf_obj = Ppf.objects.get(number=number)
        total = 0
        interest = 0
        principal = 0
        cash_flows = list()
        ppf_num = ppf_obj.number
        ppf_trans = PpfEntry.objects.filter(number=ppf_num).order_by('trans_date')
        for entry in ppf_trans:
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
        return {'number': ppf_num, 'total': total, 'principal':principal, 'interest':interest, 'roi':roi}
    except Ppf.DoesNotExist:
        return None