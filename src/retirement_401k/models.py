from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Account401K(models.Model):
    company = models.CharField(max_length=100)
    start_date = models.DateField()
    user = models.IntegerField()
    goal =  models.IntegerField(null=True)
    notes = models.CharField(max_length=40, null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    employee_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    employer_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    total = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    roi = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    units = models.DecimalField(max_digits=20, decimal_places=6, null=True, default=0)
    nav = models.DecimalField(max_digits=20, decimal_places=6, null=True, default=0)
    nav_date = models.DateField(null=True, blank=True)
    latest_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    gain = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)

    def get_absolute_url(self):
        return reverse("retirement_401k:account-detail", kwargs={'id': self.id})

class Transaction401K(models.Model):
    account = models.ForeignKey('Account401K', on_delete=models.CASCADE)
    trans_date = models.DateField(null=False)
    notes = models.CharField(max_length=40)
    employee_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    employer_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    units = models.DecimalField(max_digits=20, decimal_places=6, null=False)
    class Meta:
        unique_together = ('account', 'trans_date')

    def get_absolute_url(self):
        return reverse("retirement_401k:transaction-entry-detail", kwargs={"id": self.id})

class NAVHistory(models.Model):
    account = models.ForeignKey('Account401K', on_delete=models.CASCADE)
    nav_value = models.DecimalField(max_digits=20, decimal_places=6)
    nav_date = models.DateField()
    comparision_nav_value = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    class Meta:
        unique_together = ('account', 'nav_date')
    
    def __str__(self):
        return self.account.company+ ' ' + self.nav_date.strftime('%d-%b-%Y') + ' ' + str(self.nav_value)
