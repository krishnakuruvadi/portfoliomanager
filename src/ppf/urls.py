from django.urls import path

from .views import (
    add_ppf,
    PpfDeleteView,
    PpfDetailView,
    PpfListView,
    update_ppf,
    PpfEntryListView,
    upload_ppf_trans,
    add_trans,
    ChartData,
    CurrentPpfs

)

app_name = 'ppfs'
urlpatterns = [
    path('', PpfListView.as_view(), name='ppf-list'),
    path('create/', add_ppf, name='ppf-create'),
    path('<id>/', PpfDetailView.as_view(), name='ppf-detail'),
    path('<id>/update/', update_ppf, name='ppf-update'),
    path('<id>/delete/', PpfDeleteView.as_view(), name='ppf-delete'),
    path('<id>/transactions/', PpfEntryListView.as_view(), name='ppf-entry-list'),
    path('<id>/upload-transactions/', upload_ppf_trans, name='ppf-upload-trans'),
    path('<id>/add-transaction/', add_trans, name='ppf-add-trans'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('api/get/current/<user_id>', CurrentPpfs.as_view()),
    path('api/get/current/', CurrentPpfs.as_view())
]