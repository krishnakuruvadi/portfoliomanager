from django.contrib import admin

# Register your models here.
from .models import Ppf, PpfEntry


admin.site.register(Ppf)
admin.site.register(PpfEntry)