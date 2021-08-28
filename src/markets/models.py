from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class PEMonthy(models.Model):
    index_name = models.CharField(max_length=60)
    month = models.IntegerField(null=False)
    year = models.IntegerField(null=False)
    pe_avg = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    pe_max = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    pe_min = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        unique_together = (('index_name','month', 'year'),)

class PBMonthy(models.Model):
    index_name = models.CharField(max_length=60)
    month = models.IntegerField(null=False)
    year = models.IntegerField(null=False)
    pb_avg = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    pb_max = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    pb_min = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        unique_together = (('index_name','month', 'year'),)

class News(models.Model):
    exchange = models.CharField(max_length=60)
    symbol = models.CharField(max_length=60)
    text = models.CharField(max_length=6000)
    date = models.DateField()
    link = models.CharField(max_length=6000)
    source = models.CharField(max_length=60)

    class Meta:
        unique_together = (('exchange','symbol','text','date','source'),)

class IndexRollingReturns(models.Model):
    country = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
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
    as_on_date = models.DateField(_('As On Date'), null=True, blank=True)

    class Meta:
        unique_together = (('country', 'name'),)

class IndexYearlyReturns(models.Model):
    country = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    year = models.IntegerField(null=False)
    ret = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), null=True, blank=True)

    class Meta:
        unique_together = (('country', 'name', 'year'),)

class IndexQuarterlyReturns(models.Model):
    country = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    quarter = models.CharField(max_length=10)
    ret = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), null=True, blank=True)

    class Meta:
        unique_together = (('country', 'name', 'quarter'),)

class IndexMonthlyReturns(models.Model):
    country = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    month = models.CharField(max_length=10)
    ret = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), null=True, blank=True)

    class Meta:
        unique_together = (('country', 'name', 'month'),)
