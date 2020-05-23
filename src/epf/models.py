from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Epf(models.Model):
    class Meta:
        unique_together = (('number', 'company'),)
    number = models.CharField(max_length=20)
    company = models.CharField(max_length=120)
    start_date = models.DateField()
    user = models.CharField(max_length=20)
    goal =  models.IntegerField(null=True)

    def get_absolute_url(self):
        return reverse("epfs:epf-detail", kwargs={'id': self.id})

class EpfEntry(models.Model):
    CREDIT = 'CR'
    DEBIT = 'DR'
    ENTRY_TYPE_CHOICES = (
        (CREDIT, 'Credit'),
        (DEBIT, 'Debit'),
        )
    epf_id = models.ForeignKey('Epf', on_delete=models.CASCADE)
    trans_date = models.DateField(null=False)
    notes = models.CharField(max_length=40)
    reference = models.CharField(max_length=20)
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPE_CHOICES, default=CREDIT, null=False)
    employee_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=False, default=0)
    employer_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=False, default=0)
    interest_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=False, default=0)
    class Meta:
        unique_together = ('epf_id', 'trans_date','entry_type')

    def get_absolute_url(self):
        return reverse("epfentries:epf-entry-detail", kwargs={"id": self.epf_id})
