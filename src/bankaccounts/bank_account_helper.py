from django.db.utils import IntegrityError
from .models import BankAccount, Transaction
from ofxparse import OfxParser
import datetime

def update_balance_for_accounts():
    for ba in BankAccount.objects.all():
        update_balance_for_account(ba.id)

def update_balance_for_account(id):
    try:
        ba = BankAccount.objects.get(id=id)
        bal = 0
        for t in Transaction.objects.filter(account=ba):
            if t.trans_type == 'Credit':
                bal += float(t.amount)
            else:
                bal -= float(t.amount)
        ba.balance = bal
        ba.as_on_date = datetime.date.today()
        ba.save()

    except BankAccount.DoesNotExist:
        print(f'No bank account with id {id} to update balance')

def upload_transactions(full_file_path, bank_name, file_type, acc_number, account_id):
    try:
        ba = BankAccount.objects.get(id=account_id)
        if file_type == 'QUICKEN':
            with open(full_file_path) as fileobj:
                ofx = OfxParser.parse(fileobj)
                account = ofx.account
                if acc_number not in account.number:
                    print(f'mismatch between account number in file.  Expected {acc_number} got {ofx.account.number}')
                    return
                statement = account.statement
                for transaction in statement.transactions:
                    #print(f'{transaction.payee}, {transaction.type}, {transaction.date}, {transaction.user_date}, {transaction.amount}, {transaction.id}, {transaction.memo}, {transaction.sic}, {transaction.mcc}, {transaction.checknum}')
                    trans_type = 'Credit'
                    amount = transaction.amount
                    print(f'type of amount in {type(amount)}')
                    if 'withdrawal' in transaction.memo.lower():
                        trans_type = 'Debit'
                        if amount < 0:
                            amount = -1*amount
                    category = None
                    if transaction.type == 'int':
                        category = 'Interest'
                    elif transaction.type == 'directdep':
                        category = 'Salary/Payment'
                    elif 'safeway fuel' in transaction.payee:
                        category = 'Fuel'
                    elif 'target' in transaction.payee or 'walmart' in transaction.payee:
                        category = 'Groceries'
                    try:
                        Transaction.objects.create(
                            account=ba,
                            trans_date=transaction.date,
                            trans_type=trans_type,
                            amount=amount,
                            description=transaction.payee,
                            category=category
                        )
                    except IntegrityError as ie:
                        print(f'error {ie} when adding transaction')
        else:
            print(f'unsupported type {file_type}')
    except BankAccount.DoesNotExist:
        print(f'not uploading transactions from {full_file_path} {bank_name} since no account with number {acc_number}')