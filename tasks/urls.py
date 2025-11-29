"""
URL configuration for tasks app.

This module defines URL routes for task-related views.
"""

from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('list/', views.TaskListView.as_view(), name='task_list'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('survey/<int:task_id>/', views.SurveyResponseView.as_view(), name='survey_response'),
]