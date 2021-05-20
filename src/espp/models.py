from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


# Create your models here.

EXCHANGE_CHOICES = [
    ('NASDAQ', 'NASDAQ'),
    ('NYSE', 'NYSE'),
    ('BSE', 'BSE'),
    ('NSE', 'NSE'),
]

class Espp(models.Model):
    class Meta:
        unique_together = (('purchase_date', 'symbol'),)
    purchase_date = models.DateField(_('Purchase Date'), )
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES)
    symbol = models.CharField(max_length=20)
    subscription_fmv = models.DecimalField(_('Subscription FMV'), max_digits=20, decimal_places=2, null=False)
    purchase_fmv = models.DecimalField(_('Purchase FMV'), max_digits=20, decimal_places=2, null=False)
    purchase_price = models.DecimalField(_('Purchase Price'), max_digits=20, decimal_places=2, null=False)
    shares_purchased = models.DecimalField(_('Shares Purchased'), max_digits=20, decimal_places=0, null=False)
    purchase_conversion_rate = models.DecimalField(_('Purchase Conversion Rate'), max_digits=20, decimal_places=2, null=False)
    total_purchase_price = models.DecimalField(_('Total Purchase Price'), max_digits=20, decimal_places=2, null=False)
    shares_avail_for_sale = models.DecimalField(_('Shares Available For Sale'), max_digits=20, decimal_places=0, null=False)
    user = models.IntegerField()
    goal = models.IntegerField(null=True, blank=True)
    latest_conversion_rate =  models.DecimalField(_('Latest Conversion Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_price = models.DecimalField(_('Latest Price'), max_digits=20, decimal_places=2, default=0)
    latest_value = models.DecimalField(_('Latest Value'), max_digits=20, decimal_places=2, default=0)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    unrealised_gain = models.DecimalField(_('Unrealised Gain'), max_digits=20, decimal_places=2, default=0)
    realised_gain = models.DecimalField(_('Realised Gain'), max_digits=20, decimal_places=2, default=0)

    def get_absolute_url(self):
        return reverse("espps:espp-detail", kwargs={'id': self.id})


class EsppSellTransactions(models.Model):
    class Meta:
        unique_together = (('espp', 'trans_date'))
    espp = models.ForeignKey('Espp', on_delete=models.CASCADE)
    trans_date = models.DateField(_('Transaction Date'), )
    price = models.DecimalField(_('Price'), max_digits=20, decimal_places=4, null=False, blank=False)
    units = models.DecimalField(max_digits=20, decimal_places=4, null=False, blank=False)
    conversion_rate = models.DecimalField(_('Conversion Rate'), max_digits=20, decimal_places=2, default=1)
    trans_price = models.DecimalField(_('Total Price'), max_digits=20, decimal_places=4, default=0)
    realised_gain = models.DecimalField(_('Realised Gain'), max_digits=20, decimal_places=2, default=0)
    notes = models.CharField(max_length=80, null=True, blank=True)
