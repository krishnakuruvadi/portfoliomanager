from django.contrib import admin

# Register your models here.
from .models import RSUAward, RestrictedStockUnits


admin.site.register(RSUAward)
admin.site.register(RestrictedStockUnits)