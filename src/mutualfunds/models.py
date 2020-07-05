from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from common.models import MutualFund

# Create your models here.

TRANSACTION_TYPE_CHOICES = [
    ('Buy', 'Buy'),
    ('Sell', 'Sell'),
]


class Folio(models.Model):
    country = models.CharField(max_length=50, default='India')
    folio = models.CharField(max_length=50)
    fund = models.ForeignKey('common.MutualFund',on_delete=models.CASCADE)
    user = models.IntegerField()
    goal = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    units = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    conversion_rate =  models.DecimalField(_('Conversion Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    buy_price = models.DecimalField(_('Buy Price'), max_digits=20, decimal_places=2)
    buy_value = models.DecimalField(_('Buy Value'), max_digits=20, decimal_places=2)
    latest_price = models.DecimalField(_('Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_value = models.DecimalField(_('Value'), max_digits=20, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    gain = models.DecimalField(_('Gain'), max_digits=20, decimal_places=2, null=True, blank=True)
    notes = models.CharField(max_length=80, null=True, blank=True)
    
    def get_absolute_url(self):
        return reverse('mutualfund:mf-summary-detail', args=[str(self.id)])

class MutualFundTransaction(models.Model):
    class Meta:
        unique_together = (('folio','trans_date','trans_type','broker'),)
    folio = models.ForeignKey('Folio',on_delete=models.CASCADE)
    trans_date = models.DateField(_('Transaction Date'), )
    trans_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    price = models.DecimalField(_('Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    units = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    conversion_rate = models.DecimalField(_('Conversion Rate'), max_digits=20, decimal_places=2, null=True, blank=True)
    trans_price = models.DecimalField(_('Total Price'), max_digits=20, decimal_places=2, null=True, blank=True)    
    broker = models.CharField(max_length=20, blank=True, null=True)
    notes = models.CharField(max_length=80, null=True, blank=True)
    
    def get_absolute_url(self):
        return reverse('mutualfund:mf-transaction-detail', args=[str(self.id)])

