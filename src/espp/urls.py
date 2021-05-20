from django.urls import path

from .views import (
    EsppCreateView,
    EsppDeleteView,
    EsppListView,
    EsppDetailView,
    EsppUpdateView,
    refresh_espp_trans,
    CurrentEspps,
    get_sell_trans,
    add_sell_trans,
    delete_sell_trans
)

app_name = 'espps'
urlpatterns = [
    path('', EsppListView.as_view(), name='espp-list'),
    path('create/', EsppCreateView.as_view(), name='espp-create'),
    path('refresh/', refresh_espp_trans, name='espp-refresh'),
    path('<id>/', EsppDetailView.as_view(), name='espp-detail'),
    path('<id>/update/', EsppUpdateView.as_view(), name='espp-update'),
    path('<id>/delete/', EsppDeleteView.as_view(), name='espp-delete'),
    path('<id>/sell/', get_sell_trans, name='espp-sell-trans-list'),
    path('<id>/sell/add', add_sell_trans, name='espp-add-sell-trans'),
    path('<id>/sell/delete', delete_sell_trans, name='espp-delete-sell-trans'),
    #path('<id>/transactions/<year>', show_contributions, name='espp-entry-list'),
    #path('<id>/upload-transactions/', upload_espp_trans, name='espp-upload-trans'),
    #path('<id>/add-contribution/', add_contribution, name='espp-add-contribution'),
    path('api/get/current/<user_id>', CurrentEspps.as_view()),
    path('api/get/current/', CurrentEspps.as_view())
]