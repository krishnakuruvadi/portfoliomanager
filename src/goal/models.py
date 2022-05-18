from django.db import models
from django.urls import reverse

# Create your models here.

class Goal(models.Model):
    name = models.CharField(max_length=60)
    start_date = models.DateField(null=False)
    curr_val = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    time_period = models.IntegerField(null=False)
    inflation = models.DecimalField(max_digits=4, decimal_places=2, null=False)
    final_val = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    user = models.IntegerField()
    recurring_pay_goal = models.BooleanField(null=False)
    expense_period = models.IntegerField(null=True, blank=True)
    post_returns = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    notes = models.CharField(max_length=60, null=True, blank=True)
    equity_contrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    debt_contrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    achieved_amt = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    pending_amt = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    achieved_percent = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    pending_percent = models.DecimalField(max_digits=20, decimal_places=2, default=100)
    epf_conitrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    espp_conitrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    fd_conitrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    ppf_conitrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    ssy_conitrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    rsu_conitrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    shares_conitrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    mf_conitrib = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    r_401k_contribution = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    insurance_contribution = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    gold_contribution = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cash_contribution = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    crypto_contribution = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    def get_absolute_url(self):
        return reverse("goals:goal-detail", kwargs={'id': self.id})