from .ssy_sbi_xls import SsySbiHelper
from .models import SsyEntry, Ssy

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


    '''
    number = models.ForeignKey('Ssy', on_delete=models.CASCADE)
    trans_date = models.DateField()
    notes = models.CharField(max_length=40)
    reference = models.CharField(max_length=20)
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPE_CHOICES, default=CREDIT)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    interest_component = models.BooleanField()
    '''
