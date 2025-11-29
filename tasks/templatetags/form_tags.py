# -*- coding: utf-8 -*-
"""
Created on Sat Nov 29 15:41:04 2025

@author: Professional
"""

# tasks/templatetags/form_tags.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получает элемент из словаря по ключу."""
    return dictionary.get(f'question_{key}')