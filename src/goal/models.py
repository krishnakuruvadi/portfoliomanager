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

    def get_absolute_url(self):
        return reverse("goals:goal-detail", kwargs={'id': self.id})