from django.contrib import admin

from .models import Stock, HistoricalStockPrice, MutualFund, HistoricalMFPrice, HistoricalForexRates, MFYearlyReturns, MFCategoryReturns


admin.site.register(Stock)
admin.site.register(HistoricalStockPrice)
admin.site.register(MutualFund)
admin.site.register(HistoricalMFPrice)
admin.site.register(HistoricalForexRates)
admin.site.register(MFYearlyReturns)
admin.site.register(MFCategoryReturns)
