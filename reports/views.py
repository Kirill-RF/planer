"""
Reporting views for analytics and statistics.

This module provides views for generating and displaying reports.
"""

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext as _
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Prefetch
from django.core.cache import cache
from datetime import date
from .models import EquipmentReport, Evaluation, Photo
from .serializers import (
    EquipmentReportSerializer, 
    EvaluationSerializer, 
    PhotoReportStatsSerializer,
    EquipmentPhotoReportQuestionSerializer,
    EquipmentPhotoReportAnswerSerializer
)
from users.models import CustomUser, UserRoles
from clients.models import Client
from tasks.models import TaskType


def get_photo_report_stats(client_id=None, employee_id=None, left_date=None, right_start=None, right_end=None):
    """
    Get photo report statistics based on filters.
    
    Parameters
    ----------
    client_id : int, optional
        Filter by specific client
    employee_id : int, optional
        Filter by employee
    left_date : date, optional
        Date for left panel
    right_start : date, optional
        Start date for right panel
    right_end : date, optional
        End date for right panel
    
    Returns
    -------
    dict
        Statistics data for both panels
    """
    # Build query filters
    base_filters = Q()
    
    if client_id:
        base_filters &= Q(client_id=client_id)
    elif employee_id:
        base_filters &= Q(employee_id=employee_id)
    
    # Left panel: single date
    left_filters = base_filters
    if left_date:
        left_filters &= Q(date=left_date)
    
    # Right panel: date range
    right_filters = base_filters
    if right_start and right_end:
        right_filters &= Q(date__range=[right_start, right_end])
    elif right_start:
        right_filters &= Q(date=right_start)  # Single date if only start provided
    
    # Get reports with related data
    left_reports = EquipmentReport.objects.filter(left_filters).select_related(
        'client', 'employee'
    ).prefetch_related(
        'photos', 'evaluation_set'
    ).order_by('client__name', '-date')
    
    right_reports = EquipmentReport.objects.filter(right_filters).select_related(
        'client', 'employee'
    ).prefetch_related(
        'photos', 'evaluation_set'
    ).order_by('client__name', '-date')
    
    # Group reports by client
    left_data = {}
    for report in left_reports:
        client_key = report.client.id
        if client_key not in left_data:
            left_data[client_key] = {
                'client_id': report.client.id,
                'client_name': report.client.name,
                'employee_id': report.employee.id,
                'employee_name': report.employee.get_full_name() or report.employee.username,
                'reports': [],
                'evaluation': None
            }
        left_data[client_key]['reports'].append(report)
        
        # Get evaluation if exists
        evaluation = report.evaluation_set.first()
        if evaluation:
            left_data[client_key]['evaluation'] = evaluation
    
    right_data = {}
    for report in right_reports:
        client_key = report.client.id
        if client_key not in right_data:
            right_data[client_key] = {
                'client_id': report.client.id,
                'client_name': report.client.name,
                'employee_id': report.employee.id,
                'employee_name': report.employee.get_full_name() or report.employee.username,
                'reports': [],
                'evaluation': None
            }
        right_data[client_key]['reports'].append(report)
        
        # Get evaluation if exists
        evaluation = report.evaluation_set.first()
        if evaluation:
            right_data[client_key]['evaluation'] = evaluation
    
    return {
        'left_panel': list(left_data.values()),
        'right_panel': list(right_data.values())
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def photo_report_stats(request):
    """
    API endpoint to get photo report statistics.
    
    Query parameters:
    - client_id: filter by specific client
    - employee_id: filter by employee
    - left_date: date for left panel
    - right_start: start date for right panel
    - right_end: end date for right panel
    """
    if not request.user.has_perm('reports.view_taskstatistics') and request.user.role != UserRoles.MODERATOR:
        return Response(
            {'error': 'У вас нет прав для просмотра статистики'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get query parameters
    client_id = request.query_params.get('client_id')
    employee_id = request.query_params.get('employee_id')
    left_date = request.query_params.get('left_date')
    right_start = request.query_params.get('right_start')
    right_end = request.query_params.get('right_end')
    
    # Validate dates
    if left_date:
        try:
            left_date = date.fromisoformat(left_date)
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты для left_date'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if right_start:
        try:
            right_start = date.fromisoformat(right_start)
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты для right_start'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if right_end:
        try:
            right_end = date.fromisoformat(right_end)
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты для right_end'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Validate date range
    if right_start and right_end and right_start > right_end:
        return Response(
            {'error': 'Начальная дата не может быть позже конечной'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate future dates
    if (left_date and left_date > date.today()) or \
       (right_start and right_start > date.today()) or \
       (right_end and right_end > date.today()):
        return Response(
            {'error': 'Нельзя выбирать даты в будущем'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate cache key
    cache_key = f"photo_report_stats_{client_id}_{employee_id}_{left_date}_{right_start}_{right_end}"
    cache_key = cache_key.replace(" ", "_").replace("-", "_").replace(":", "_")
    
    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)
    
    # Get data
    data = get_photo_report_stats(client_id, employee_id, left_date, right_start, right_end)
    
    # Cache for 5 minutes
    cache.set(cache_key, data, 300)  # 5 minutes
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_evaluation(request):
    """
    API endpoint to create evaluation and improvement task.
    """
    if request.user.role != UserRoles.MODERATOR:
        return Response(
            {'error': 'Только модераторы могут оценивать отчеты'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = EvaluationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        evaluation = serializer.save()
        return Response(
            EvaluationSerializer(evaluation).data, 
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_equipment_report_questions(request, report_id):
    """
    API endpoint to get questions for equipment report.
    
    Parameters
    ----------
    report_id : int
        ID of the equipment report
    """
    try:
        report = EquipmentReport.objects.get(id=report_id)
    except EquipmentReport.DoesNotExist:
        return Response(
            {'error': 'Отчет по оборудованию не найден'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    questions = EquipmentPhotoReportQuestion.objects.filter(report=report).prefetch_related('choices')
    serializer = EquipmentPhotoReportQuestionSerializer(questions, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_equipment_report_answer(request):
    """
    API endpoint to submit answer to equipment report question.
    """
    if request.user.role != UserRoles.EMPLOYEE:
        return Response(
            {'error': 'Только сотрудники могут отвечать на вопросы'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = EquipmentPhotoReportAnswerSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        answer = serializer.save()
        return Response(
            EquipmentPhotoReportAnswerSerializer(answer).data, 
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@staff_member_required
def generate_statistics(request):
    """Generate statistics for all completed tasks."""
    # TODO: Implement actual statistics generation
    messages.info(request, _("Генерация статистики будет реализована"))
    return redirect('admin:reports_taskstatistics_changelist')


@staff_member_required
def export_to_excel(request):
    """Export statistics to Excel."""
    messages.info(request, _("Экспорт в Excel будет реализован"))
    return redirect('admin:reports_taskstatistics_changelist')


@staff_member_required
def task_analysis(request, task_id):
    """Detailed analysis view for specific task."""
    messages.info(request, _("Подробный анализ будет реализован"))
    return redirect('admin:reports_taskstatistics_changelist')