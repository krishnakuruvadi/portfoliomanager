from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

RISK_PROFILE_CHOICES = [
    ('conservative', 'Conservative'),
    ('moderate', 'Moderate'),
    ('aggressive', 'Aggressive'),
]

class User(models.Model):
    name = models.CharField(max_length=60, unique=True)
    email = models.EmailField(_('e-mail'),blank=True, null=True)
    dob = models.DateField(_('Date Of Birth'),null=True, blank=True)
    notes = models.CharField(max_length=60, null=True, blank=True)
    short_name = models.CharField(max_length=15, unique=True, null=True, blank=True)
    total_networth = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    as_on = models.DateTimeField(null=True, blank=True)
    risk_profile = models.CharField(max_length=20, choices=RISK_PROFILE_CHOICES, default='moderate')
    
    def get_absolute_url(self):
        return reverse("users:user-detail", kwargs={'id': self.id})
    
    def get_user_short_name_or_name(self):
        if self.short_name and self.short_name != '':
            return self.short_name
        return self.name

class AssetClassDistribution(models.Model):

    user = models.ForeignKey('User',on_delete=models.CASCADE)
    as_on_date = models.DateTimeField(null=True, blank=True, default="")

    suggested_equity_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    preferred_equity_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    current_equity_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    suggested_debt_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    preferred_debt_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    current_debt_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    suggested_gold_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    preferred_gold_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    current_gold_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    suggested_crypto_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    preferred_crypto_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    current_crypto_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    suggested_cash_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    preferred_cash_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    current_cash_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def get_absolute_url(self):
        return reverse("users:asset-class-distribution", kwargs={'id': self.id})