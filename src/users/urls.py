from django.urls import path

from .views import (
    UserListView,
    UserDetailView,
    user_delete,
    add_user,
    update_user,
    ChartData,
    Users,
    UserMonthlyContribDeduct,
    insights_view,
)

app_name = 'users'

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('create/', add_user, name='user-add'),
    path('insights/', insights_view, name='insights'),
    path('<id>/', UserDetailView.as_view(), name='user-detail'),
    path('<id>/delete/', user_delete, name='user-delete'),
    path('<id>/update', update_user, name='user-update'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('api/get/users', Users.as_view()),
    path('api/get/users_contrib/<id>/<year>', UserMonthlyContribDeduct.as_view())
]
