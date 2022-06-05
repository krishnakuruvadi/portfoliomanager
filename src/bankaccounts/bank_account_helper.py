from django.db.utils import IntegrityError
from .models import BankAccount, Transaction
from ofxparse import OfxParser
import datetime
import os

def is_a_loan_account(acc_type):
    if acc_type in ['Savings', 'Checking', 'Current', 'Other']:
        return False
    return True

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

def upload_transactions(full_file_path, bank_name, file_type, acc_number, account_id, passwd):
    try:
        ba = BankAccount.objects.get(id=account_id)
        if file_type == 'QUICKEN' and full_file_path.lower().endswith("qfx"):
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
                    if 'withdrawal' in transaction.memo.lower():
                        trans_type = 'Debit'
                        
                    category = None
                    if transaction.type.lower() == 'debit':
                        trans_type = 'Debit'
                    elif transaction.type.lower() == 'credit':
                        trans_type = 'Credit'
                    
                    if transaction.type.lower() == 'int':
                        category = 'Interest'
                    elif transaction.type.lower() == 'directdep':
                        category = 'Salary/Payment'
                    if 'safeway fuel' in transaction.payee.lower():
                        category = 'Fuel'
                    elif 'etsy' in transaction.payee.lower() or 'target' in transaction.payee.lower() or 'walmart' in transaction.payee.lower() or 'costco' in transaction.payee.lower() or 'amazon' in transaction.payee.lower():
                        category = 'Shopping'
                    elif 'wholefds' in transaction.payee.lower():
                        category = 'Groceries'
                    elif 'robinhood' in transaction.payee.lower():
                        category = 'Investment'
                    elif 'pgande web' in transaction.payee.lower():
                        category = 'Utilitiy'
                    if not category:
                        print(f'unknown category {transaction.payee.lower()}')
                        category = 'Other'
                    if trans_type == 'Debit' and amount < 0:
                        amount = -1*amount
                    try:
                        t = Transaction.objects.get(account=ba,
                            trans_date=transaction.date,
                            trans_type=trans_type,
                            amount=amount,
                            description=transaction.payee,
                            category=category,
                            tran_id=None
                        )
                        
                        t.tran_id = transaction.id
                        t.save()
                    except Transaction.DoesNotExist:
                        pass
                    try:
                        Transaction.objects.create(
                            account=ba,
                            trans_date=transaction.date,
                            trans_type=trans_type,
                            amount=amount,
                            description=transaction.payee,
                            category=category,
                            tran_id=transaction.id
                        )
                    except IntegrityError as ie:
                        print(f'error {ie} when adding transaction {transaction.date} {amount}')
        else:
            if file_type == 'PDF' and bank_name == 'IDFC':
                from .idfc_helper import upload_transactions
                upload_transactions(full_file_path, ba, passwd)
            else:
                print(f'unsupported type {file_type} {bank_name} {acc_number}')
    except BankAccount.DoesNotExist:
        print(f'not uploading transactions from {full_file_path} {bank_name} since no account with number {acc_number}')
    # remove the file from disk
    os.remove(full_file_path)