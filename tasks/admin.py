# tasks/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.forms import TextInput, Textarea
from django.db import models
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404
from django.utils.html import format_html
from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline
from .models import (
    Task, TaskStatus, TaskType, SurveyQuestion, 
    SurveyQuestionChoice, SurveyAnswer, PhotoReport, PhotoReportItem,
    SurveyAnswerPhoto
)

class SurveyQuestionChoiceInline(NestedTabularInline):
    """Inline choices for survey questions."""
    model = SurveyQuestionChoice
    extra = 3
    verbose_name = _('Вариант ответа')
    verbose_name_plural = _('Варианты ответов')

class SurveyQuestionInline(NestedStackedInline):
    """Inline questions for survey tasks."""
    model = SurveyQuestion
    extra = 1
    inlines = [SurveyQuestionChoiceInline]
    verbose_name = _('Вопрос')
    verbose_name_plural = _('Вопросы')
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 80})},
    }

@admin.register(SurveyQuestionChoice)
class SurveyQuestionChoiceAdmin(admin.ModelAdmin):
    list_display = ('question', 'choice_text', 'order')
    list_filter = ('question__task', 'question')
    search_fields = ('choice_text', 'question__question_text')
    ordering = ('question', 'order')

@admin.register(Task)
class TaskAdmin(NestedModelAdmin):
    list_display = ('title', 'task_type', 'status', 'is_active', 
                   'assigned_to', 'client', 'created_by', 'created_at',
                   'get_completion_info')
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
        if obj and obj.task_type == TaskType.SURVEY:
            return [SurveyQuestionInline]
        elif obj and obj.task_type in [TaskType.EQUIPMENT_PHOTO, TaskType.SIMPLE_PHOTO]:
            return []
        return []
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'assigned_to', 'client', 'created_by'
        )
    
    def get_completion_info(self, obj):
        if obj.task_type == TaskType.SURVEY:
            percentage = obj.get_completion_percentage()
            return format_html(
                '{} / {} ({}%)<br><a href="{}" class="btn btn-sm btn-info">📊 Статистика</a>',
                obj.current_count,
                obj.target_count,
                percentage,
                reverse('admin:survey_statistics', args=[obj.id])
            )
        return '-'
    get_completion_info.short_description = _('Выполнение')
    get_completion_info.allow_tags = True
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('survey-stats/<int:task_id>/', 
                 self.admin_site.admin_view(self.survey_statistics_view), 
                 name='survey_statistics'),
        ]
        return custom_urls + urls
    
    def survey_statistics_view(self, request, task_id):
        """View for detailed survey statistics."""
        task = get_object_or_404(Task, id=task_id)
        
        # Общая статистика
        total_responses = SurveyAnswer.objects.filter(question__task=task).count()
        unique_clients = SurveyAnswer.objects.filter(question__task=task).values('client').distinct().count()
        
        # Статистика по вопросам
        questions_stats = []
        for question in task.questions.all():
            question_stats = {
                'question': question,
                'total_answers': SurveyAnswer.objects.filter(question=question).count()
            }
            
            # Обработка всех типов вопросов с выбором
            if question.question_type in ['RADIO', 'CHECKBOX', 'SELECT_SINGLE', 'SELECT_MULTIPLE']:
                choice_stats = []
                
                # 1. Обработка кастомных вариантов ответов (если есть)
                if question.has_custom_choices():
                    for choice in question.choices.all():
                        # Подсчет ответов для разных типов вопросов
                        if question.question_type == 'RADIO':
                            # Для радиокнопок - через selected_choices
                            count = SurveyAnswer.objects.filter(
                                question=question,
                                selected_choices=choice
                            ).count()
                        elif question.question_type == 'CHECKBOX':
                            # Для чекбоксов - через selected_choices
                            count = SurveyAnswer.objects.filter(
                                question=question,
                                selected_choices=choice
                            ).count()
                        elif question.question_type == 'SELECT_SINGLE':
                            # Для одиночного выбора - через text_answer (ID варианта)
                            count = SurveyAnswer.objects.filter(
                                question=question,
                                text_answer=str(choice.id)
                            ).count()
                        elif question.question_type == 'SELECT_MULTIPLE':
                            # Для множественного выбора - через text_answer (ID вариантов через запятую)
                            count = SurveyAnswer.objects.filter(
                                question=question,
                                text_answer__contains=str(choice.id)
                            ).count()
                        
                        percentage = (count / question_stats['total_answers'] * 100) if question_stats['total_answers'] > 0 else 0
                        # Округление до 0.5%
                        percentage = round(percentage * 2) / 2.0
                        choice_stats.append({
                            'choice': choice,
                            'count': count,
                            'percentage': percentage
                        })
                
                # 2. Обработка стандартных вариантов (если нет кастомных)
                else:
                    # Для вопросов с типом RADIO - стандартные варианты "Да" и "Нет"
                    if question.question_type == 'RADIO':
                        # Стандартные варианты "Да" и "Нет"
                        yes_count = SurveyAnswer.objects.filter(
                            question=question,
                            text_answer__iexact='да'
                        ).count()
                        no_count = SurveyAnswer.objects.filter(
                            question=question,
                            text_answer__iexact='нет'
                        ).count()
                        
                        yes_percentage = (yes_count / question_stats['total_answers'] * 100) if question_stats['total_answers'] > 0 else 0
                        no_percentage = (no_count / question_stats['total_answers'] * 100) if question_stats['total_answers'] > 0 else 0
                        # Округление до 0.5%
                        yes_percentage = round(yes_percentage * 2) / 2.0
                        no_percentage = round(no_percentage * 2) / 2.0
                        
                        choice_stats.extend([
                            {
                                'choice': type('Choice', (), {'choice_text': 'Да'}),
                                'count': yes_count,
                                'percentage': yes_percentage
                            },
                            {
                                'choice': type('Choice', (), {'choice_text': 'Нет'}),
                                'count': no_count,
                                'percentage': no_percentage
                            }
                        ])
                    
                    # Для вопросов с типом CHECKBOX - стандартные варианты "Да" и "Нет"
                    elif question.question_type == 'CHECKBOX':
                        # Стандартные варианты "Да" и "Нет"
                        yes_count = SurveyAnswer.objects.filter(
                            question=question,
                            text_answer__icontains='да'
                        ).count()
                        no_count = SurveyAnswer.objects.filter(
                            question=question,
                            text_answer__icontains='нет'
                        ).count()
                        
                        yes_percentage = (yes_count / question_stats['total_answers'] * 100) if question_stats['total_answers'] > 0 else 0
                        no_percentage = (no_count / question_stats['total_answers'] * 100) if question_stats['total_answers'] > 0 else 0
                        # Округление до 0.5%
                        yes_percentage = round(yes_percentage * 2) / 2.0
                        no_percentage = round(no_percentage * 2) / 2.0
                        
                        choice_stats.extend([
                            {
                                'choice': type('Choice', (), {'choice_text': 'Да'}),
                                'count': yes_count,
                                'percentage': yes_percentage
                            },
                            {
                                'choice': type('Choice', (), {'choice_text': 'Нет'}),
                                'count': no_count,
                                'percentage': no_percentage
                            }
                        ])
                
                question_stats['choice_stats'] = choice_stats
                
            # Текстовые вопросы
            elif question.question_type in ['TEXT', 'TEXT_SHORT', 'TEXTAREA']:
                text_answers = SurveyAnswer.objects.filter(
                    question=question
                ).exclude(text_answer__isnull=True).exclude(text_answer='')
                question_stats['text_answers_count'] = text_answers.count()
                
            # Фото вопросы
            elif question.question_type == 'PHOTO':
                # Получаем все ответы с фото для этого вопроса
                answers_with_photos = SurveyAnswer.objects.filter(
                    question=question
                ).prefetch_related('photos', 'client').order_by('client__name', 'created_at')
                
                # Группируем фото по ответам (клиентам)
                photo_groups = []
                for answer in answers_with_photos:
                    photos_data = []
                    for photo in answer.photos.all():
                        # Попытка извлечь EXIF данные
                        exif_data = self._extract_photo_exif(photo.photo.path) if photo.photo else None
                        address = self._format_address_from_exif(exif_data) if exif_data else None
                        
                        photos_data.append({
                            'photo': photo,
                            'client': answer.client,
                            'created_at': answer.created_at,
                            'exif_data': exif_data,
                            'address': address
                        })
                    
                    if photos_data:
                        photo_groups.append({
                            'answer': answer,
                            'photos_data': photos_data
                        })
                
                question_stats['photo_groups'] = photo_groups
                question_stats['total_photos'] = sum(len(group['photos_data']) for group in photo_groups)
            
            questions_stats.append(question_stats)
        
        context = {
            'title': f'Статистика: {task.title}',
            'task': task,
            'total_responses': total_responses,
            'unique_clients': unique_clients,
            'questions_stats': questions_stats,
            'opts': self.model._meta,
        }
        return render(request, 'admin/tasks/survey_statistics.html', context)

    def _extract_photo_exif(self, photo_path):
        """Извлекает EXIF данные из фото."""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            img = Image.open(photo_path)
            exifdata = img.getexif()
            if exifdata:
                exif = {}
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exifdata.get(tag_id)
                    if isinstance(data, bytes):
                        data = data.decode()
                    exif[tag] = data
                return exif
        except Exception as e:
            print(f"Error extracting EXIF: {e}")
        return None

    def _format_address_from_exif(self, exif_data):
        """Форматирует адрес из EXIF данных."""
        if not exif_data:
            return None
        
        try:
            # Извлечение координат из GPS данных
            gps_info = exif_data.get('GPSInfo')
            if gps_info:
                # Извлечение GPS-координат
                gps_keys = list(gps_info.keys())
                gps_values = list(gps_info.values())
                
                # Извлечение широты и долготы
                lat = self._convert_to_degrees(gps_info.get(2), gps_info.get(1))  # GPSLatitude, GPSLatitudeRef
                lon = self._convert_to_degrees(gps_info.get(4), gps_info.get(3))  # GPSLongitude, GPSLongitudeRef
                
                if lat and lon:
                    return f"{lat}, {lon}"
        except Exception as e:
            print(f"Error formatting address from EXIF: {e}")
        
        return None

    def _convert_to_degrees(self, value, ref):
        """Конвертирует GPS-координаты в градусы."""
        if not value:
            return None
        
        try:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            
            degrees = d + (m / 60.0) + (s / 3600.0)
            
            if ref in ['S', 'W']:
                degrees = -degrees
                
            return degrees
        except (IndexError, ValueError, TypeError):
            return None

