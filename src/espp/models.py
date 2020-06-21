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
    sell_date = models.DateField(_('Sell Date'), blank=True, null=True)
    sell_price = models.DecimalField(_('Sell Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    sell_conversion_rate = models.DecimalField(_('Sell Conversion Rate'), max_digits=20, decimal_places=2, null=True, blank=True)
    total_sell_price = models.DecimalField(_('Total Sell Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    user = models.CharField(max_length=20)
    goal = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    latest_conversion_rate =  models.DecimalField(_('Latest Conversion Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_price = models.DecimalField(_('Latest Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_value = models.DecimalField(_('Latest Value'), max_digits=20, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    gain = models.DecimalField(_('Gain'), max_digits=20, decimal_places=2, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("espps:espp-detail", kwargs={'id': self.id})

