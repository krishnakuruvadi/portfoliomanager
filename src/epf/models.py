from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Epf(models.Model):
    class Meta:
        unique_together = (('number', 'company'),)
    number = models.CharField(max_length=50)
    company = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    user = models.IntegerField()
    goal =  models.IntegerField(null=True)
    notes = models.CharField(max_length=40, null=True, blank=True)
    employee_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    employer_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    interest_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    withdrawl = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    total = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    roi = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)

    def get_absolute_url(self):
        return reverse("epfs:epf-detail", kwargs={'id': self.id})

class EpfEntry(models.Model):
    epf_id = models.ForeignKey('Epf', on_delete=models.CASCADE)
    trans_date = models.DateField(null=False)
    notes = models.CharField(max_length=40)
    reference = models.CharField(max_length=20)
    employee_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=False, default=0)
    employer_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=False, default=0)
    interest_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=False, default=0)
    withdrawl = models.DecimalField(max_digits=20, decimal_places=2, null=False, default=0)

    class Meta:
        unique_together = ('epf_id', 'trans_date')

    def get_absolute_url(self):
        return reverse("epfentries:epf-entry-detail", kwargs={"id": self.epf_id})
    
    def __str__(self):
        return str(self.trans_date) + ":" + str(self.employee_contribution) + ":" + str(self.employer_contribution) + " " + str(self.interest_contribution) + " " + str(self.withdrawl)

