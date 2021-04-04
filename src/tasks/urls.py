from django.urls import path

from .views import (
    get_tasks,
    TaskDetailView,
    run_task
)

app_name = 'tasks'

urlpatterns = [
    path('', get_tasks, name='task-list'),
    path('<id>/', TaskDetailView.as_view(), name='task-detail'),
    path('<id>/run/', run_task, name='run-task')
]