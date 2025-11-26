# -*- coding: utf-8 -*-
"""
Created on Sat Nov 22 17:51:57 2025

@author: Professional
"""

# surveys/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-clients/', views.upload_clients, name='upload_clients'),
    path('survey/<int:survey_id>/fill/', 
         views.fill_survey, name='fill_survey'),
    path('results/', views.results_overview, name='results_overview'),
]