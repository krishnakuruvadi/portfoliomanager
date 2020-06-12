"""portfoliomgr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from pages.views import home_view
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('ppf/', include('ppf.urls')),
    path('ssy/', include('ssy.urls')),
    path('epf/', include('epf.urls')),
    path('espp/', include('espp.urls')),
    path('goal/', include('goal.urls')),
    path('user/', include('users.urls')),
    path('fixed-deposit/', include('fixed_deposit.urls')),
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)