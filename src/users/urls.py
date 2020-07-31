from django.urls import path

from .views import (
    UserListView,
    UserDetailView,
    UserDeleteView,
    add_user,
    update_user,
    ChartData,
    Users
)

app_name = 'users'

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('create/', add_user, name='user-add'),
    path('<id>/', UserDetailView.as_view(), name='user-detail'),
    path('<id>/delete/', UserDeleteView.as_view(), name='user-delete'),
    path('<id>/update', update_user, name='user-update'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('api/get/users', Users.as_view())

]