from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from solo.models import SingletonModel

# Create your models here.

EXCHANGE_CHOICES = [
    ('NASDAQ', 'NASDAQ'),
    ('NYSE', 'NYSE'),
    ('BSE', 'BSE'),
    ('NSE', 'NSE'),
    ('NSE/BSE', 'NSE/BSE'),
]

CAPITALISATION_CHOICES = [
    ('Large-Cap','Large-Cap'),
    ('Mid-Cap','Mid-Cap'),
    ('Small-Cap','Small-Cap'),
    ('Micro-Cap','Micro-Cap'),
]

class Bonusv2(models.Model):
    class Meta:
        unique_together = (('stock', 'announcement_date'),)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    ratio_num = models.DecimalField( max_digits=20, decimal_places=2, null=False)
    ratio_denom = models.DecimalField( max_digits=20, decimal_places=2, null=False)
    announcement_date = models.DateField(null=False)
    record_date = models.DateField(null=False)
    ex_date = models.DateField(null=False)

    def __str__(self):
        return self.stock.symbol + '/' + self.stock.exchange + ': ' + self.stock.isin + ' on ' + str(self.announcement_date)

class Splitv2(models.Model):
    class Meta:
        unique_together = (('stock', 'announcement_date'),)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    old_fv = models.DecimalField( max_digits=20, decimal_places=2, null=False)
    new_fv = models.DecimalField( max_digits=20, decimal_places=2, null=False)
    announcement_date = models.DateField(null=False)    
    ex_date = models.DateField(null=False)

    def __str__(self):
        return self.stock.symbol + '/' + self.stock.exchange + ': ' + self.stock.isin + ' on ' + str(self.announcement_date)

class Dividendv2(models.Model):
    class Meta:
        unique_together = (('stock', 'announcement_date'),)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    announcement_date = models.DateField(null=False)
    ex_date = models.DateField(null=False)
    
    def __str__(self):
        return self.stock.symbol + '/' + self.stock.exchange + ': ' + self.stock.isin + str(self.amount) + ' on ' + str(self.announcement_date)
    
class Stock(models.Model):
    class Meta:
        unique_together = (('exchange','symbol'),)
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES)
    symbol = models.CharField(max_length=20)
    isin = models.CharField(max_length=20, default='')
    collection_start_date = models.DateField(_('Collection Start Date'), )
    capitalisation = models.CharField(max_length=15, choices=CAPITALISATION_CHOICES, null=True, blank=True)
    industry = models.CharField(max_length=50, null=True, blank=True)
    etf = models.BooleanField(default=False)
    
    def get_absolute_url(self):
        return reverse("common:stock-detail", kwargs={'id': self.id})
    
    def __str__(self):
        return str(self.id) + ":" + self.exchange + ":" + self.symbol


class HistoricalStockPrice(models.Model):
    class Meta:
        unique_together = (('symbol','date'),)
    symbol = models.ForeignKey('Stock', on_delete=models.CASCADE)
    date = models.DateField(_('Date'), )
    price = models.DecimalField(_('Price'), max_digits=20, decimal_places=2, null=False)
    #face_value = models.DecimalField(_('Face Value'), max_digits=20, decimal_places=2, null=False)
    def __str__(self):
        return str(self.id) + ":" + self.symbol.exchange + ":" + self.symbol.symbol + " " + self.date + " " + self.price


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
    
    def __str__(self):
        return str(self.id) + ":" + self.code + ":" + self.name

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

class ScrollData(models.Model):
    scrip = models.CharField(max_length=100, blank=False, null=False, unique=True)
    val = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    change = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    percent = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    last_updated = models.DateTimeField()
    display = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id) + ":" + self.scrip

class Preferences(SingletonModel):
    timezone = models.CharField(max_length=100, default='Asia/Kolkata')
    indexes_to_scroll = models.CharField(max_length=20000, null=True, blank=True)
    document_backup_locn = models.CharField(max_length=20000, null=True, blank=True)


class Passwords(models.Model):
    class Meta:
        unique_together = (('user','user_id','source'),)
    user = models.IntegerField()
    user_id = models.CharField(max_length=50)
    #password = models.CharField(max_length=50)
    #additional_password = models.CharField(max_length=50)
    password = models.BinaryField()
    additional_password = models.BinaryField(null=True)
    additional_input = models.CharField(max_length=50)
    source = models.CharField(max_length=50)
    last_updated = models.DateField()
    notes = models.CharField(max_length=40, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("common:password-detail", kwargs={'id': self.id})