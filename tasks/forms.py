# tasks/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _  # Добавьте этот импорт!
from .models import SurveyAnswer, SurveyQuestion, Client, SurveyQuestionChoice
from users.models import CustomUser

class SurveyResponseForm(forms.Form):
    """
    Форма для заполнения анкеты с динамическими полями.
    
    Автоматически создает поля на основе вопросов в задаче,
    включая выбор клиента и обработку разных типов ответов.
    """
    
    def __init__(self, task, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task = task
        self.user = user
        
        # Добавляем поле выбора клиента
        if not task.client:  # Если в задаче не указан клиент
            self.fields['selected_client'] = forms.ModelChoiceField(
                queryset=Client.objects.all(),
                label=_('Выберите клиента'),
                empty_label=_('Выберите клиента...'),
                required=True
            )
        
        # Создаем поля для каждого вопроса
        for question in task.questions.all().order_by('order'):
            field_name = f'question_{question.id}'
            
            if question.question_type == 'RADIO':
                if question.choices.exists():  # Есть кастомные варианты
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    self.fields[field_name] = forms.ChoiceField(
                        label=question.question_text,
                        choices=choices,
                        widget=forms.RadioSelect(),
                        required=True
                    )
                else:
                    # Стандартные варианты
                    self.fields[field_name] = forms.ChoiceField(
                        label=question.question_text,
                        choices=[('да', 'Да'), ('нет', 'Нет')],
                        widget=forms.RadioSelect(),
                        required=True
                    )
                    
            elif question.question_type == 'CHECKBOX':
                if question.choices.exists():  # Есть кастомные варианты
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    self.fields[field_name] = forms.MultipleChoiceField(
                        label=question.question_text,
                        choices=choices,
                        widget=forms.CheckboxSelectMultiple(),
                        required=False
                    )
                else:
                    self.fields[field_name] = forms.MultipleChoiceField(
                        label=question.question_text,
                        choices=[('да', 'Да'), ('нет', 'Нет')],
                        widget=forms.CheckboxSelectMultiple(),
                        required=False
                    )
                    
            elif question.question_type == 'TEXT':
                self.fields[field_name] = forms.CharField(
                    label=question.question_text,
                    widget=forms.TextInput(),
                    required=False
                )
                
            elif question.question_type == 'TEXTAREA':
                self.fields[field_name] = forms.CharField(
                    label=question.question_text,
                    widget=forms.Textarea(attrs={'rows': 3}),
                    required=False
                )
                
            elif question.question_type == 'PHOTO':
                self.fields[field_name] = forms.ImageField(
                    label=question.question_text,
                    required=False
                )

    def save(self):
        """Сохраняет ответы на анкету в базу данных."""
        # Определяем клиента
        if self.task.client:
            client = self.task.client
        else:
            client = self.cleaned_data['selected_client']
        
        for question in self.task.questions.all():
            field_name = f'question_{question.id}'
            
            if field_name in self.cleaned_data:
                answer_data = self.cleaned_data[field_name]
                
                survey_answer = SurveyAnswer.objects.create(
                    question=question,
                    user=self.user,
                    client=client
                )
                
                # Обработка разных типов вопросов
                if question.question_type == 'RADIO':
                    if question.choices.exists():
                        if answer_data:
                            choice = question.choices.get(id=int(answer_data))
                            survey_answer.selected_choices.add(choice)
                    else:
                        survey_answer.text_answer = answer_data
                        
                elif question.question_type == 'CHECKBOX':
                    if question.choices.exists():
                        if answer_data:
                            choices = question.choices.filter(id__in=[int(id) for id in answer_data])
                            survey_answer.selected_choices.set(choices)
                    else:
                        if isinstance(answer_data, list):
                            survey_answer.text_answer = ', '.join(answer_data)
                        else:
                            survey_answer.text_answer = answer_data or ''
                            
                elif question.question_type == 'TEXT':
                    survey_answer.text_answer = answer_data or ''
                    
                elif question.question_type == 'TEXTAREA':
                    survey_answer.text_answer = answer_data or ''
                    
                elif question.question_type == 'PHOTO':
                    survey_answer.photo = answer_data
                
                survey_answer.save()