# Остальные регистрации моделей...
@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'client', 'get_selected_choices', 'text_answer_preview', 'has_photos', 'created_at')
    readonly_fields = ('user', 'question', 'selected_choices', 'text_answer', 'client', 'created_at')
    list_per_page = 20
    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_selected_choices(self, obj):
        if obj.selected_choices.exists():
            return ', '.join([choice.choice_text for choice in obj.selected_choices.all()])
        return '-'
    get_selected_choices.short_description = _('Выбранные варианты')
    
    def text_answer_preview(self, obj):
        if obj.text_answer:
            return obj.text_answer[:50] + '...' if len(obj.text_answer) > 50 else obj.text_answer
        return '-'
    text_answer_preview.short_description = _('Текстовый ответ')
    
    def has_photos(self, obj):
        return obj.photos.exists()
    has_photos.short_description = _('Есть фото')
    has_photos.boolean = True

@admin.register(SurveyAnswerPhoto)
class SurveyAnswerPhotoAdmin(admin.ModelAdmin):
    list_display = ('answer', 'photo_thumbnail', 'created_at')
    readonly_fields = ('answer', 'photo', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.photo.url)
        return '-'
    photo_thumbnail.short_description = _('Миниатюра')

@admin.register(PhotoReport)
class PhotoReportAdmin(admin.ModelAdmin):
    list_display = ('task', 'client', 'address', 'stand_count', 'created_by', 'created_at')
    readonly_fields = ('task', 'client', 'address', 'stand_count', 'comment', 'created_by')
    list_per_page = 20

@admin.register(PhotoReportItem)
class PhotoReportItemAdmin(admin.ModelAdmin):
    list_display = ('report', 'photo_thumbnail', 'quality_score', 'is_accepted', 'created_at')
    readonly_fields = ('report', 'photo', 'description', 'quality_score', 'is_accepted', 'created_at')
    list_per_page = 20
    
    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.photo.url)
        return '-'
    photo_thumbnail.short_description = _('Миниатюра')