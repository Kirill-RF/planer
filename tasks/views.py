# -*- coding: utf-8 -*-
"""
Task management views.

This module provides views for displaying and managing tasks.
Follows SOLID principles by separating concerns and providing clear interfaces.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from .forms import SurveyResponseForm, AddPhotosForm
from .models import Task, TaskStatus, TaskType
from users.models import CustomUser
from django.db.models import Count, Q
from .models import SurveyAnswer, SurveyQuestion, SurveyAnswerPhoto

class TaskListView(LoginRequiredMixin, ListView):
    """
    View for displaying list of active tasks.
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
                status__in=[TaskStatus.SENT, TaskStatus.REWORK, TaskStatus.ON_CHECK],
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
    """
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_object(self, queryset=None):
        """Get the task object with permission check."""
        task = super().get_object(queryset)
        if not task.can_be_viewed_by(self.request.user):
            raise Http404(_("Задача не найдена или недоступна"))
        return task
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Детали задачи')
        context['can_edit'] = self.object.can_be_edited_by(self.request.user)
        
        user = self.request.user
        context['debug_info'] = {
            'user_role': user.role,
            'task_status': context['task'].status,
            'task_is_completed': context['task'].status == 'COMPLETED',
            'user_can_view': context['task'].can_be_viewed_by(user),
            'user_can_edit': context['task'].can_be_edited_by(user),
        }
        
        if context['task'].task_type == TaskType.SURVEY:
            context['completion_percentage'] = context['task'].get_completion_percentage()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle task completion."""
        task = self.get_object()
        if task.can_be_edited_by(request.user) or (request.user.role == 'EMPLOYEE' and task.assigned_to == request.user):
            task.status = TaskStatus.COMPLETED
            task.is_active = False
            task.save()
            messages.success(request, _("Задача успешно завершена!"))
            return HttpResponseRedirect(reverse('tasks:task_list'))
        return self.get(request, *args, **kwargs)

class SurveyResponseView(LoginRequiredMixin, FormView):
    """
    Представление для заполнения анкеты.
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
    
class SurveyResultsView(LoginRequiredMixin, ListView):
    """
    View for displaying survey results.
    """
    template_name = 'tasks/survey_results.html'
    context_object_name = 'results'
    
    def get_queryset(self):
        task_id = self.kwargs['task_id']
        task = get_object_or_404(Task, id=task_id)
        
        # Получаем все ответы по этой задаче
        answers = SurveyAnswer.objects.filter(question__task=task)
        
        # Группируем по вопросам
        results = []
        for question in task.questions.all():
            question_results = {
                'question': question,
                'answers_count': answers.filter(question=question).count()
            }
            
            # Если это вопрос с вариантами ответов
            if question.has_custom_choices():
                choice_stats = {}
                for choice in question.choices.all():
                    count = answers.filter(selected_choices=choice).count()
                    choice_stats[choice.choice_text] = count
                question_results['choice_stats'] = choice_stats
            
            results.append(question_results)
        
        return results
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task'] = get_object_or_404(Task, id=self.kwargs['task_id'])
        context['title'] = _('Результаты анкеты')
        return context
    
class TaskStatisticsView(LoginRequiredMixin, TemplateView):
    """
    View for displaying task statistics.
    """
    template_name = 'tasks/statistics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Статистика задач')
        context['total_tasks'] = Task.objects.count()
        context['completed_tasks'] = Task.objects.filter(status='COMPLETED').count()
        return context
    
# В конец файла tasks/views.py

class AddPhotosView(LoginRequiredMixin, FormView):
    """
    View for adding additional photos to existing survey answer.
    """
    template_name = 'tasks/add_photos.html'
    form_class = AddPhotosForm
    
    def get_answer(self):
        answer_id = self.kwargs['answer_id']
        return get_object_or_404(SurveyAnswer, id=answer_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answer = self.get_answer()
        context['answer'] = answer
        context['current_photo_count'] = answer.photos.count()
        context['remaining_photos'] = max(0, 10 - answer.photos.count())
        return context
    
    # tasks/views.py - метод form_valid в AddPhotosView

    def form_valid(self, form):
        answer = self.get_answer()
        current_count = answer.photos.count()
        remaining_slots = 10 - current_count
        
        if remaining_slots <= 0:
            messages.error(self.request, _("Максимальное количество фото (10) уже достигнуто."))
            return self.form_invalid(form)
        
        # ИСПРАВЛЕНО: используем self.request.FILES вместо self.files
        uploaded_files = self.request.FILES.getlist('photos')
        actual_upload_count = min(len(uploaded_files), remaining_slots)
        
        for i in range(actual_upload_count):
            SurveyAnswerPhoto.objects.create(
                answer=answer,
                photo=uploaded_files[i]
            )
        
        messages.success(self.request, _(f"Успешно добавлено {actual_upload_count} фото."))
        return redirect('tasks:survey_results', task_id=answer.question.task.id)