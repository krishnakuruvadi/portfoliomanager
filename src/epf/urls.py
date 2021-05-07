from django.urls import path

from .views import (
    create_epf,
    EpfDeleteView,
    EpfListView,
    EpfDetailView,
    update_epf,
    add_contribution,
    show_contributions,
    CurrentEpfs
)

app_name = 'epfs'
urlpatterns = [
    path('', EpfListView.as_view(), name='epf-list'),
    path('create/', create_epf, name='epf-create'),
    path('<id>/', EpfDetailView.as_view(), name='epf-detail'),
    path('<id>/update/', update_epf, name='epf-update'),
    path('<id>/delete/', EpfDeleteView.as_view(), name='epf-delete'),
    path('<id>/transactions/', show_contributions, name='epf-entry-list'),
    path('<id>/transactions/<year>', show_contributions, name='epf-entry-list'),
    #path('<id>/upload-transactions/', upload_epf_trans, name='epf-upload-trans'),
    path('<id>/add-contribution/', add_contribution, name='epf-add-contribution'),
    path('api/get/current/<user_id>', CurrentEpfs.as_view()),
    path('api/get/current/', CurrentEpfs.as_view())
]