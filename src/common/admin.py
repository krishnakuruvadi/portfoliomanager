from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import Stock, HistoricalStockPrice, MutualFund, HistoricalMFPrice, HistoricalForexRates, MFYearlyReturns, MFCategoryReturns, ScrollData, Preferences


admin.site.register(Stock)
admin.site.register(HistoricalStockPrice)
admin.site.register(MutualFund)
admin.site.register(HistoricalMFPrice)
admin.site.register(HistoricalForexRates)
admin.site.register(MFYearlyReturns)
admin.site.register(MFCategoryReturns)
admin.site.register(ScrollData)
admin.site.register(Preferences, SingletonModelAdmin)