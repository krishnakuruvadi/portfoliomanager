from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

TRANSACTION_TYPE_CHOICES = [
    ('Buy', 'Buy'),
    ('Sell', 'Sell'),
    ('Receive', 'Receive'),
    ('Send', 'Send')
]

# Create your models here.
class Crypto(models.Model):
    class Meta:
        unique_together = (('symbol', 'user'),)
    user = models.IntegerField(null=False)
    notes = models.CharField(max_length=80, null=True, blank=True)
    goal = models.IntegerField(null=True, blank=True)
    symbol = models.CharField(max_length=20)
    units = models.DecimalField(max_digits=30, decimal_places=10, null=True, blank=True)
    buy_price = models.DecimalField(_('Buy Price'), max_digits=30, decimal_places=6)
    buy_value = models.DecimalField(_('Buy Value'), max_digits=30, decimal_places=6)
    latest_conversion_rate =  models.DecimalField(_('Latest Conversion Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_price = models.DecimalField(_('Latest Price'), max_digits=30, decimal_places=6, default=0)
    latest_value = models.DecimalField(_('Latest Value'), max_digits=30, decimal_places=6, default=0)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    unrealised_gain = models.DecimalField(_('Unrealised Gain'), max_digits=30, decimal_places=6, default=0)
    realised_gain = models.DecimalField(_('Realised Gain'), max_digits=30, decimal_places=6, default=0)
    xirr = models.DecimalField(_('XIRR'), max_digits=20, decimal_places=2, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("crypto:crypto-detail", kwargs={'id': self.id})

class Transaction(models.Model):
    class Meta:
        unique_together = (('crypto', 'trans_date', 'price','units', 'trans_type', 'broker'),)

    crypto = models.ForeignKey('Crypto',on_delete=models.CASCADE)
    trans_date = models.DateField(_('Transaction Date'), )
    trans_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    units = models.DecimalField(max_digits=30, decimal_places=10, null=False)
    price = models.DecimalField(_('Price'), max_digits=30, decimal_places=6, null=False, blank=False)
    conversion_rate = models.DecimalField(_('Conversion Rate'), max_digits=20, decimal_places=2, default=1)
    trans_price = models.DecimalField(_('Total Price'), max_digits=20, decimal_places=6, default=0)    
    notes = models.CharField(max_length=80, null=True, blank=True)
    broker = models.CharField(max_length=20, blank=True, null=True)
    buy_currency = models.CharField(max_length=3, default='USD')
    fees = models.DecimalField(_('Fees'), max_digits=20, decimal_places=6, default=0)    

    def get_absolute_url(self):
        return reverse('crypto:transaction-detail', args=[str(self.crypto.id),str(self.id)])

    def __str__(self):
        return str(self.crypto.symbol) + " : " + str(self.trans_date) + ", " + str(self.trans_price)