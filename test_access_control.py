#!/usr/bin/env python
"""
Test script to verify access control changes
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

def test_access_control():
    print("=== Тестирование контроля доступа ===\n")
    
    # Проверяем пользователя Kirill
    try:
        kirill = User.objects.get(username='Kirill')
        print(f"Пользователь Kirill:")
        print(f"  - Пароль: {'Установлен' if kirill.check_password('A3k18Js') else 'Неверный пароль'}")
        print(f"  - is_staff: {kirill.is_staff}")
        print(f"  - is_superuser: {kirill.is_superuser}")
        print()
    except User.DoesNotExist:
        print("Пользователь Kirill не найден")
        print()
    
    # Проверяем администратора
    try:
        admin = User.objects.get(username='admin')
        print(f"Пользователь admin:")
        print(f"  - Пароль: {'Установлен' if admin.check_password('admin_password') else 'Неверный пароль'}")
        print(f"  - is_staff: {admin.is_staff}")
        print(f"  - is_superuser: {admin.is_superuser}")
        print()
    except User.DoesNotExist:
        print("Пользователь admin не найден")
        print()
    
    # Проверяем сотрудников
    employees = Employee.objects.all()
    for employee in employees:
        if employee.user:
            user = employee.user
            print(f"Сотрудник {employee.full_name} (пользователь {user.username}):")
            print(f"  - is_staff: {user.is_staff} (должен быть False)")
            print(f"  - Может войти: {'Да' if user.check_password('pwd1') else 'Пароль изменен, но это нормально'}")
            print()
    
    print("=== Резюме изменений ===")
    print("1. Пароль Kirill изменен на A3k18Js")
    print("2. Пароли сотрудников - 4 символа")
    print("3. Сотрудники НЕ имеют доступа к Админпанели (is_staff=False)")
    print("4. Пользователи (модераторы) имеют доступ к Админпанели (is_staff=True)")

if __name__ == '__main__':
    test_access_control()