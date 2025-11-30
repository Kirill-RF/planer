# tasks/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.forms import TextInput, Textarea
from django.db import models
from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline
from .models import (
    Task, TaskStatus, TaskType, SurveyQuestion, 
    SurveyQuestionChoice, SurveyAnswer, PhotoReport, PhotoReportItem
)



class SurveyQuestionChoiceInline(NestedTabularInline):
    """Inline choices for survey questions."""
    model = SurveyQuestionChoice
    extra = 3
    verbose_name = _('Вариант ответа')
    verbose_name_plural = _('Варианты ответов')
    
    def has_add_permission(self, request, obj=None):
        """
        Добавляем варианты ответов только для вопросов с подходящим типом.
        obj здесь — это SurveyQuestion, а не Task.
        """
        if obj and hasattr(obj, 'question_type'):
            if obj.question_type in ['RADIO', 'CHECKBOX']:
                return True
            else:
                return False
        # Если obj еще не создан (при создании новой задачи), разрешаем добавление
        return True
    
    def get_queryset(self, request):
        """Отображаем варианты ответов только для подходящих типов вопросов."""
        qs = super().get_queryset(request)
        return qs

@admin.register(SurveyQuestionChoice)
class SurveyQuestionChoiceAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для вариантов ответов.
    """
    list_display = ('question', 'choice_text', 'order')
    list_filter = ('question__task', 'question')
    search_fields = ('choice_text', 'question__question_text')
    ordering = ('question', 'order')

@admin.register(Task)
class TaskAdmin(NestedModelAdmin):  # <-- Изменено на NestedModelAdmin
    """
    Админ-интерфейс для задач.
    """
    list_display = ('title', 'task_type', 'status', 'is_active', 'assigned_to', 'client', 'created_by', 'created_at')
    list_filter = ('task_type', 'status', 'is_active', 'assigned_to', 'client', 'created_by')
    search_fields = ('title', 'description')
    list_per_page = 20
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('title', 'description', 'task_type', 'status', 'is_active')
        }),
        (_('Назначение'), {
            'fields': ('assigned_to', 'client', 'created_by'),
            'classes': ('wide',)
        }),
        (_('План выполнения'), {
            'fields': ('target_count', 'current_count'),
            'classes': ('collapse',)
        }),
        (_('Дополнительно'), {
            'fields': ('moderator_comment',),
            'classes': ('collapse',)
        }),
    )
    
    def get_inlines(self, request, obj=None):
        """Return appropriate inlines based on task type."""
        if obj and obj.task_type == TaskType.SURVEY:
            return [SurveyQuestionInline]
        elif obj and obj.task_type in [TaskType.EQUIPMENT_PHOTO, TaskType.SIMPLE_PHOTO]:
            return []
        return []
    
    def get_queryset(self, request):
        """Optimize queryset by selecting related fields."""
        return super().get_queryset(request).select_related(
            'assigned_to', 'client', 'created_by'
        )
    
    class Meta:
        verbose_name = _('Задача')
        verbose_name_plural = _('Задачи')
        
class SurveyQuestionInline(NestedStackedInline):
    """Inline questions for survey tasks."""
    model = SurveyQuestion
    extra = 1  # Показывать 1 пустое поле для вопроса при создании
    inlines = [SurveyQuestionChoiceInline]
    verbose_name = _('Вопрос')
    verbose_name_plural = _('Вопросы')
    
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 80})},
    }
    
    def has_add_permission(self, request, obj=None):
        """
        Разрешаем добавление вопросов только если задача — это анкета.
        """
        if obj and obj.task_type == 'SURVEY':
            return True
        # Для новой задачи разрешаем добавление вопросов
        return True