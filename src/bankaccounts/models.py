from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator 

TRANSACTION_TYPE_CHOICES = [
    ('Credit', 'Credit'),
    ('Debit', 'Debit'),
]

CATEGORY_CHOICES = [
    ('Card Payment', 'Card Payment'),
    ('Interest', 'Interest'),
    ('Shopping', 'Shopping'),
    ('EMI/Loan Payment', 'EMI/Loan Payment'),
    ('Fuel', 'Fuel'),
    ('Other', 'Other'),
    ('Groceries', 'Groceries'),
    ('Rent', 'Rent'),
    ('Medical', 'Medical'),
    ('Charity', 'Charity'),
    ('Investment', 'Investment'),
    ('Child Education', 'Child Education'),
    ('Vacation', 'Vacation'),
    ('Entertainment', 'Entertainment'),
    ('Utility', 'Utility'),
    ('Gift', 'Gift'),
    ('Salary/Payment', 'Salary/Payment'),
    ('Insurance', 'Insurance'),
    ('Self Transfer', 'Self Transfer')
]

ACCOUNT_TYPE_CHOICES = [
    ('Savings', 'Savings'),
    ('Checking', 'Checking'),
    ('Current', 'Current'),
    ('HomeLoan', 'Home Loan'),
    ('CarLoan', 'Car Loan'),
    ('PersonalLoan', 'Personal Loan'),
    ('OtherLoan', 'Other Loan'),
    ('Other', 'Other')
]

# Create your models here.
class BankAccount(models.Model):
    class Meta:
        unique_together = (('number', 'bank_name'),)

    number = models.CharField(max_length=60, null=False)
    bank_name = models.CharField(max_length=60, null=False)
    currency = models.CharField(max_length=3, null=False)
    user = models.IntegerField(null=False)
    notes = models.CharField(max_length=80, null=True, blank=True)
    goal = models.IntegerField(null=True, blank=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    start_date = models.DateField(_('Start Date'), blank=True, null=True)
    acc_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='Other')

    def get_absolute_url(self):
        return reverse("bankaccounts:account-detail", kwargs={'id': self.id})

class Transaction(models.Model):
    class Meta:
        unique_together = (('account', 'trans_date', 'amount', 'trans_type', 'description', 'notes', 'tran_id'),)

    account = models.ForeignKey('BankAccount',on_delete=models.CASCADE)
    trans_date = models.DateField(_('Transaction Date'), )
    trans_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=False, validators=[MinValueValidator(0.01)])
    notes = models.CharField(max_length=80, null=True, blank=True)
    description = models.CharField(max_length=80, null=True, blank=True)
    tran_id = models.CharField(max_length=30, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('bankaccounts:transaction-detail', args=[str(self.account.id),str(self.id)])