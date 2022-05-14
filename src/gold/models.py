from django.db import models
from django.urls import reverse

# Create your models here.

BUY_TYPE_CHOICES = [
    ('Physical', 'Physical'),
    ('Other', 'Other'),
    ('Sovereign Gold Bond Scheme', 'Sovereign Gold Bond Scheme')
]

GOLD_PURITY_CHOICES = [
    ('22K', '22K'),
    ('24K', '24K')
]

class Gold(models.Model):
    weight = models.DecimalField(max_digits=20, decimal_places=10, null=False)
    per_gm = models.DecimalField(max_digits=20, decimal_places=4, null=False)
    buy_value = models.DecimalField(max_digits=20, decimal_places=4, null=False)
    latest_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    latest_value = models.DecimalField(max_digits=200, decimal_places=4, null=True, blank=True)
    buy_date = models.DateField(null=False)
    as_on_date = models.DateField(null=True, blank=True)
    user = models.IntegerField(null=False)
    notes = models.CharField(max_length=80, null=True, blank=True)
    goal = models.IntegerField(null=True, blank=True)
    roi = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    buy_type = models.CharField(max_length=50, choices=BUY_TYPE_CHOICES)
    realised_gain = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    unrealised_gain = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    unsold_weight = models.DecimalField(max_digits=20, decimal_places=10, null=False)
    purity = models.CharField(max_length=10, choices=GOLD_PURITY_CHOICES, default='24K')

    def get_absolute_url(self):
        return reverse("gold:gold-detail", kwargs={'id': self.id})

    class Meta:
        unique_together = ('buy_date', 'user', 'buy_type', 'weight')

class SellTransaction(models.Model):
    buy_trans = models.ForeignKey('Gold', on_delete=models.CASCADE)
    trans_date = models.DateField(null=False)
    notes = models.CharField(max_length=40, null=True, blank=True)
    weight = models.DecimalField(max_digits=20, decimal_places=10)
    per_gm = models.DecimalField(max_digits=20, decimal_places=4)
    trans_amount = models.DecimalField(max_digits=20, decimal_places=4)

    class Meta:
        unique_together = ('buy_trans', 'trans_date', 'trans_amount')
    
    def get_absolute_url(self):
        return reverse('gold:sell-transaction-detail', args=[str(self.buy_trans.id),str(self.id)])
