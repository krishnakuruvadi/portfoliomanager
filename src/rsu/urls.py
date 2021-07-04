from django.urls import path

from .views import (
    RsuDeleteView,
    RsuListView,
    RsuDetailView,
    delete_vest,
    RsuVestDetailView,
    refresh_rsu_trans,
    refresh_rsu_vest_trans,
    show_vest_list,
    add_vest,
    update_vest,
    add_vest_sell_trans,
    show_vest_sell_trans,
    delete_vest_sell_trans,
    CurrentRsus,
    create_rsu,
    update_rsu
)

app_name = 'rsus'
urlpatterns = [
    path('', RsuListView.as_view(), name='rsu-list'),
    path('create/', create_rsu, name='rsu-create'),
    path('refresh/', refresh_rsu_trans, name='rsu-refresh'),
    path('<id>/', RsuDetailView.as_view(), name='rsu-detail'),
    path('<id>/update/', update_rsu, name='rsu-update'),
    path('<id>/delete/', RsuDeleteView.as_view(), name='rsu-delete'),
    path('<id>/vest/', show_vest_list, name='rsu-vest-list'),
    path('<id>/vest/create', add_vest, name='rsu-add-vest'),
    path('<id>/vest/<vestid>/update', update_vest, name='rsu-update-vest'),
    path('<id>/vest/refresh/', refresh_rsu_vest_trans, name='rsu-vest-refresh'),
    path('<id>/vest/<vestid>/delete', delete_vest, name='rsu-vest-delete'),
    path('<id>/vest/<vestid>/sell', add_vest_sell_trans, name='rsu-sell-vest-add'),
    path('<id>/vest/<vestid>/sell_trans', show_vest_sell_trans, name='rsu-sell-vest'),
    path('<id>/vest/<vestid>/delete/<selltransid>', delete_vest_sell_trans, name='rsu-sell-vest-delete'),
    path('<id>/vest/<vestid>/', RsuVestDetailView.as_view(), name='rsu-vest-detail'),

    #path('<id>/upload-transactions/', upload_rsu_trans, name='rsu-upload-trans'),
    #path('<id>/add-contribution/', add_contribution, name='rsu-add-contribution'),
    path('api/get/current/<user_id>', CurrentRsus.as_view()),
    path('api/get/current/', CurrentRsus.as_view())
]