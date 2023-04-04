from django.contrib import admin
from django.urls import include, path
from pages.views import home_view, GetInvestmentData, Export
#from pages.views import ChartData
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('alerts/', include('alerts.urls')),
    path('api/chart/investmentdata/', GetInvestmentData.as_view()),
    path('api/export/', Export.as_view()),
    path('bankaccounts/', include('bankaccounts.urls')),
    path('calculator/', include('calculator.urls')),
    path('common/', include('common.urls')),
    path('crypto/', include('crypto.urls')),
    path('epf/', include('epf.urls')),
    path('espp/', include('espp.urls')),
    path('fixed-deposit/', include('fixed_deposit.urls')),
    path('goal/', include('goal.urls')),
    path('gold/', include('gold.urls')),
    path('insurance/', include('insurance.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='account-login'),
    path('logout/', auth_views.LogoutView.as_view(), name='account-logout'),
    path('markets/', include('markets.urls')),
    path('mutualfunds/', include('mutualfunds.urls')),
    path('ppf/', include('ppf.urls')),
    path('reports/', include('reports.urls')),
    path('retirement_401k/', include('retirement_401k.urls')),
    path('rsu/', include('rsu.urls')),
    path('shares/', include('shares.urls')),
    path('ssy/', include('ssy.urls')),
    path('tasks/', include('tasks.urls')),
    path('tax/', include('tax.urls')),
    path('user/', include('users.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)