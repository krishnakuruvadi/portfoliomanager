from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

# Create your models here.

EXCHANGE_CHOICES = [
    ('NASDAQ', 'NASDAQ'),
    ('NYSE', 'NYSE'),
    ('BSE', 'BSE'),
    ('NSE', 'NSE'),
]

class Stock(models.Model):
    class Meta:
        unique_together = (('exchange','symbol'),)
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES)
    symbol = models.CharField(max_length=20)
    collection_start_date = models.DateField(_('Collection Start Date'), )
    
    def get_absolute_url(self):
        return reverse("common:stock-detail", kwargs={'id': self.id})


class HistoricalStockPrice(models.Model):
    class Meta:
        unique_together = (('symbol','date'),)
    symbol = models.ForeignKey('Stock', on_delete=models.CASCADE)
    date = models.DateField(_('Date'), )
    price = models.DecimalField(_('Price'), max_digits=20, decimal_places=2, null=False)
    #face_value = models.DecimalField(_('Face Value'), max_digits=20, decimal_places=2, null=False)


class MutualFund(models.Model):
    code = models.CharField(max_length=15) # amfi code for India
    name = models.CharField(max_length=200) # amfi name for India
    isin = models.CharField(max_length=20) # amfi isin code ISIN Div Payout/ ISIN Growth
    isin2 = models.CharField(max_length=20, null=True, blank=True) # amfi isin code ISIN Div Reinvestment
    fund_house = models.CharField(max_length=50, null=True, blank=True)
    kuvera_name = models.CharField(max_length=200, null=True, blank=True)
    collection_start_date = models.DateField(_('Collection Start Date'), )
    bse_star_name = models.CharField(max_length=200, null=True, blank=True)
    ms_name = models.CharField(max_length=200, null=True, blank=True)
    ms_id = models.CharField(max_length=20, null=True, blank=True)
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
    category = models.CharField(max_length=200, null=True, blank=True)
    investment_style = models.CharField(max_length=200, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), null=True, blank=True)
    def get_absolute_url(self):
        return reverse("common:mf-detail", kwargs={'id': self.id})

class MFCategoryReturns(models.Model):
    category = models.CharField(max_length=200, unique=True)
    return_1d_avg = models.DecimalField(_('1D Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1w_avg = models.DecimalField(_('1W Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1m_avg = models.DecimalField(_('1M Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_3m_avg = models.DecimalField(_('3M Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_6m_avg = models.DecimalField(_('6M Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1y_avg = models.DecimalField(_('1Y Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_3y_avg = models.DecimalField(_('3Y Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_5y_avg = models.DecimalField(_('5Y Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_10y_avg = models.DecimalField(_('10Y Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_15y_avg = models.DecimalField(_('15Y Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_inception_avg = models.DecimalField(_('Inception Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_ytd_avg = models.DecimalField(_('YTD Avg'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1d_top = models.DecimalField(_('1D Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1w_top = models.DecimalField(_('1W Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1m_top = models.DecimalField(_('1M Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_3m_top = models.DecimalField(_('3M Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_6m_top = models.DecimalField(_('6M Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1y_top = models.DecimalField(_('1Y Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_3y_top = models.DecimalField(_('3Y Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_5y_top = models.DecimalField(_('5Y Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_10y_top = models.DecimalField(_('10Y Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_15y_top = models.DecimalField(_('15Y Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_inception_top = models.DecimalField(_('Inception Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_ytd_top = models.DecimalField(_('YTD Top'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1d_bot = models.DecimalField(_('1D Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1w_bot = models.DecimalField(_('1W Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1m_bot = models.DecimalField(_('1M Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_3m_bot = models.DecimalField(_('3M Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_6m_bot = models.DecimalField(_('6M Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_1y_bot = models.DecimalField(_('1Y Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_3y_bot = models.DecimalField(_('3Y Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_5y_bot = models.DecimalField(_('5Y Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_10y_bot = models.DecimalField(_('10Y Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_15y_bot = models.DecimalField(_('15Y Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_inception_bot = models.DecimalField(_('Inception Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    return_ytd_bot = models.DecimalField(_('YTD Bottom'), max_digits=10, decimal_places=2, null=True, blank=True)
    as_on_date = models.DateField(_('As On Date'), null=True, blank=True)
 
    def __str__(self):
        return str(self.id)+':'+self.category

class MFYearlyReturns(models.Model):
    class Meta:
        unique_together = (('fund','year'),)
    fund = models.ForeignKey('MutualFund', on_delete=models.CASCADE)
    year = models.IntegerField()
    returns = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    diff_index = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    diff_category = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentile_rank = models.IntegerField(null=True, blank=True)
    funds_in_category = models.IntegerField(null=True, blank=True)

class HistoricalMFPrice(models.Model):
    class Meta:
        unique_together = (('code','date'),)
    code = models.ForeignKey('MutualFund', on_delete=models.CASCADE)
    date = models.DateField(_('Date'), )
    nav = models.DecimalField(_('NAV'), max_digits=20, decimal_places=2, null=False)

class HistoricalForexRates(models.Model):
    class Meta:
        unique_together = (('from_cur','to_cur','date'),)
    from_cur = models.CharField(_('From Currency'),max_length=20)
    to_cur = models.CharField(_('To Currency'),max_length=20)
    date = models.DateField(_('Date'))
    rate = models.DecimalField(_('Conversion Rate'), max_digits=20, decimal_places=2, null=False)

