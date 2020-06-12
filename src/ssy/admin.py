from django.contrib import admin

# Register your models here.
from .models import Ssy, SsyEntry


admin.site.register(Ssy)
admin.site.register(SsyEntry)