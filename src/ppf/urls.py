from django.urls import path

from .views import (
    PpfCreateView,
    PpfDeleteView,
    PpfDetailView,
    PpfListView,
    PpfUpdateView,
    PpfEntryListView,
    upload_ppf_trans,
    PpfAddEntryView,
    ChartData
   

)

app_name = 'ppfs'
urlpatterns = [
    path('', PpfListView.as_view(), name='ppf-list'),
    path('create/', PpfCreateView.as_view(), name='ppf-create'),
    path('<id>/', PpfDetailView.as_view(), name='ppf-detail'),
    path('<id>/update/', PpfUpdateView.as_view(), name='ppf-update'),
    path('<id>/delete/', PpfDeleteView.as_view(), name='ppf-delete'),
    path('<id>/transactions/', PpfEntryListView.as_view(), name='ppf-entry-list'),
    path('<id>/upload-transactions/', upload_ppf_trans, name='ppf-upload-trans'),
    path('<id>/add-transaction/', PpfAddEntryView.as_view(), name='ppf-add-trans'),
    path('api/chart/data/<id>', ChartData.as_view())
]