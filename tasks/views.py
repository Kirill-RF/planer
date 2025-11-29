# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 20:48:00 2025

@author: Professional
"""

"""
Task management views.

This module provides views for displaying and managing tasks.
Follows SOLID principles by separating concerns and providing clear interfaces.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import SurveyResponseForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from django.db.models import Q
from .models import Task, TaskStatus, TaskType
from django.http import HttpResponseRedirect
from django.urls import reverse

class TaskListView(LoginRequiredMixin, ListView):
    """
    View for displaying list of active tasks.
    
    Attributes
    ----------
    model : Task
        Model to use for the view
    template_name : str
        Template name for task list
    context_object_name : str
        Name of the context variable for the object list
    
    Methods
    -------
    get_queryset()
        Get queryset of active tasks for current user
    get_context_data(**kwargs)
        Add additional context data
    """
    
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    
    def get_queryset(self):
        """Get queryset of active tasks for current user."""
        user = self.request.user
        
        if user.role == 'EMPLOYEE':
            return Task.objects.filter(
                status__in=[TaskStatus.SENT, TaskStatus.REWORK],
                is_active=True
            ).filter(
                Q(assigned_to=user) | Q(assigned_to__isnull=True)
            ).order_by('-created_at')
        
        elif user.role == 'MODERATOR':
            return Task.objects.all().order_by('-created_at')
        
        return Task.objects.none()
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Список задач')
        context['user_role'] = self.request.user.role
        return context


    
class TaskDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying details of a single task.
    
    Attributes
    ----------
    model : Task
        Model to use for the view
    template_name : str
        Template name for task detail
    context_object_name : str
        Name of the context variable for the object
    
    Methods
    -------
    get_object(queryset=None)
        Get the task object with permission check
    get_context_data(**kwargs)
        Add additional context data
    post(request, *args, **kwargs)
        Handle form submission for task completion
    """
    
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_object(self, queryset=None):
        """Get the task object with permission check."""
        task = super().get_object(queryset)
        
        # Check if user can view this task
        if not task.can_be_viewed_by(self.request.user):
            from django.http import Http404
            raise Http404(_("Задача не найдена или недоступна"))
        
        return task
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Детали задачи')
        context['can_edit'] = self.object.can_be_edited_by(self.request.user)
        
        # Добавим отладочную информацию
        user = self.request.user
        context['debug_info'] = {
            'user_role': user.role,
            'task_status': context['task'].status,
            'task_is_completed': context['task'].status == 'COMPLETED',
            'user_can_view': context['task'].can_be_viewed_by(user),
            'user_can_edit': context['task'].can_be_edited_by(user),
        }
        
        # Для анкет добавим информацию о выполнении
        if context['task'].task_type == TaskType.SURVEY:
            context['completion_percentage'] = context['task'].get_completion_percentage()
            
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle task completion."""
        task = self.get_object()
        
        # Check if user can complete this task
        if task.can_be_edited_by(request.user) or (request.user.role == 'EMPLOYEE' and task.assigned_to == request.user):
            # For now, just mark task as completed
            task.status = TaskStatus.COMPLETED
            task.is_active = False
            task.save()
            
            messages.success(request, _("Задача успешно завершена!"))
            return HttpResponseRedirect(reverse('tasks:task_list'))
        
        return self.get(request, *args, **kwargs)

# tasks/views.py - обновленный SurveyResponseView

class SurveyResponseView(LoginRequiredMixin, FormView):
    """
    Представление для заполнения анкеты.
    
    Обрабатывает отправку формы, сохранение ответов
    и обновление статуса задачи.
    """
    
    template_name = 'tasks/survey_form.html'
    form_class = SurveyResponseForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        task_id = self.kwargs['task_id']
        task = get_object_or_404(Task, id=task_id)
        
        if not task.can_be_viewed_by(self.request.user):
            raise Http404(_("Задача не найдена или недоступна"))
        
        if task.task_type != TaskType.SURVEY:
            raise Http404(_("Задача не является анкетой"))
        
        kwargs['task'] = task
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.save()
        
        # Обновляем статус задачи на "На проверке"
        task = form.task
        task.status = TaskStatus.ON_CHECK
        if task.task_type == TaskType.SURVEY:
            task.current_count += 1
        task.save()
        
        messages.success(self.request, _("Анкета успешно заполнена! Ожидайте проверки модератора."))
        return redirect('tasks:task_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = self.kwargs['task_id']
        context['task'] = get_object_or_404(Task, id=task_id)
        context['title'] = _('Заполнение анкеты')
        return context