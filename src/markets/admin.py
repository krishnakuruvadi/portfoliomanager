from django.contrib import admin

# Register your models here.

from .models import PEMonthy, PBMonthy

admin.site.register(PEMonthy)
admin.site.register(PBMonthy)