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

class RSUAward(models.Model):
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES)
    symbol = models.CharField(max_length=20)
    user = models.IntegerField()
    goal = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    award_date = models.DateField(_('Award Date'), )
    award_id = models.CharField(max_length=20)
    shares_awarded = models.DecimalField(_('Awarded'), max_digits=20, decimal_places=0, null=False)

    def get_absolute_url(self):
        return reverse("rsus:rsu-detail", kwargs={'id': self.id})

class RestrictedStockUnits(models.Model):
    class Meta:
        unique_together = (('award','vest_date'),)
    award = models.ForeignKey('RSUAward',on_delete=models.CASCADE)
    vest_date = models.DateField(_('Vest Date'), )
    fmv = models.DecimalField(_('FMV'), max_digits=20, decimal_places=2, null=False)
    aquisition_price = models.DecimalField(_('Aquisition Price'), max_digits=20, decimal_places=2, null=False)
    shares_vested = models.DecimalField(_('Vested'), max_digits=20, decimal_places=0, null=False)
    shares_for_sale = models.DecimalField(_('Available For Sell'), max_digits=20, decimal_places=0, null=False)
    total_aquisition_price = models.DecimalField(_('Total Aquisition Price'), max_digits=20, decimal_places=2, null=False)
    sell_date = models.DateField(_('Sell Date'), blank=True, null=True)
    sell_price = models.DecimalField(_('Sell Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    sell_conversion_rate = models.DecimalField(_('Sell Conversion Rate'), max_digits=20, decimal_places=2, null=True, blank=True)
    total_sell_price = models.DecimalField(_('Total Sell Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    notes = models.CharField(max_length=80, null=True, blank=True)

    latest_conversion_rate =  models.DecimalField(_('Latest Conversion Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_price = models.DecimalField(_('Latest Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_value = models.DecimalField(_('Latest Value'), max_digits=20, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    
    def get_absolute_url(self):
        return reverse("rsus:rsu-vest-detail", kwargs={'id': self.id})
