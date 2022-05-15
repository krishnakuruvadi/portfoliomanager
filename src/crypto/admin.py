from django.contrib import admin
from .models import Crypto, Transaction

# Register your models here.
admin.site.register(Crypto)
admin.site.register(Transaction)