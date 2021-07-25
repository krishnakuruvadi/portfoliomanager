from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Create your models here.

EXCHANGE_CHOICES = [
    ('NASDAQ', 'NASDAQ'),
    ('NYSE', 'NYSE'),
    ('BSE', 'BSE'),
    ('NSE', 'NSE'),
    ('NSE/BSE', 'NSE/BSE')
]

TRANSACTION_TYPE_CHOICES = [
    ('Buy', 'Buy'),
    ('Sell', 'Sell'),
]

class Share(models.Model):
    class Meta:
        unique_together = (('exchange','symbol','user'),)
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES)
    symbol = models.CharField(max_length=20)
    user = models.IntegerField()
    goal = models.IntegerField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    conversion_rate =  models.DecimalField(_('Conversion Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    buy_price = models.DecimalField(_('Buy Price'), max_digits=20, decimal_places=2)
    buy_value = models.DecimalField(_('Buy Value'), max_digits=20, decimal_places=2)
    latest_price = models.DecimalField(_('Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_value = models.DecimalField(_('Value'), max_digits=20, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    gain = models.DecimalField(_('Gain'), max_digits=20, decimal_places=2, null=True, blank=True)
    notes = models.CharField(max_length=80, null=True, blank=True)
    realised_gain = models.DecimalField(_('Realised Gain'), max_digits=20, decimal_places=2, null=True, blank=True)
    etf = models.BooleanField(default=False)
    roi = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    def get_absolute_url(self):
        return reverse('shares:share-detail', args=[str(self.id)])


class Transactions(models.Model):
    class Meta:
        unique_together = (('share','trans_date','price','quantity','trans_type','broker'),)
    share = models.ForeignKey('Share',on_delete=models.CASCADE)
    trans_date = models.DateField(_('Transaction Date'), )
    trans_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    price = models.DecimalField(_('Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    conversion_rate = models.DecimalField(_('Conversion Rate'), max_digits=20, decimal_places=2, null=True, blank=True)
    trans_price = models.DecimalField(_('Total Price'), max_digits=20, decimal_places=2, null=True, blank=True)    
    broker = models.CharField(max_length=20, blank=True, null=True)
    notes = models.CharField(max_length=80, null=True, blank=True)
    div_reinv = models.BooleanField(default=False)
    
    def get_absolute_url(self):
        return reverse('shares:transaction-detail', args=[str(self.id)])
    