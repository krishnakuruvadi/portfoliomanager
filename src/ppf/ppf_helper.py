from .ppf_sbi_xls import PpfSbiHelper
from .models import PpfEntry, Ppf

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


    '''
    number = models.ForeignKey('Ppf', on_delete=models.CASCADE)
    trans_date = models.DateField()
    notes = models.CharField(max_length=40)
    reference = models.CharField(max_length=20)
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPE_CHOICES, default=CREDIT)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    interest_component = models.BooleanField()
    '''
