from django.urls import path

from .views import (
    add_ssy,
    SsyDeleteView,
    SsyListView,
    SsyDetailView,
    update_ssy,
    SsyEntryListView,
    upload_ssy_trans,
    add_trans,
    ChartData,
    CurrentSsys
)

app_name = 'ssys'
urlpatterns = [
    path('', SsyListView.as_view(), name='ssy-list'),
    path('create/', add_ssy, name='ssy-create'),
    path('<id>/', SsyDetailView.as_view(), name='ssy-detail'),
    path('<id>/update/', update_ssy, name='ssy-update'),
    path('<id>/delete/', SsyDeleteView.as_view(), name='ssy-delete'),
    path('<id>/transactions/', SsyEntryListView.as_view(), name='ssy-entry-list'),
    path('<id>/upload-transactions/', upload_ssy_trans, name='ssy-upload-trans'),
    path('<id>/add-transaction/', add_trans, name='ssy-add-trans'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('api/get/current/<user_id>', CurrentSsys.as_view()),
    path('api/get/current/', CurrentSsys.as_view())
]