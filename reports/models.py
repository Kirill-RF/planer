"""
Reporting and analytics models.

This module defines models for storing aggregated statistics and analytics data.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser, UserRoles  # Исправленный импорт
from clients.models import Client, ClientGroup
from tasks.models import Task, TaskType
from django.core.validators import FileExtensionValidator

class TaskStatistics(models.Model):
    """
    Aggregated task statistics model.
    
    Stores pre-calculated statistics for performance optimization.
    """
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='report_statistics_tasks')
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Клиент')
    )
    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': UserRoles.EMPLOYEE},  # Исправлено
        null=True,
        blank=True,
        verbose_name=_('Сотрудник')
    )
    moderator = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': UserRoles.MODERATOR},  # Исправлено
        related_name='moderator_stats',
        null=True,
        blank=True,
        verbose_name=_('Модератор')
    )
    client_group = models.ForeignKey(
        ClientGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Группа клиентов')
    )
    
    # Статистика для анкет
    total_responses = models.PositiveIntegerField(_('Всего ответов'), default=0)
    completed_tasks = models.PositiveIntegerField(_('Завершено задач'), default=0)
    pending_tasks = models.PositiveIntegerField(_('В процессе'), default=0)
    
    # JSON поле для хранения детальной статистики по вопросам
    survey_stats = models.JSONField(_('Статистика анкет'), null=True, blank=True)
    
    last_updated = models.DateTimeField(_('Последнее обновление'), auto_now=True)
    
    def __str__(self):
        return f"Статистика для {self.task.title}"
    
    class Meta:
        verbose_name = _('Статистика задачи')
        verbose_name_plural = _('Статистика задач')
        unique_together = ('task', 'client', 'employee')


class EquipmentReport(models.Model):
    """
    Модель отчета по оборудованию.
    
    Parameters
    ----------
    client : Client
        Клиент, для которого создан отчет
    employee : CustomUser
        Сотрудник, загрузивший фото
    date : datetime.date
        Дата отчета
    photos : ManyToManyField
        Связь с моделью фото
    created_at : datetime
        Время создания
    updated_at : datetime
        Время последнего обновления
    """
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Клиент')
    )
    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_('Сотрудник'),
        limit_choices_to={'role': UserRoles.EMPLOYEE}
    )
    date = models.DateField(
        _('Дата отчета')
    )
    photos = models.ManyToManyField(
        'Photo',
        blank=True,
        verbose_name=_('Фото')
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)
    
    def __str__(self):
        return f"Отчет по оборудованию для {self.client.name} ({self.date})"
    
    class Meta:
        verbose_name = _('Отчет по оборудованию')
        verbose_name_plural = _('Отчеты по оборудованию')
        ordering = ['-date']


class Photo(models.Model):
    """
    Модель фото для отчетов.
    
    Parameters
    ----------
    photo : ImageField
        Файл изображения
    description : str
        Описание фото
    created_at : datetime
        Время создания
    """
    
    photo = models.ImageField(
        _('Фото'),
        upload_to='equipment_reports/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    description = models.TextField(
        _('Описание'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    def __str__(self):
        return f"Фото от {self.created_at.date()}"
    
    class Meta:
        verbose_name = _('Фото')
        verbose_name_plural = _('Фото')
        ordering = ['-created_at']


class Evaluation(models.Model):
    """
    Модель оценки модератора.
    
    Parameters
    ----------
    report : EquipmentReport
        Отчет, который оценивается
    moderator : CustomUser
        Модератор, оставивший оценку
    fullness_comment : str
        Комментарий по критерию "Наполнение"
    no_foreign_goods_comment : str
        Комментарий по критерию "Отсутствие посторонних товаров"
    presentation_comment : str
        Комментарий по критерию "Оформление"
    improvement_task : Task
        Ссылка на задачу на доработку
    created_at : datetime
        Время создания
    updated_at : datetime
        Время последнего обновления
    """
    
    report = models.ForeignKey(
        EquipmentReport,
        on_delete=models.CASCADE,
        verbose_name=_('Отчет по оборудованию')
    )
    moderator = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Модератор'),
        limit_choices_to={'role': UserRoles.MODERATOR}
    )
    fullness_comment = models.TextField(
        _('Комментарий по наполнению'),
        blank=True
    )
    no_foreign_goods_comment = models.TextField(
        _('Комментарий по отсутствию посторонних товаров'),
        blank=True
    )
    presentation_comment = models.TextField(
        _('Комментарий по оформлению'),
        blank=True
    )
    improvement_task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Задача на доработку')
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)
    
    def __str__(self):
        return f"Оценка от {self.moderator.username if self.moderator else 'Unknown'} для {self.report}"
    
    class Meta:
        verbose_name = _('Оценка')
        verbose_name_plural = _('Оценки')
        ordering = ['-created_at']


class EquipmentPhotoReportQuestion(models.Model):
    """
    Модель вопроса для фотоотчета по оборудованию.
    
    Parameters
    ----------
    report : EquipmentReport
        Отчет, к которому относится вопрос
    question_text : str
        Текст вопроса
    order : int
        Порядок отображения
    question_type : str
        Тип вопроса
    created_at : datetime
        Время создания
    """
    
    QUESTION_TYPE_CHOICES = [
        ('TEXT', 'Текстовое поле'),
        ('TEXT_SHORT', 'Короткое текстовое поле (20 символов)'),
        ('RADIO', 'Радиокнопки (одиночный выбор)'),
        ('CHECKBOX', 'Чекбоксы (множественный выбор)'),
        ('SELECT_SINGLE', 'Выбор из списка (одиночный выбор)'),
        ('SELECT_MULTIPLE', 'Выбор из списка (множественный выбор)'),
        ('PHOTO', 'Фото'),
    ]
    
    report = models.ForeignKey(
        EquipmentReport,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Отчет по оборудованию')
    )
    question_text = models.CharField(_('Текст вопроса'), max_length=500)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    question_type = models.CharField(
        _('Тип вопроса'),
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='TEXT'
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    def __str__(self):
        return self.question_text[:50] + '...' if len(self.question_text) > 50 else self.question_text
    
    def has_custom_choices(self):
        """Проверяет наличие кастомных вариантов ответов."""
        return self.choices.exists()
    
    class Meta:
        verbose_name = _('Вопрос фотоотчета')
        verbose_name_plural = _('Вопросы фотоотчетов')
        ordering = ['order']


class EquipmentPhotoReportQuestionChoice(models.Model):
    """
    Модель варианта ответа для вопроса фотоотчета.
    
    Parameters
    ----------
    question : EquipmentPhotoReportQuestion
        Родительский вопрос
    choice_text : str
        Текст варианта ответа
    is_correct : bool
        Является ли правильным ответом
    order : int
        Порядок отображения
    """
    
    question = models.ForeignKey(
        EquipmentPhotoReportQuestion,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name=_('Вопрос')
    )
    choice_text = models.CharField(_('Текст варианта'), max_length=200)
    is_correct = models.BooleanField(_('Правильный ответ'), default=False)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    def __str__(self):
        return self.choice_text
    
    class Meta:
        verbose_name = _('Вариант ответа')
        verbose_name_plural = _('Варианты ответов')
        ordering = ['order']


class EquipmentPhotoReportAnswer(models.Model):
    """
    Модель ответа на вопрос фотоотчета.
    
    Parameters
    ----------
    question : EquipmentPhotoReportQuestion
        Вопрос, на который дается ответ
    user : CustomUser
        Пользователь, давший ответ
    selected_choices : ManyToManyField
        Выбранные варианты ответов (для вопросов с выбором)
    text_answer : str, optional
        Текстовый ответ
    client : Client
        Клиент, к которому относится ответ
    created_at : datetime
        Время создания
    """
    
    question = models.ForeignKey(
        EquipmentPhotoReportQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Вопрос')
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь')
    )
    selected_choices = models.ManyToManyField(
        EquipmentPhotoReportQuestionChoice,
        blank=True,
        verbose_name=_('Выбранные варианты')
    )
    text_answer = models.TextField(_('Текстовый ответ'), blank=True, null=True)
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Клиент')
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)

    def __str__(self):
        return f"Ответ от {self.user.username} на '{self.question.question_text[:30]}...'"

    class Meta:
        verbose_name = _('Ответ на вопрос фотоотчета')
        verbose_name_plural = _('Ответы на вопросы фотоотчетов')


class EquipmentPhotoReportAnswerPhoto(models.Model):
    """
    Модель фото для ответа на вопрос фотоотчета.
    
    Parameters
    ----------
    answer : EquipmentPhotoReportAnswer
        Ответ, к которому прикреплено фото
    photo : ImageField
        Файл изображения
    description : str, optional
        Описание фото
    created_at : datetime
        Время создания
    """
    
    answer = models.ForeignKey(
        EquipmentPhotoReportAnswer,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Ответ')
    )
    photo = models.ImageField(
        _('Фото'),
        upload_to='equipment_report_answer_photos/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    description = models.TextField(
        _('Описание'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    def __str__(self):
        return f"Фото для ответа {self.answer.id}"
    
    class Meta:
        verbose_name = _('Фото ответа на вопрос')
        verbose_name_plural = _('Фото ответов на вопросы')
        ordering = ['-created_at']
