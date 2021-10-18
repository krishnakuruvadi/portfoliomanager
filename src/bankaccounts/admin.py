from django.contrib import admin
from .models import BankAccount, Transaction

# Register your models here.
admin.site.register(BankAccount)
admin.site.register(Transaction)