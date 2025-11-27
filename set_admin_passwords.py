#!/usr/bin/env python
"""
Скрипт для установки паролей администраторам, если они существуют.
"""
import os
import sys
import django

# Добавляем путь к проекту Django
sys.path.append('/workspace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'polling_system.settings')

django.setup()

from django.contrib.auth.models import User

def set_admin_passwords():
    # Устанавливаем пароли для администраторов
    admin_users = ['Kirill', 'admin']
    
    for username in admin_users:
        try:
            user = User.objects.get(username=username)
            user.set_password('admin_password')  # В реальном приложении используйте более безопасный пароль
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print(f"Пароль установлен для администратора {username}")
        except User.DoesNotExist:
            print(f"Пользователь {username} не найден")

if __name__ == '__main__':
    set_admin_passwords()
    print("Скрипт завершён.")