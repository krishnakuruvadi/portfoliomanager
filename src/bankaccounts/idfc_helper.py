from django.db.utils import IntegrityError
from .models import BankAccount, Transaction
from shared.utils import get_date_or_none_from_string, get_float_or_zero_from_string

# extract tables from pdf using camelot
def parse_pdf(full_file_path, passwd):
    trans = list()
    try:
        import camelot
    
        # extract all the tables in the PDF file
        tables = camelot.read_pdf(filepath=full_file_path, password=passwd)
        for table in tables:
            # get the table as dict
            det = table.df.to_dict()
            if 'Withdrawals' in det[4][0]:
                count = det[0].keys()
                for i in range(2, len(count)):
                    # change string of format '04 Apr 22' to date object
                    dt = get_date_or_none_from_string(det[1][i], '%d %b %y')
                    if not dt:
                        dt = get_date_or_none_from_string(det[1][i], '%d%b%y')
                    amount = 0
                    trans_type = 'Credit'
                    if det[4][i] != '':
                        trans_type = 'Debit'
                        amount = round(get_float_or_zero_from_string(det[4][i].replace(',', '')), 2)
                    else:
                        amount = round(get_float_or_zero_from_string(det[5][i].replace(',', '')), 2)
                    cat = None
                    desc = det[2][i].replace('\n', ' ')
                    if 'FD ' in desc:
                        cat = 'Investment'
                    if 'interest credit' in desc.lower():
                        cat = 'Interest'
                    trans.append(
                        {
                            'date': dt,
                            'amount': amount,
                            'trans_type': trans_type,
                            'description': desc,
                            'tran_id':det[0][i],
                            'category': cat
                        }
                    )
    except Exception as ex:
        print(f'exception while getting transactions from pdf {ex}')
    print(f'returning transactions {trans}')
    return trans


def upload_transactions(full_file_path, ba, passwd):
    transactions = parse_pdf(full_file_path, passwd)
    updated = 0
    added = 0
    exists = 0
    for transaction in transactions:
        try:
            t = Transaction.objects.get(account=ba,
                trans_date=transaction['date'],
                trans_type=transaction['trans_type'],
                amount=transaction['amount'],
                description=transaction['description'],
                tran_id=None
            )
            t.tran_id = transaction['tran_id']
            t.save()
            updated += 1
            continue
        except Transaction.DoesNotExist:
            pass

        try:
            t = Transaction.objects.get(account=ba,
                trans_date=transaction['date'],
                trans_type=transaction['trans_type'],
                amount=transaction['amount'],
                description=transaction['description'],
                tran_id=transaction['tran_id']
            )
            exists += 1
            continue
        except Transaction.DoesNotExist:
            pass

        print(f"transaction with {transaction['date']}, {transaction['trans_type']}, {transaction['amount']}, {transaction['description']} does not exist")
        try:
            t = Transaction.objects.create(account=ba,
                trans_date=transaction['date'],
                trans_type=transaction['trans_type'],
                amount=transaction['amount'],
                description=transaction['description'],
                category=transaction['category'],
                tran_id=transaction['tran_id']
            )
            added += 1
        except IntegrityError as ie:
            print(f'error {ie} when adding transaction {transaction.date} {transaction.amount}')
    print(f'added {added} updated {updated} exists {exists}')