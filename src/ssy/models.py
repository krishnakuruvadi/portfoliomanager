from django.db import models
from django.urls import reverse

# Create your models here.
class Ssy(models.Model):
    number = models.CharField(max_length=20, primary_key=True)
    start_date = models.DateField()
    user = models.IntegerField()
    goal = models.IntegerField(null=True)
    notes = models.CharField(max_length=40, null=True, blank=True)
    contribution = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    interest_contribution = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    total = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)
    roi = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=0)

    def get_absolute_url(self):
        return reverse("ssys:ssy-detail", kwargs={'id': self.number})

class SsyEntry(models.Model):
    CREDIT = 'CR'
    DEBIT = 'DR'
    ENTRY_TYPE_CHOICES = (
        (CREDIT, 'Credit'),
        (DEBIT, 'Debit'),
        )
    number = models.ForeignKey('Ssy', on_delete=models.CASCADE)
    trans_date = models.DateField(null=False)
    notes = models.CharField(max_length=40)
    reference = models.CharField(max_length=20)
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPE_CHOICES, default=CREDIT, null=False)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    interest_component = models.BooleanField(null=False)
    class Meta:
        unique_together = ('number', 'trans_date','entry_type', 'interest_component')

    def get_absolute_url(self):
        return reverse("ssyentries:ssy-entry-detail", kwargs={"id": self.number})
