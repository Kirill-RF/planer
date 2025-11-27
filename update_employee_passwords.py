#!/usr/bin/env python
"""
Скрипт для обновления паролей у существующих пользователей сотрудников до 4-символьных.
"""
import os
import sys
import django

# Добавляем путь к проекту Django
sys.path.append('/workspace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'polling_system.settings')

django.setup()

from django.contrib.auth.models import User
from surveys.models import Employee

def update_employee_passwords():
    # Получаем всех сотрудников, которые уже связаны с пользователями
    employees = Employee.objects.all()
    
    for employee in employees:
        if employee.user:
            # Обновляем пароль сотрудника на 4-символьный
            employee.user.set_password('pwd1')  # 4-символьный пароль
            employee.user.save()
            print(f"Обновлён пароль для пользователя {employee.user.username} (сотрудник {employee.full_name})")
        else:
            print(f"Сотрудник {employee.full_name} не связан с пользователем")

if __name__ == '__main__':
    update_employee_passwords()
    print("Скрипт завершён.")