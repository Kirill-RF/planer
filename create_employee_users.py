#!/usr/bin/env python
"""
Скрипт для создания пользователей для сотрудников, если они еще не связаны с пользователями.
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

def create_employee_users():
    # Получаем всех сотрудников
    employees = Employee.objects.all()
    
    for employee in employees:
        # Проверяем, связан ли сотрудник с пользователем
        if not employee.user:
            # Создаем имя пользователя на основе ФИО сотрудника
            # Убираем пробелы и делаем имя уникальным
            username = employee.full_name.replace(' ', '_')
            
            # Проверяем, существует ли уже пользователь с таким именем
            if User.objects.filter(username=username).exists():
                print(f"Пользователь с именем {username} уже существует для сотрудника {employee.full_name}")
                continue
            
            # Создаем нового пользователя
            user = User.objects.create_user(
                username=username,
                password='pwd1',  # 4-символьный пароль для сотрудников
                is_staff=False  # Сотрудники не являются администраторами по умолчанию
            )
            
            # Связываем пользователя с сотрудником
            employee.user = user
            employee.save()
            
            print(f"Создан пользователь {username} для сотрудника {employee.full_name}")
        else:
            print(f"Сотрудник {employee.full_name} уже связан с пользователем {employee.user.username}")

if __name__ == '__main__':
    create_employee_users()
    print("Скрипт завершён.")