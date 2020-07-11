from django.db import models

from django.urls import reverse

# Create your models here.

class FixedDeposit(models.Model):
    number = models.CharField(max_length=60)
    bank_name = models.CharField(max_length=60)
    start_date = models.DateField(null=False)
    principal = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    roi = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    time_period = models.IntegerField(null=False)
    final_val = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    user = models.IntegerField()
    notes = models.CharField(max_length=80, null=True, blank=True)
    goal = models.IntegerField(null=True, blank=True)
    mat_date = models.DateField(null=False)

    def get_absolute_url(self):
        return reverse("fixed-deposits:fixed-deposit-detail", kwargs={'id': self.id})
