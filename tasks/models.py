"""
Task management models for the employee management system.
This module defines task models, their types, and related entities.
Implements SOLID principles by separating different task types into
specialized models while maintaining a common base.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from users.models import CustomUser, UserRoles
from clients.models import Client

class TaskStatus(models.TextChoices):
    """Task status enumeration."""
    DRAFT = 'DRAFT', _('Черновик')
    SENT = 'SENT', _('Отправлено')
    REWORK = 'REWORK', _('На доработку')
    ON_CHECK = 'ON_CHECK', _('На проверке')  # Новый статус
    COMPLETED = 'COMPLETED', _('Завершена')

class TaskType(models.TextChoices):
    """Task type enumeration."""
    SURVEY = 'SURVEY', _('Анкета')
    EQUIPMENT_PHOTO = 'EQUIPMENT_PHOTO', _('Фотоотчет по оборудованию')
    SIMPLE_PHOTO = 'SIMPLE_PHOTO', _('Фотоотчет простой')

class Task(models.Model):
    """
    Base task model with common attributes.
    Attributes
    ----------
    title : str
        Task title
    description : str, optional
        Task description
    task_type : str
        Type of task (SURVEY, EQUIPMENT_PHOTO, SIMPLE_PHOTO)
    status : str
        Current task status
    is_active : bool
        Whether task is visible to employees
    assigned_to : CustomUser, optional
        Employee assigned to task
    client : Client, optional
        Client associated with task
    created_by : CustomUser
        User who created the task
    created_at : datetime
        Creation timestamp
    updated_at : datetime
        Last update timestamp
    moderator_comment : str, optional
        Comment from moderator for rework tasks
    target_count : int, optional
        Target number of responses (for surveys)
    current_count : int
        Current number of responses (for surveys)
    Methods
    -------
    can_be_viewed_by(user)
        Check if user can view this task
    can_be_edited_by(user)
        Check if user can edit this task
    get_completion_percentage()
        Get completion percentage for survey tasks
    """
    title = models.CharField(_('Название задачи'), max_length=200)
    description = models.TextField(_('Описание'), blank=True, null=True)
    task_type = models.CharField(
        _('Тип задачи'),
        max_length=20,
        choices=TaskType.choices
    )
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.DRAFT
    )
    is_active = models.BooleanField(_('Активная'), default=True)
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': UserRoles.EMPLOYEE},
        verbose_name=_('Назначено сотруднику')
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Клиент')
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        limit_choices_to={'role': UserRoles.MODERATOR},
        verbose_name=_('Создано модератором')
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)
    moderator_comment = models.TextField(
        _('Комментарий модератора'),
        blank=True,
        null=True
    )
    target_count = models.PositiveIntegerField(
        _('Целевое количество ответов'),
        default=0,
        help_text=_('Для анкет: сколько клиентов нужно опросить')
    )
    current_count = models.PositiveIntegerField(
        _('Текущее количество ответов'),
        default=0
    )
    
    def __str__(self):
        """Return string representation of task."""
        return f"{self.title} ({self.get_task_type_display()})"
    
    def can_be_viewed_by(self, user):
        """
        Check if user can view this task.
        Parameters
        ----------
        user : CustomUser
            User to check permissions for
        Returns
        -------
        bool
            True if user can view task, False otherwise
        """
        if user.role == UserRoles.MODERATOR:
            return True
        if user.role == UserRoles.EMPLOYEE:
            return (
                self.status in [TaskStatus.SENT, TaskStatus.REWORK, TaskStatus.ON_CHECK] and
                self.is_active and
                (self.assigned_to == user or self.assigned_to is None)
            )
        return False
    
    def can_be_edited_by(self, user):
        """
        Check if user can edit this task.
        Parameters
        ----------
        user : CustomUser
            User to check permissions for
        Returns
        -------
        bool
            True if user can edit task, False otherwise
        """
        return user.role == UserRoles.MODERATOR
    
    def get_completion_percentage(self):
        """Get completion percentage for survey tasks."""
        if self.task_type == TaskType.SURVEY and self.target_count > 0:
            return min(100, int((self.current_count / self.target_count) * 100))
        return 0
    
    class Meta:
        verbose_name = _('Задача')
        verbose_name_plural = _('Задачи')
        ordering = ['-created_at']

# tasks/models.py - обновленный SurveyQuestion

class SurveyQuestion(models.Model):
    """
    Модель вопроса для анкет.
    
    Позволяет создавать вопросы с разными типами ответов,
    включая кастомные варианты.
    """
    
    QUESTION_TYPE_CHOICES = [
        ('TEXT', 'Текстовое поле'),
        ('RADIO', 'Радиокнопки (одиночный выбор)'),
        ('CHECKBOX', 'Чекбоксы (множественный выбор)'),
        ('TEXTAREA', 'Текстовая область'),
        ('PHOTO', 'Фото'),
    ]
    
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        limit_choices_to={'task_type': TaskType.SURVEY},
        related_name='questions',
        verbose_name=_('Задача')
    )
    question_text = models.CharField(_('Текст вопроса'), max_length=500)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    question_type = models.CharField(
        _('Тип вопроса'),
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='TEXT'
    )
    # Удаляем get_default_choices - будем использовать связанные варианты
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    def __str__(self):
        return self.question_text[:50] + '...' if len(self.question_text) > 50 else self.question_text
    
    def has_custom_choices(self):
        """Проверяет, есть ли кастомные варианты ответов."""
        return self.choices.exists()
    
    class Meta:
        verbose_name = _('Вопрос анкеты')
        verbose_name_plural = _('Вопросы анкет')
        ordering = ['order']

# tasks/models.py - проверьте эту часть

class SurveyQuestionChoice(models.Model):
    """
    Вариант ответа для вопроса анкеты.
    """
    question = models.ForeignKey(
        SurveyQuestion,
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
    


class PhotoReport(models.Model):
    """
    Photo report model for both equipment and simple photo reports.
    Attributes
    ----------
    task : Task
        Parent task (must be EQUIPMENT_PHOTO or SIMPLE_PHOTO type)
    client : Client
        Client for the report
    address : str
        Address of equipment/location
    stand_count : int
        Number of stands (0 for simple photo reports)
    comment : str, optional
        Additional comment
    created_by : CustomUser
        User who created the report
    created_at : datetime
        Creation timestamp
    Methods
    -------
    __str__()
        String representation of report
    is_equipment_report()
        Check if this is an equipment photo report
    """
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        limit_choices_to={
            'task_type__in': [TaskType.EQUIPMENT_PHOTO, TaskType.SIMPLE_PHOTO]
        },
        related_name='photo_reports',
        verbose_name=_('Задача')
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Клиент')
    )
    address = models.CharField(_('Адрес'), max_length=300)
    stand_count = models.PositiveIntegerField(_('Количество стендов'), default=0)
    comment = models.TextField(_('Комментарий'), blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_('Создано')
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    def __str__(self):
        """Return string representation of report."""
        report_type = "оборудованию" if self.is_equipment_report() else "простой"
        return f"Фотоотчет ({report_type}) для {self.client.name}"
    
    def is_equipment_report(self):
        """Check if this is an equipment photo report."""
        return self.task.task_type == TaskType.EQUIPMENT_PHOTO
    
    def is_simple_report(self):
        """Check if this is a simple photo report."""
        return self.task.task_type == TaskType.SIMPLE_PHOTO
    
    class Meta:
        verbose_name = _('Фотоотчет')
        verbose_name_plural = _('Фотоотчеты')

class PhotoReportItem(models.Model):
    """
    Photo item for photo reports.
    Attributes
    ----------
    report : PhotoReport
        Parent report
    photo : ImageField
        Photo file
    description : str, optional
        Photo description
    quality_score : float, optional
        Photo quality score (0.0 to 1.0)
    is_accepted : bool
        Whether photo is accepted
    created_at : datetime
        Creation timestamp
    Methods
    -------
    __str__()
        String representation of photo item
    """
    report = models.ForeignKey(
        PhotoReport,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Отчет')
    )
    photo = models.ImageField(
        _('Фото'),
        upload_to='photo_reports/%Y/%m/%d/'
    )
    description = models.CharField(
        _('Описание'),
        max_length=200,
        blank=True,
        null=True
    )
    quality_score = models.FloatField(
        _('Качество фото'),
        blank=True,
        null=True,
        help_text=_('Оценка качества от 0.0 до 1.0')
    )
    is_accepted = models.BooleanField(
        _('Принято'),
        default=False
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    def __str__(self):
        """Return string representation of photo item."""
        return f"Фото для {self.report.client.name} ({self.created_at.date()})"
    
    class Meta:
        verbose_name = _('Фото для отчета')
        verbose_name_plural = _('Фото для отчетов')

class SurveyAnswer(models.Model):
    """
    Survey answer model storing user responses.
    Attributes
    ----------
    question : SurveyQuestion
        Question being answered
    user : CustomUser
        User providing the answer
    selected_choices : ManyToManyField
        Selected choices (for multiple choice)
    text_answer : str, optional
        Text answer (for open questions)
    photo : ImageField, optional
        Photo answer
    client : Client
        Client for this response
    created_at : datetime
        Creation timestamp
    Methods
    -------
    __str__()
        String representation of answer
    """
    question = models.ForeignKey(
        SurveyQuestion,
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
        SurveyQuestionChoice,
        blank=True,
        verbose_name=_('Выбранные варианты')
    )
    text_answer = models.TextField(_('Текстовый ответ'), blank=True, null=True)
    photo = models.ImageField(
        _('Фото'),
        upload_to='survey_photos/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Клиент')
    )
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    def __str__(self):
        """Return string representation of answer."""
        return f"Ответ от {self.user.username} на '{self.question.question_text[:30]}...'"
    
    class Meta:
        verbose_name = _('Ответ на вопрос')
        verbose_name_plural = _('Ответы на вопросы')

class SurveyClientAssignment(models.Model):
    """
    Link between survey tasks and clients.
    Tracks which clients have been assigned to which survey tasks.
    """
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        limit_choices_to={'task_type': TaskType.SURVEY},
        verbose_name=_('Задача')
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Клиент')
    )
    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': UserRoles.EMPLOYEE},
        verbose_name=_('Сотрудник')
    )
    completed = models.BooleanField(_('Завершено'), default=False)
    completed_at = models.DateTimeField(_('Завершено'), null=True, blank=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    def __str__(self):
        return f"{self.task.title} - {self.client.name}"
    
    class Meta:
        verbose_name = _('Назначение клиента к анкете')
        verbose_name_plural = _('Назначения клиентов к анкетам')
        unique_together = ('task', 'client', 'employee')