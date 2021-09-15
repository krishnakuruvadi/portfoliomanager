from django.contrib import admin
from .models import InsurancePolicy, Transaction, Fund, NAVHistory
# Register your models here.


admin.site.register(InsurancePolicy)
admin.site.register(Transaction)
admin.site.register(NAVHistory)
admin.site.register(Fund)