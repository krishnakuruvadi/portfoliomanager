from django.urls import path

from .views import (
    EpfCreateView,
    EpfDeleteView,
    EpfListView,
    EpfDetailView,
    EpfUpdateView,
    add_contribution,
    show_contributions

)

app_name = 'epfs'
urlpatterns = [
    path('', EpfListView.as_view(), name='epf-list'),
    path('create/', EpfCreateView.as_view(), name='epf-create'),
    path('<id>/', EpfDetailView.as_view(), name='epf-detail'),
    path('<id>/update/', EpfUpdateView.as_view(), name='epf-update'),
    path('<id>/delete/', EpfDeleteView.as_view(), name='epf-delete'),
    path('<id>/transactions/', show_contributions, name='epf-entry-list'),
    path('<id>/transactions/<year>', show_contributions, name='epf-entry-list'),
    #path('<id>/upload-transactions/', upload_epf_trans, name='epf-upload-trans'),
    path('<id>/add-contribution/', add_contribution, name='epf-add-contribution'),
    #path('api/chart/data/<id>', ChartData.as_view())
]