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
