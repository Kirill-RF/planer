# tasks/templatetags/form_tags.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Получает элемент из словаря по ключу.
    Используется в шаблонах для доступа к полям формы по ключу вопроса.
    """
    return dictionary.get(f'question_{key}')