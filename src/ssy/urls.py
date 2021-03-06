from django.urls import path

from .views import (
    SsyCreateView,
    SsyDeleteView,
    SsyListView,
    SsyDetailView,
    SsyUpdateView,
    SsyEntryListView,
    upload_ssy_trans,
    SsyAddEntryView,
    ChartData,
    CurrentSsys
)

app_name = 'ssys'
urlpatterns = [
    path('', SsyListView.as_view(), name='ssy-list'),
    path('create/', SsyCreateView.as_view(), name='ssy-create'),
    path('<id>/', SsyDetailView.as_view(), name='ssy-detail'),
    path('<id>/update/', SsyUpdateView.as_view(), name='ssy-update'),
    path('<id>/delete/', SsyDeleteView.as_view(), name='ssy-delete'),
    path('<id>/transactions/', SsyEntryListView.as_view(), name='ssy-entry-list'),
    path('<id>/upload-transactions/', upload_ssy_trans, name='ssy-upload-trans'),
    path('<id>/add-transaction/', SsyAddEntryView.as_view(), name='ssy-add-trans'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('api/get/current/<user_id>', CurrentSsys.as_view()),
    path('api/get/current/', CurrentSsys.as_view())
]