# surveys/models.py
import re
from django.db import models

# === Типы вопросов ===
QUESTION_TYPES = (
    ('text', 'Текст'),
    ('single_select', 'Список (один выбор)'),
    ('multi_select', 'Список (множественный выбор)'),
    ('checkbox', 'Чекбоксы (множественный)'),
    ('radio', 'Радиокнопки (один)'),
    ('photo', 'Фото'),
)

# === Статусы фотоотчёта ===
PHOTO_REPORT_STATUS = (
    ('draft', 'Черновик'),
    ('submitted', 'Отправлен'),
    ('rejected', 'На доработку'),
    ('approved', 'Принят'),
)

# === Модели ===
class Survey(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название анкеты")
    target_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="План (мин. кол-во заполнений)",
        help_text="Оставьте пустым для '--' (любое количество)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Анкета"
        verbose_name_plural = "Анкеты"


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500, verbose_name="Текст вопроса")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, verbose_name="Тип вопроса")
    required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.text} ({self.question_type})"

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"


class Holding(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название холдинга")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Холдинг"
        verbose_name_plural = "Холдинги"


class Employee(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="ФИО сотрудника")
    position = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=4, verbose_name="Пароль (до 4 символов)", blank=True, help_text="Пароль для аутентификации сотрудника (до 4 символов)")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"


class Client(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="ФИО клиента / Название компании")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    holding = models.ForeignKey(Holding, on_delete=models.SET_NULL, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class ClientAssignment(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client} → {self.employee}"

    class Meta:
        verbose_name = "Назначение клиента"
        verbose_name_plural = "Назначения клиентов"


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    text_answer = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='responses/photos/', blank=True, null=True)
    selected_options = models.ManyToManyField(Option, blank=True)

    def __str__(self):
        return f"Ответ от {self.employee} по анкете {self.survey}"

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"


# === НОВЫЕ МОДЕЛИ ФОТООТЧЁТА (только один раз!) ===

class PhotoReport(models.Model):
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    created_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_reports', verbose_name="Создано"
    )
    assigned_to = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports',
        verbose_name="Назначен сотруднику"
    )
    assignment_comment = models.TextField(
        blank=True,
        verbose_name="Комментарий при назначении"
    )
    stand_count = models.PositiveIntegerField(verbose_name="Количество стендов")
    address = models.CharField(max_length=500, blank=True, verbose_name="Адрес")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=PHOTO_REPORT_STATUS, default='draft')
    moderator = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    rejected_reason = models.TextField(blank=True, verbose_name="Комментарий при возврате")

    def __str__(self):
        return f"Фотоотчёт: {self.client} — {self.get_status_display()}"

    class Meta:
        verbose_name = "Фотоотчёт"
        verbose_name_plural = "Фотоотчёты"


class Photo(models.Model):
    report = models.ForeignKey(PhotoReport, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='photo_reports/')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    detected_address = models.CharField(max_length=500, blank=True)
    is_high_quality = models.BooleanField(default=False)

    def __str__(self):
        return f"Фото {self.id} — {self.report.client}"

    class Meta:
        verbose_name = "Фото"
        verbose_name_plural = "Фотографии"


class ModeratorComment(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    moderator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий модератора"
        verbose_name_plural = "Комментарии модератора"


# === Утилиты нормализации ===

def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    name = re.sub(r'\s+', ' ', name.strip())
    for abbr in ['ООО', 'ИП', 'ЗАО', 'ОАО', 'АО', 'ПАО', 'НКО']:
        name = re.sub(rf'\b{abbr.lower()}\b', abbr, name, flags=re.IGNORECASE)
    return name


def normalize_phone(phone):
    if not phone:
        return None
    cleaned = re.sub(r'[^\d+]', '', str(phone))
    if cleaned.startswith('8'):
        cleaned = '+7' + cleaned[1:]
    elif cleaned.startswith('7') and not cleaned.startswith('+7'):
        cleaned = '+' + cleaned
    elif not cleaned.startswith('+7'):
        return None
    if len(cleaned) == 12:
        return cleaned
    return None