from django.urls import path

from .views import (
    RsuCreateView,
    RsuDeleteView,
    RsuListView,
    RsuDetailView,
    RsuUpdateView,
    RsuVestDeleteView,
    RsuVestDetailView,
    refresh_rsu_trans,
    refresh_rsu_vest_trans,
    show_vest_list,
    add_vest,
    update_vest,
    CurrentRsus
)

app_name = 'rsus'
urlpatterns = [
    path('', RsuListView.as_view(), name='rsu-list'),
    path('create/', RsuCreateView.as_view(), name='rsu-create'),
    path('refresh/', refresh_rsu_trans, name='rsu-refresh'),
    path('<id>/', RsuDetailView.as_view(), name='rsu-detail'),
    path('<id>/update/', RsuUpdateView.as_view(), name='rsu-update'),
    path('<id>/delete/', RsuDeleteView.as_view(), name='rsu-delete'),
    path('<id>/vest/', show_vest_list, name='rsu-vest-list'),
    path('<id>/vest/create', add_vest, name='rsu-add-vest'),
    path('<id>/vest/<vestid>/update', update_vest, name='rsu-update-vest'),
    path('<id>/vest/refresh/', refresh_rsu_vest_trans, name='rsu-vest-refresh'),
    path('vest/<vestid>/delete', RsuVestDeleteView.as_view(), name='rsu-vest-delete'),
    path('vest/<id>/', RsuVestDetailView.as_view(), name='rsu-vest-detail'),

    #path('<id>/upload-transactions/', upload_rsu_trans, name='rsu-upload-trans'),
    #path('<id>/add-contribution/', add_contribution, name='rsu-add-contribution'),
    path('api/get/current/<user_id>', CurrentRsus.as_view()),
    path('api/get/current/', CurrentRsus.as_view())
]