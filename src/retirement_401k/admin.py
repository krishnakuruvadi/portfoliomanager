from django.contrib import admin
from .models import Account401K, Transaction401K, NAVHistory

# Register your models here.

admin.site.register(Account401K)
admin.site.register(Transaction401K)
admin.site.register(NAVHistory)