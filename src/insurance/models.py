from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

# Create your models here.
POLICY_TYPE_CHOICES = [
    ('Traditional', 'Traditional'),
    ('ULIP', 'ULIP'),
    ('Term', 'Term'),
    ('Health', 'Health')
]

TRANSACTION_TYPE_CHOICES = [
    ('Premium', 'Premium'),
    ('OtherCharges', 'OtherCharges'),
    ('OtherCredits', 'OtherCredits'),
    ('PolicyAdminCharges', 'PolicyAdminCharges'),
    ('CentralGST', 'CentralGST'),
    ('StateGST', 'StateGST'),
    ('OtherDeductions', 'OtherDeductions'),
    ('MortalityCharges', 'MortalityCharges'),
    ('OtherTaxes', 'OtherTaxes')
]

class InsurancePolicy(models.Model):
    policy = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    start_date = models.DateField()
    user = models.IntegerField()
    goal =  models.IntegerField(null=True, blank=True)
    notes = models.CharField(max_length=40, null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPE_CHOICES)
    roi = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    buy_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    latest_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    gain = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    sum_assured = models.DecimalField(max_digits=20, decimal_places=0, null=True, default=0)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    mortality_charges = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    taxes = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    charges = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)

    class Meta:
        unique_together = ('policy', 'user')

    def get_absolute_url(self):
        return reverse('insurance:policy-detail', args=[str(self.id)])

class Fund(models.Model):
    policy = models.ForeignKey('InsurancePolicy', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    notes = models.CharField(max_length=40, null=True, blank=True)
    fund_type = models.CharField(max_length=40, null=True, blank=True)
    units = models.DecimalField(max_digits=20, decimal_places=6, null=True, default=0)
    nav = models.DecimalField(max_digits=20, decimal_places=6, null=True, default=0)
    nav_date = models.DateField(null=True, blank=True)
    return_1d = models.DecimalField(_('1D'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1w = models.DecimalField(_('1W'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1m = models.DecimalField(_('1M'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_3m = models.DecimalField(_('3M'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_6m = models.DecimalField(_('6M'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1y = models.DecimalField(_('1Y'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_3y = models.DecimalField(_('3Y'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_5y = models.DecimalField(_('5Y'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_10y = models.DecimalField(_('10Y'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_15y = models.DecimalField(_('15Y'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_incep = models.DecimalField(_('Inception'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_ytd = models.DecimalField(_('YTD'), max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('policy', 'name')

class Transaction(models.Model):
    policy = models.ForeignKey('InsurancePolicy', on_delete=models.CASCADE)
    fund = models.ForeignKey('Fund', on_delete=models.CASCADE, null=True, blank=True)
    trans_date = models.DateField(null=False)
    notes = models.CharField(max_length=40, blank=True)
    units = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    nav = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    trans_amount = models.DecimalField(max_digits=20, decimal_places=4)
    description = models.CharField(max_length=40)
    trans_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)

    class Meta:
        unique_together = ('policy', 'trans_date', 'trans_amount', 'description')
    
    def get_absolute_url(self):
        return reverse('insurance:transaction-detail', args=[str(self.policy.id),str(self.id)])

class NAVHistory(models.Model):
    fund = models.ForeignKey('Fund', on_delete=models.CASCADE)
    nav_value = models.DecimalField(max_digits=20, decimal_places=6)
    nav_date = models.DateField()

    class Meta:
        unique_together = ('fund', 'nav_date')
    
    def __str__(self):
        return self.fund.name+ ' ' + self.nav_date.strftime('%d-%b-%Y') + ' ' + str(self.nav_value)
