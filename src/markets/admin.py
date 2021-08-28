from django.contrib import admin

# Register your models here.

from .models import PEMonthy, PBMonthy, News, IndexYearlyReturns, IndexQuarterlyReturns, IndexMonthlyReturns, IndexRollingReturns

admin.site.register(PEMonthy)
admin.site.register(PBMonthy)
admin.site.register(News)
admin.site.register(IndexYearlyReturns)
admin.site.register(IndexQuarterlyReturns)
admin.site.register(IndexMonthlyReturns)
admin.site.register(IndexRollingReturns)