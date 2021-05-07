from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class User(models.Model):
    name = models.CharField(max_length=60, unique=True)
    email = models.EmailField(_('e-mail'),blank=True, null=True)
    dob = models.DateField(_('Date Of Birth'),null=True, blank=True)
    notes = models.CharField(max_length=60, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("users:user-detail", kwargs={'id': self.id})