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
    goal = models.IntegerField(null=True, blank=True)
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
    shares_for_sale = models.DecimalField(_('Available For Sell At Vest'), max_digits=20, decimal_places=0, null=False)
    conversion_rate =  models.DecimalField(_('Conversion Price'), max_digits=20, decimal_places=2, default=1)
    total_aquisition_price = models.DecimalField(_('Total Aquisition Price'), max_digits=20, decimal_places=2, null=False)
    notes = models.CharField(max_length=80, null=True, blank=True)
    unsold_shares = models.DecimalField(_('Unsold Quantity'), max_digits=20, decimal_places=0, default=0)
    latest_conversion_rate =  models.DecimalField(_('Latest Conversion Price'), max_digits=20, decimal_places=2, default=1)
    latest_price = models.DecimalField(_('Latest Price'), max_digits=20, decimal_places=2, null=True, blank=True)
    latest_value = models.DecimalField(_('Latest Value'), max_digits=20, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), blank=True, null=True)
    realised_gain = models.DecimalField(_('Realised Gain'), max_digits=20, decimal_places=2, default=0)
    unrealised_gain = models.DecimalField(_('Unrealised Gain'), max_digits=20, decimal_places=2, default=0)
    tax_at_vest = models.DecimalField(_('Tax at Vest'), max_digits=20, decimal_places=2, default=0)


    def get_absolute_url(self):
        return reverse("rsus:rsu-vest-detail", kwargs={'id': self.id})

class RSUSellTransactions(models.Model):
    class Meta:
        unique_together = (('rsu_vest', 'trans_date'))
    rsu_vest = models.ForeignKey('RestrictedStockUnits', on_delete=models.CASCADE)
    trans_date = models.DateField(_('Transaction Date'), null=False, blank=False)
    price = models.DecimalField(_('Price'), max_digits=20, decimal_places=4, null=False, blank=False)
    units = models.DecimalField(max_digits=20, decimal_places=4, null=False, blank=False)
    conversion_rate = models.DecimalField(_('Conversion Rate'), max_digits=20, decimal_places=2, default=1)
    trans_price = models.DecimalField(_('Total Price'), max_digits=20, decimal_places=4, default=0)
    realised_gain = models.DecimalField(_('Realised Gain'), max_digits=20, decimal_places=2, default=0)
    notes = models.CharField(max_length=80, null=True, blank=True)