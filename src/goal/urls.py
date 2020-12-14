from django.urls import path

from .views import (
    GoalListView,
    GoalDetailView,
    GoalDeleteView,
    add_goal,
    add_retirement_goal,
    update_goal,
    GoalNames,
    ChartData,
    CurrentGoals,
    GoalProgressData
)

app_name = 'goals'

urlpatterns = [
    path('', GoalListView.as_view(), name='goal-list'),
    path('create/', add_goal, name='goal-add'),
    path('create-retirement/', add_retirement_goal, name='goal-add-retirement'),
    path('<id>/', GoalDetailView.as_view(), name='goal-detail'),
    path('<id>/delete/', GoalDeleteView.as_view(), name='goal-delete'),
    path('<id>/update', update_goal, name='goal-update'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('get-goals/<user>', GoalNames.as_view(), name='get-goals'),
    path('api/get/current/<user_id>', CurrentGoals.as_view()),
    path('api/get/current/', CurrentGoals.as_view()),
    path('api/chart/progress/<id>', GoalProgressData.as_view())
]