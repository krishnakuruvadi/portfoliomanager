from django.db import models

# Create your models here.

class InvestmentData(models.Model):
    user = models.CharField(max_length=20, null=False, blank=False, primary_key=True)
    as_on_date = models.DateTimeField(null=True, blank=True)
    start_day_across_portfolio = models.DateField(null=True, blank=True)
    ppf_data  = models.CharField(max_length=6000, null=True, blank=True)
    epf_data = models.CharField(max_length=6000, null=True, blank=True)
    ssy_data = models.CharField(max_length=6000, null=True, blank=True)
    fd_data = models.CharField(max_length=6000, null=True, blank=True)
    espp_data = models.CharField(max_length=6000, null=True, blank=True)
    rsu_data = models.CharField(max_length=6000, null=True, blank=True)
    shares_data = models.CharField(max_length=6000, null=True, blank=True)
    mf_data = models.CharField(max_length=6000, null=True, blank=True)
    r401k_data = models.CharField(max_length=6000, null=True, blank=True)
    insurance_data = models.CharField(max_length=6000, null=True, blank=True)
    gold_data = models.CharField(max_length=6000, null=True, blank=True)
    cash_data = models.CharField(max_length=6000, null=True, blank=True)
    loan_data = models.CharField(max_length=6000, null=True, blank=True, default="")
    crypto_data = models.CharField(max_length=6000, null=True, blank=True, default="")
    total_data = models.CharField(max_length=6000, null=True, blank=True)
