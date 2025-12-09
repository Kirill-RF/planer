from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Existing URLs
    path('generate-statistics/', views.generate_statistics, name='generate_statistics'),
    path('export-excel/', views.export_to_excel, name='export_excel'),
    path('task/<int:task_id>/analysis/', views.task_analysis, name='task_analysis'),
    
    # New API endpoints for photo report statistics
    path('api/photo-report-stats/', views.photo_report_stats, name='photo_report_stats'),
    path('api/create-evaluation/', views.create_evaluation, name='create_evaluation'),
]