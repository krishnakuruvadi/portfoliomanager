from django.urls import path

from .views import (
    goal_list,
    GoalDetailView,
    GoalDeleteView,
    add_goal,
    add_retirement_goal,
    update_goal,
    GoalNames,
    ChartData,
    CurrentGoals,
    GoalProgressData,
    goals_insight
)

app_name = 'goals'

urlpatterns = [
    path('', goal_list, name='goal-list'),
    path('create/', add_goal, name='goal-add'),
    path('create-retirement/', add_retirement_goal, name='goal-add-retirement'),
    path('insights/', goals_insight, name='goals-insight'),
    path('<id>/', GoalDetailView.as_view(), name='goal-detail'),
    path('<id>/delete/', GoalDeleteView.as_view(), name='goal-delete'),
    path('<id>/update', update_goal, name='goal-update'),
    path('api/chart/data/<id>', ChartData.as_view()),
    path('get-goals/<user>', GoalNames.as_view(), name='get-goals'),
    path('api/get/current/<user_id>', CurrentGoals.as_view()),
    path('api/get/current/', CurrentGoals.as_view()),
    path('api/chart/progress/<id>/', GoalProgressData.as_view()),
    path('api/chart/progress/<id>/<expected_return>', GoalProgressData.as_view())
]