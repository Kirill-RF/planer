# tasks/urls.py

from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('list/', views.TaskListView.as_view(), name='task_list'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('survey/<int:task_id>/', views.SurveyResponseView.as_view(), name='survey_response'),
    path('survey/<int:task_id>/results/', views.SurveyResultsView.as_view(), name='survey_results'),
    path('answer/<int:answer_id>/add-photos/', views.AddPhotosView.as_view(), name='add_photos'),  # ДОБАВЬТЕ ЭТУ СТРОКУ
]