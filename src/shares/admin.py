from django.contrib import admin

# Register your models here.
from .models import Share, Transactions

admin.site.register(Share)
admin.site.register(Transactions)