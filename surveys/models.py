# surveys/models.py
from django.db import models

QUESTION_TYPES = (
    ('text', 'Текст'),
    ('single_select', 'Список (один выбор)'),
    ('multi_select', 'Список (множественный выбор)'),
    ('checkbox', 'Чекбоксы (множественный)'),
    ('radio', 'Радиокнопки (один)'),
    ('photo', 'Фото'),
)

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

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"


class Client(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="ФИО клиента / Название компании")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    holding = models.ForeignKey(Holding, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Холдинг")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сотрудник")

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